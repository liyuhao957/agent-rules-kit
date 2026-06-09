# Verification Map

Use this map to choose evidence for claims.

| Claim Type | Preferred Evidence |
|---|---|
| Code structure | Current files, search results, imports, call graph |
| Build correctness | Current build command output |
| Test correctness | Targeted tests, then broader tests when risk is high |
| UI correctness | Running app/page, browser/device/simulator inspection, screenshots when feasible |
| Copy/localization | Current string keys, rendered UI, localization files |
| Data behavior | Model/schema code, migration tests, fixtures, local DB or controlled data flow |
| Sync/remote behavior | Real sync tool, logs, remote API, authenticated CLI/MCP |
| Release state | Authenticated release/store/CI/tool output |
| Another agent claim | Current diff, code, test/build output, handoff only as context |
| Documentation truth | Current code/config/tool output plus doc citation |

Never upgrade an inferred claim into a verified claim in the final reply.

