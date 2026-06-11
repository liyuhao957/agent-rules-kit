#!/usr/bin/env python3
"""Tests for suggest-rule-updates.py: idempotency and gate semantics."""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from lib import REPO_ROOT

INSTALL = REPO_ROOT / "scripts" / "install-rules.sh"


def sh(args, cwd=None):
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True)


def install_project(root: Path) -> Path:
    proj = root / "proj"
    (proj / "src" / "components").mkdir(parents=True)
    (proj / "src" / "components" / "Button.js").write_text("export const B = 1\n")
    (proj / "package.json").write_text('{"name":"p"}\n')
    sh(["git", "init", "-q"], cwd=proj)
    sh(["git", "config", "user.email", "t@t"], cwd=proj)
    sh(["git", "config", "user.name", "t"], cwd=proj)
    sh(["git", "add", "-A"], cwd=proj)
    sh(["git", "commit", "-qm", "init"], cwd=proj)
    sh(["bash", str(INSTALL), "--target", str(proj), "--bootstrap"])
    sh(["git", "add", "-A"], cwd=proj)
    sh(["git", "commit", "-qm", "install"], cwd=proj)
    return proj


def main() -> int:
    work = Path(tempfile.mkdtemp())
    passed = 0
    failed = 0
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        nonlocal passed, failed
        if ok:
            passed += 1
        else:
            failed += 1
            fails.append(f"{name}: {detail}".rstrip(": "))

    try:
        proj = install_project(work)
        cand = proj / ".agent" / "rule-candidates.md"

        # Make a drift-only change (UI component, no risk path).
        (proj / "src" / "components" / "Card.js").write_text("export const C = 1\n")

        # Idempotency: two consecutive scans must yield byte-identical output.
        sh([sys.executable, "scripts/suggest-rule-updates.py", "--quiet"], cwd=proj)
        first = cand.read_text(encoding="utf-8")
        sh([sys.executable, "scripts/suggest-rule-updates.py", "--quiet"], cwd=proj)
        second = cand.read_text(encoding="utf-8")
        check("idempotent rewrite (no spurious diff)", first == second,
              "second scan changed the file")

        # Gate semantics: drift-only pending must NOT fail --check --gate,
        # but MUST fail plain --check (strict, for adaptation).
        gate = sh([sys.executable, "scripts/suggest-rule-updates.py", "--quiet", "--check", "--gate"], cwd=proj)
        strict = sh([sys.executable, "scripts/suggest-rule-updates.py", "--quiet", "--check"], cwd=proj)
        check("drift-only passes --check --gate", gate.returncode == 0, f"exit {gate.returncode}")
        check("drift-only fails plain --check", strict.returncode == 1, f"exit {strict.returncode}")

        # A risk path makes --check --gate fail.
        (proj / "config").mkdir(exist_ok=True)
        (proj / "config" / "billing.ts").write_text("export const X = 1\n")
        gate2 = sh([sys.executable, "scripts/suggest-rule-updates.py", "--quiet", "--check", "--gate"], cwd=proj)
        check("risk path fails --check --gate", gate2.returncode == 1, f"exit {gate2.returncode}")

        # No-explosion: editing N files in ONE domain incrementally (scanning
        # between edits, as the Stop hook does) must yield ONE drift candidate
        # for that rule, not N.
        proj2 = work / "proj2"
        (proj2 / "src" / "components").mkdir(parents=True)
        (proj2 / "package.json").write_text('{"name":"q"}\n')
        sh(["git", "init", "-q"], cwd=proj2)
        sh(["git", "config", "user.email", "t@t"], cwd=proj2)
        sh(["git", "config", "user.name", "t"], cwd=proj2)
        sh(["git", "add", "-A"], cwd=proj2)
        sh(["git", "commit", "-qm", "init"], cwd=proj2)
        sh(["bash", str(INSTALL), "--target", str(proj2), "--bootstrap"])
        sh(["git", "add", "-A"], cwd=proj2)
        sh(["git", "commit", "-qm", "install"], cwd=proj2)
        cand2 = proj2 / ".agent" / "rule-candidates.md"
        for name in ("A", "B", "C", "D"):
            (proj2 / "src" / "components" / f"{name}.js").write_text(f"export const {name} = 1\n")
            sh([sys.executable, "scripts/suggest-rule-updates.py", "--quiet"], cwd=proj2)
        pending_drift = sum(
            1
            for line in cand2.read_text(encoding="utf-8").splitlines()
            if line.startswith("### drift:")
        )
        check("one drift candidate per rule (no per-file explosion)", pending_drift <= 1,
              f"got {pending_drift} drift candidate blocks after 4 incremental edits")

        # Phantom: a Markdown heading inside a human decision note must NOT
        # become a candidate that blocks --check.
        text = cand2.read_text(encoding="utf-8")
        # Resolve the drift candidate with a note containing a sub-heading.
        text = text.replace("Status: pending", "Status: checked-unchanged", 1)
        text = text.replace(
            "- pending",
            "- reviewed; see notes below\n### TODO follow up on naming\n- still fine",
            1,
        )
        cand2.write_text(text, encoding="utf-8")
        sh([sys.executable, "scripts/suggest-rule-updates.py", "--quiet"], cwd=proj2)
        strict2 = sh([sys.executable, "scripts/suggest-rule-updates.py", "--quiet", "--check"], cwd=proj2)
        check("markdown heading in note is not a phantom candidate", strict2.returncode == 0,
              f"exit {strict2.returncode}; a '### TODO' note became a pending candidate")

        total = passed + failed
        status = "OK" if failed == 0 else "FAIL"
        print(f"[{status}] scanner: {passed}/{total} passed")
        for f in fails:
            print(f"    - {f}")
        return 0 if failed == 0 else 1
    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
