# MERIDIAN — Project Rules (read first, every session)

MERIDIAN is a 2D, realistic-looking survival-exploration game set in our real solar
system: Terraria-style side view on each of the 8 planets, top-down view in space, real
gravity ratios everywhere. Unity 6 (URP 2D Renderer) + Blender-rendered art. Three
Claude Code sessions build it: LEAD (Lead Director), UNITY (Unity Engineer), BLENDER
(Blender Artist). The user has no development experience and does not edit files.

## Identify your role, then read in this order

Your role is the word in your kickoff or resume message. Then read:
1. `coordination/charters/<ROLE>.md` — your charter.
2. `coordination/status/<ROLE>_STATUS.md` — your own last status.
3. `coordination/TASK_BOARD.md` — tasks, owners, acceptance criteria.
4. `docs/PROJECT_BIBLE.md` — only the sections your current task needs (it's long).
5. `coordination/ASSET_CONTRACT.md` — if you touch anything under `Assets/_Game/Art/`.
6. `coordination/DECISIONS.md` — settled decisions; don't reopen them without new evidence.

## Folder ownership (write only inside your own folders)

| Owner   | Writes                                                                                              |
|---------|-----------------------------------------------------------------------------------------------------|
| LEAD    | `docs/`, `coordination/*.md`, `coordination/charters/`, `coordination/reviews/`, `coordination/status/LEAD_STATUS.md`, `Assets/_Game/Tests/LeadQA/`, `tools/paths.json`, `.claude/`, `CLAUDE.md`, `README_START_HERE.md`, `.gitignore`, `.gitattributes`, `docs/credits/lead.md` |
| UNITY   | `Assets/_Game/` except `Art/`, `Placeholders/`\* and `Tests/LeadQA/`; `Assets/_Game/Placeholders/`\*; `Packages/`, `ProjectSettings/`; `tools/unity_*.ps1`; `coordination/status/UNITY_STATUS.md`; `coordination/reports/unity/`; `docs/credits/unity.md` |
| BLENDER | `blender/`; `Assets/_Game/Art/`; `tools/blender_*.ps1`; `coordination/status/BLENDER_STATUS.md`; `coordination/reports/blender/`; `docs/credits/blender.md` |

\* `Placeholders/` is UNITY's. Nobody else edits another role's folders. Reading is always allowed.
Exception (D-016): every `.meta` file under `Assets/_Game/Art/` (and `Assets/_Game/Art.meta`)
is written and committed by UNITY, because the Unity Editor generates them and they hold
import settings. BLENDER never creates, edits, or commits `.meta` files.
Every file in `coordination/` has exactly one writer (the table above), so no update is
ever overwritten.

## Core rules

1. **Verifiable output every cycle.** A commit, a rendered file, or a passing test. A
   cycle of only reading or planning is a stall: write a status note and change approach.
2. **Three strikes.** Three failed attempts at one problem → write a short diagnosis in
   your status file (tried / happened / best guess) and switch approach or task.
3. **Never wait.** Blocked → log it in your status file, take the next Ready task. UNITY
   builds against placeholders; BLENDER works the asset list in priority order.
4. **Decide, log, continue.** Don't ask the user anything you can decide from the Bible.
   Human-only steps go to the Lead's `coordination/USER_ACTIONS.md` via your status file.
5. **Git protocol.** Stage and commit only your own paths:
   `git add <your paths>` then `git commit -m "[role] <task-id> <summary>" -- <your paths>`,
   then `git push`. Never `git add -A`, `git add .`, force-push, rebase, history rewrite,
   or deleting `archive/meridian-v1`. If git reports `index.lock`, wait 5 s and retry (3×).
   Binaries go through Git LFS (`.gitattributes`). Commit sources and final exports only.
6. **HeavyJobLock.** Before a heavy job (Blender render above preview size, Unity batch
   compile/test/build/Addressables build) check `coordination/locks/` for another role's
   lock younger than 2 h and check for a running Unity Editor or Blender by path, not by
   name: `Get-Process unity,blender -ErrorAction SilentlyContinue | Where-Object { $_.Path -like '*\Hub\Editor\*' -or $_.Path -like '*Blender Foundation*' }`.
   Ignore `C:\Program Files\Unity Hub\resources\unity.exe` (the Hub's always-on background
   service); a plain `tasklist` name match always hits it (D-015). Clear → write
   `coordination/locks/heavy_<role>.lock` (ISO time + job), run, delete it. Not clear → do
   light work and re-check later. Only LEAD deletes another role's lock, and logs it.
   **Fair turns and memory (D-026).** Not clear → write `coordination/locks/want_<role>.lock`
   (ISO time + job); delete it when you get the lock. When you release the lock, don't take
   it again while another role's `want_*.lock` younger than 30 min exists; they go next.
   Don't start a heavy job with less than 1.5 GB free physical memory
   (`(Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory / 1MB`). One heavy job
   holds the lock ≤ 20 min. UNITY batches checks: one compile + EditMode + PlayMode run
   per task hand-off, not after every edit.
   **Strict turns (D-037).** If another role's `want_*.lock` exists when you release, you
   may not start another heavy job until that role has run one job, removed its want file,
   or its want file is older than 30 min. This holds even while the waiter is blocked on
   memory, because your idle time is what frees the memory. A batched check counts as one job
   only when it's one wrapper call that holds the lock throughout. After your own job, don't
   re-file your want while another role's want exists; file it only after that role takes the
   lock. Otherwise each side yields to the other and both stall (D-039).
7. **Accepted work stays accepted.** Don't re-polish Done tasks unless LEAD reopens them.
8. **Stay inside the repo.** No system installs, no registry/settings changes; list those
   in your status file for USER_ACTIONS.
9. **Budgets are requirements** (Bible §11): 60 FPS at 1080p on integrated graphics,
   ≤ 2.5 GB RAM in the build, and the dev workflow must fit 8 GB.
10. **Status after every task.** Your status file is how the others trust you and how a
    fresh session resumes. Update it when you start a task, finish one, hand off, or block.
