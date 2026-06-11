#!/usr/bin/env python3
"""Integration test: the documented honest-deferral adaptation path must pass
strict validation.

Round-1 found that deferring product-invariants/user-journeys (per
adapt-rules.md) could not pass validate-installed-project.sh --require-adapted.
This test follows the deferral path verbatim and asserts the strict validator
(with both flags) returns exit 0.
"""

from __future__ import annotations

import re
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


def resolve_pending_candidates(path: Path) -> None:
    """Flip every pending candidate to checked-unchanged with a real note,
    exactly what an agent does at finalize."""
    text = path.read_text(encoding="utf-8")
    out: list[str] = []
    in_notes = False
    for line in text.splitlines():
        if re.match(r"^Status:\s*pending\s*$", line.strip()):
            out.append("Status: checked-unchanged")
            continue
        if line.strip() == "Decision notes:":
            in_notes = True
            out.append(line)
            continue
        if in_notes and line.strip() == "- pending":
            out.append("- reviewed against current code; existing rules still cover this")
            in_notes = False
            continue
        if in_notes and line.strip() == "":
            in_notes = False
        out.append(line)
    path.write_text("\n".join(out) + "\n", encoding="utf-8")


def main() -> int:
    work = Path(tempfile.mkdtemp())
    try:
        proj = work / "proj"
        (proj / "src").mkdir(parents=True)
        (proj / "src" / "app.js").write_text("console.log(1)\n")
        (proj / "package.json").write_text('{"name":"p","scripts":{"test":"echo ok","build":"echo built"}}\n')
        sh(["git", "init", "-q"], cwd=proj)
        sh(["git", "config", "user.email", "t@t"], cwd=proj)
        sh(["git", "config", "user.name", "t"], cwd=proj)
        sh(["git", "add", "-A"], cwd=proj)
        sh(["git", "commit", "-qm", "init"], cwd=proj)

        inst = sh(["bash", str(INSTALL), "--target", str(proj), "--bootstrap"])
        if inst.returncode != 0:
            print(f"[FAIL] adapt_deferral: install failed\n{inst.stderr}")
            return 1

        agent = proj / ".agent"

        # command-contract.md: verify commands (clear the project-specific markers).
        cc = agent / "command-contract.md"
        cc_text = cc.read_text(encoding="utf-8")
        cc_text = cc_text.replace("| Unit tests | project-specific |", "| Unit tests | `npm test` |")
        cc_text = cc_text.replace("| Build | project-specific |", "| Build | `npm run build` |")
        # Remaining optional rows: drop the marker token honestly.
        cc_text = cc_text.replace("project-specific", "n/a")
        cc.write_text(cc_text, encoding="utf-8")

        # product-invariants.md: real verified invariant (clears "Replace this template").
        pi = agent / "product-invariants.md"
        pi.write_text(
            "# Product Invariants\n\n- The CLI prints deterministic output for `npm test`.\n", encoding="utf-8"
        )

        # user-journeys.md: DEFER honestly — replace placeholders with a needs-user note.
        uj = agent / "user-journeys.md"
        uj.write_text(
            "# User Journeys\n\nneeds-user: no UI in this CLI project; journeys not yet established.\n",
            encoding="utf-8",
        )

        # adaptation-review.md: mark adapted, tick boxes, replace pending placeholders.
        ar = agent / "adaptation-review.md"
        ar_text = ar.read_text(encoding="utf-8")
        ar_text = ar_text.replace("Status: pending", "Status: adapted")
        ar_text = ar_text.replace("Adapted by: pending", "Adapted by: test 2026-06-10")
        ar_text = ar_text.replace("Last reviewed: pending", "Last reviewed: 2026-06-10")
        ar_text = ar_text.replace("- [ ]", "- [x]")
        ar_text = ar_text.replace("- pending", "- verified: npm test/build; user-journeys deferred as needs-user")
        ar.write_text(ar_text, encoding="utf-8")

        # Resolve generated candidates with real notes.
        resolve_pending_candidates(agent / "rule-candidates.md")

        result = sh(
            ["bash", str(VALIDATE), str(proj), "--require-adapted", "--require-candidates-reviewed"]
        )
        ok = result.returncode == 0
        if ok:
            print("[OK] adapt_deferral: 1/1 passed")
            return 0
        print("[FAIL] adapt_deferral: strict validator rejected the documented deferral path")
        print(f"    stdout: {result.stdout.strip()}")
        print(f"    stderr: {result.stderr.strip()}")
        return 1
    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
