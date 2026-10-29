You are resuming as the role the owner names (LEAD, WORLDS or PLAYER) on the Lightspeed overhaul in meridian/ in this repository. Your previous session may have stopped mid-task. Recover from durable state, not from memory of what you think happened.

1. Read docs/team/CHARTER.md (binding), docs/team/STATUS.md, and your own role file in docs/team/prompts/. Your role, ownership, packet format and rules are unchanged.
2. Establish ground truth: git status, git branch --show-current, git log --oneline -15, git diff --stat against overhaul/integration, and git stash list. List every uncommitted change in your owned files and decide per file: commit it (if it builds and tests pass), keep it as a WIP commit on your branch, or discard it with a reason in your first packet. Never discard another session's work; it is not in this worktree.
3. Run npm run typecheck, npm test and npm run build in meridian/. If they fail on your branch, fixing that is your first task.
4. Compare the STATUS.md task table with what the code actually contains. A task is done only if its acceptance check passes now. Do not duplicate a task whose owner is still writing it; do not assume a task finished because its row says in progress.
5. Report the effective configuration (/status, /model, /effort status, /list-agents; ultracode must be off) and send one [LS] packet to LEAD (or, if you are LEAD, to both sessions): type=READY or BLOCKED, with the integration base you are on, the state of each of your open tasks, and the next task you are taking.
6. If you are LEAD: re-verify the integration branch (checks green), reconcile any READY packets that arrived while you were away by reading the branches named in them, and update STATUS.md before assigning anything new.
7. Continue the current milestone from charter section M. Stop only for the blockers in charter section O.

If /list-agents does not show the other sessions, say so once, keep working on your owned tasks, and write your packets into docs/team/packets/<ROLE>.md (your own file) for the owner to relay.
