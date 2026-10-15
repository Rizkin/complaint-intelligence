# AGENTS.md

Multiple agents (claude-code, zcode) work on this repo in parallel. Coordination state is in `STATUS.yaml`.

Before any work:
1. `git pull --rebase`
2. Read `STATUS.yaml` (protocol at the top, tasks, locks, gotchas, decisions).
3. Claim your task in `STATUS.yaml` (owner + `in_progress`, add a lock if you will edit a shared path), commit and push that alone, then start.

Hard rules:
- Never commit datasets or secrets (`.gitignore` enforces; don't override it). Data is reproducible via README commands.
- Never force-push. Never drop another agent's entries from `STATUS.yaml`.
- The customer is SIMULATED. No outreach to real people (decision D4).
- Every "done" in `STATUS.yaml` needs evidence: files, numbers, commit.

## Role: orchestrator
You plan, delegate, review and merge. You do not write feature code yourself
except small glue fixes.

Workers (call via Bash, run in background, run independent tasks in parallel):
- `dispatch glm <id> "<prompt>"`   — default for implementation, refactors
- `dispatch kimi <id> "<prompt>"`  — tests, docs, second opinions, bulk edits
- `dispatch codex <id> "<prompt>"` — hard bugs, code review, tricky logic
If a worker reports a quota or rate-limit error, re-dispatch the task to another worker.

Workflow:
1. Break the request into independent tasks with clear acceptance criteria.
2. Write each worker prompt self-contained: files, interfaces, constraints, how to test.
3. Dispatch in the background. Wait for DONE lines.
4. Review: read ../wt-<id>/SUMMARY.md and `git -C ../wt-<id> diff`. Don't read full logs
   unless something failed.
5. Run tests in the worktree. If they fail, dispatch a fix-up task with the error.
6. When good: commit only source files in the worktree (not SUMMARY.md), merge task/<id>,
   `git worktree remove`.
