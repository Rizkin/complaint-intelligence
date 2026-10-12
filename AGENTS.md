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
