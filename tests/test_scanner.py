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
VALIDATE = REPO_ROOT / "scripts" / "validate-installed-project.sh"


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

        # Bootstrap-generated project rules must route Claude too. The rule is
        # named project-ui in drift-map, but the path belongs in the ui-copy
        # pointer because that is the domain doc agents should load.
        proj3 = work / "proj3"
        (proj3 / "src" / "components").mkdir(parents=True)
        (proj3 / "src" / "components" / "Button.js").write_text("export const B = 1\n")
        (proj3 / "package.json").write_text('{"name":"r"}\n')
        sh(["git", "init", "-q"], cwd=proj3)
        sh(["git", "config", "user.email", "t@t"], cwd=proj3)
        sh(["git", "config", "user.name", "t"], cwd=proj3)
        sh(["git", "add", "-A"], cwd=proj3)
        sh(["git", "commit", "-qm", "init"], cwd=proj3)
        install3 = sh(["bash", str(INSTALL), "--target", str(proj3), "--bootstrap"])
        pointer3 = proj3 / ".claude" / "rules" / "ui-copy.md"
        check("bootstrap install succeeds for project routing test", install3.returncode == 0,
              install3.stderr[-400:])
        check("project-ui path mirrored into ui-copy pointer",
              '"src/components/**"' in pointer3.read_text(encoding="utf-8"),
              pointer3.read_text(encoding="utf-8")[:400])
        validate3 = sh(["bash", str(VALIDATE), str(proj3)])
        check("validator accepts project rule covered by domain pointer", validate3.returncode == 0,
              validate3.stdout[-500:] + validate3.stderr[-500:])

        drift3 = proj3 / ".agent" / "drift-map.yml"
        review3 = proj3 / ".agent" / "adaptation-review.md"
        before_drift = drift3.read_text(encoding="utf-8")
        before_pointer = pointer3.read_text(encoding="utf-8")
        review_text = review3.read_text(encoding="utf-8")
        review_text = review_text.replace("Status: pending", "Status: adapted", 1)
        review3.write_text(review_text, encoding="utf-8")
        # New scanner evidence after adaptation should refresh reports/maps,
        # not re-open the generated routing block or overwrite tightened rules.
        (proj3 / "src" / "components" / "AfterAdapt.js").write_text("export const A = 1\n")
        sh([sys.executable, "scripts/bootstrap-project-context.py"], cwd=proj3)
        check("adapted bootstrap leaves drift-map routing unchanged",
              drift3.read_text(encoding="utf-8") == before_drift,
              "drift-map changed after Status: adapted")
        check("adapted bootstrap leaves Claude pointer routing unchanged",
              pointer3.read_text(encoding="utf-8") == before_pointer,
              "ui-copy pointer changed after Status: adapted")

        stale = work / "stale"
        (stale / ".agent").mkdir(parents=True)
        (stale / "live").mkdir()
        (stale / "live" / "file.txt").write_text("ok\n")
        sh(["git", "init", "-q"], cwd=stale)
        sh(["git", "config", "user.email", "t@t"], cwd=stale)
        sh(["git", "config", "user.name", "t"], cwd=stale)
        sh(["git", "add", "-A"], cwd=stale)
        sh(["git", "commit", "-qm", "init"], cwd=stale)
        (stale / ".agent" / "adaptation-review.md").write_text("Status: adapted\n", encoding="utf-8")
        (stale / ".agent" / "drift-map.yml").write_text(
            "\n".join(
                [
                    "rules:",
                    "  - name: stale-rule",
                    "    paths:",
                    '      - "gone/a/**"',
                    '      - "gone/b/**"',
                    '      - "gone/c/**"',
                    '      - "gone/d/**"',
                    '      - "gone/e/**"',
                    '      - "gone/f/**"',
                    "    docs:",
                    '      - ".agent/domains/example.md"',
                    '    reason: "test"',
                    "",
                ]
            ),
            encoding="utf-8",
        )
        drift_check = sh([sys.executable, str(proj3 / "scripts" / "check-doc-drift.py")], cwd=stale)
        warning_lines = [line for line in drift_check.stdout.splitlines() if line.startswith("Drift-map warning:")]
        check("stale-glob warnings are grouped by rule", len(warning_lines) == 1,
              drift_check.stdout)
        check("stale-glob warning is capped with remainder count", "+1 more" in warning_lines[0] if warning_lines else False,
              warning_lines[0] if warning_lines else drift_check.stdout)

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
