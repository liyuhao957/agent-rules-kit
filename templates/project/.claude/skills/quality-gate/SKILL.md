---
name: quality-gate
description: Use before finalizing non-trivial work to close the affected loops, intent, functional, logic, UI/copy, data, verification, and doc drift, with real evidence.
---

# Quality Gate

1. Apply `.agent/quality-gates.md` to every affected loop.
2. Choose evidence with `.agent/verification-map.md`; run validation commands from `.agent/command-contract.md`.
3. Run `python3 scripts/check-doc-drift.py`, then `python3 scripts/suggest-rule-updates.py`; resolve `.agent/rule-candidates.md` per `.agent/index.md` (At Finalize).
4. Final reply must distinguish verified, inferred, and unverified.
