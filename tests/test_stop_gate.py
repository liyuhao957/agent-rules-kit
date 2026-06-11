#!/usr/bin/env python3
"""Contract tests for the Stop-gate (stop_quality_reminder.py).

Target contract (post-redesign): the gate blocks ONLY on pending high-stakes
`risk:*` candidates (secrets / billing / release / prod). Ordinary drift and
command candidates are advisory and never block — they are surfaced, not
gated. This keeps the per-session ceremony tax near zero for normal work while
preserving the one guard that earns its cost.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from lib import REPO_ROOT, STOP_HOOK, run_hook

INSTALL = REPO_ROOT / "scripts" / "install-rules.sh"


def sh(args, cwd=None, env=None):
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True, env=env)


def install_project(root: Path) -> Path:
    proj = root / "proj"
    (proj / "src").mkdir(parents=True)
    (proj / "src" / "app.js").write_text("console.log(1)\n")
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


def set_candidate(path: Path, id_substr: str, status: str, note: str) -> None:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    out: list[str] = []
    active = False
    in_notes = False
    for line in lines:
        m = re.match(r"^###\s+(\S+)", line)
        if m:
            active = id_substr in m.group(1)
            in_notes = False
            out.append(line)
            continue
        if active and re.match(r"^Status:\s*\S+", line):
            out.append(f"Status: {status}")
            continue
        if active and line.strip() == "Decision notes:":
            in_notes = True
            out.append(line)
            continue
        if active and in_notes and line.strip() == "- pending":
            out.append(f"- {note}")
            in_notes = False
            continue
        out.append(line)
    path.write_text("\n".join(out) + "\n", encoding="utf-8")


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

        # 1. loop-break flag always allows.
        code, _o, _e = run_hook(STOP_HOOK, {"stop_hook_active": True}, cwd=proj)
        check("stop_hook_active allows", code == 0, f"exit {code}")

        # 2. bypass env var allows.
        import os
        env = dict(os.environ, RULES_HOOK_ALLOW_PENDING="1")
        code, _o, _e = run_hook(STOP_HOOK, {}, cwd=proj, env=env)
        check("bypass env allows", code == 0, f"exit {code}")

        # 3. ordinary source change (drift only, no risk) is ADVISORY -> allow.
        (proj / "src" / "components").mkdir(parents=True, exist_ok=True)
        (proj / "src" / "components" / "Button.js").write_text("export const B = 1\n")
        code, _o, err = run_hook(STOP_HOOK, {}, cwd=proj)
        check("ordinary drift does not block", code == 0, f"exit {code}; stderr={err[:200]}")

        # 4. touching a high-stakes risk path BLOCKS.
        (proj / "config").mkdir(exist_ok=True)
        (proj / "config" / "pricing.ts").write_text("export const PRICE = 9\n")
        code, _o, err = run_hook(STOP_HOOK, {}, cwd=proj)
        check("risk path blocks", code == 2, f"exit {code}")
        check("risk block names risk candidate", "risk:" in err, f"stderr={err[:200]}")

        # 5. after resolving the risk candidate, advisory drift still does not block.
        set_candidate(cand, "risk:billing", "checked-unchanged", "reviewed pricing change; rules cover it")
        code, _o, err = run_hook(STOP_HOOK, {}, cwd=proj)
        check("resolved risk -> allow despite advisory drift", code == 0, f"exit {code}; stderr={err[:300]}")

        total = passed + failed
        status = "OK" if failed == 0 else "FAIL"
        print(f"[{status}] stop_gate: {passed}/{total} passed")
        for f in fails:
            print(f"    - {f}")
        return 0 if failed == 0 else 1
    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
