# Rule Candidates

This file is the automatic-growth inbox for project rules. Scripts generate candidates here; Claude/Codex agents decide and update official `.agent/*` docs when warranted.

Rules must not grow by blindly copying scanner output into durable docs. The agent should inspect current code/config/tool evidence, then choose one status for each candidate:

- `promoted`: verified durable fact was added to the appropriate `.agent/*` doc.
- `checked-unchanged`: reviewed evidence and existing rules still cover it.
- `rejected`: not durable, too specific, obvious from code, or not useful as a rule.
- `needs-user`: high-risk fact cannot be proven from repo/tool evidence. Record the uncertainty; do not ask the user unless the current task depends on it.
- `pending`: not yet handled. Pending high-risk (`risk:*`) candidates block finalization; drift and command candidates are advisory and do not block.

Agent rule: decide autonomously whenever current evidence is enough. Do not ask the user to classify ordinary candidates.

# BEGIN GENERATED RULE CANDIDATES
- no current candidates
# END GENERATED RULE CANDIDATES
