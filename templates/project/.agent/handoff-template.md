# Agent Handoff

Copy this shape into `.agent/work/current.md` only when work is unfinished, another agent is likely to continue, or review needs extra context.

## Objective

What the user wanted.

## Next Step (start here)

The single concrete action the next agent should take first.

## Baseline

- Agent/tool: which agent wrote this and when.
- Baseline commit: output of `git rev-parse HEAD` when work started.
- Branch: current branch.
- Note: diffs against the baseline include `.agent/rule-candidates.md` regeneration churn — read that file's diff as inbox state, not as task changes.

## Current State

What is done, what remains, and what assumptions were made.

## Changed Files

- `path`: why it changed

## Candidate Inbox At Handoff

N pending in `.agent/rule-candidates.md` plus their ids, or "none". Pending items carry forward to whoever continues.

## Verification Performed

- Check/command:
- Result:

## Not Verified

What was not checked. Be explicit.

## Risks

What the next agent should inspect first.

## User-Owned Changes

Local changes that may not belong to this task and must not be reverted.
