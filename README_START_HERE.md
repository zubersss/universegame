# MERIDIAN — Start Here

MERIDIAN is a 2D space-survival game set in our real solar system, built by three AI
sessions (Claude Code) that do all of the development. Your job is the part that needs
a human: install software, start the sessions, paste a few messages, playtest, and
resume a session when it stops. Everything else is automatic.

## What you need (one sitting, about 90 minutes including downloads)

Do these in order. Exact click-by-click steps are kept in `coordination/USER_ACTIONS.md`,
which the Lead session updates whenever it needs something from you.

1. **Git for Windows** (includes Git Bash) and **Git LFS**. Run `git lfs install` once.
2. **Unity Hub**, then inside it the latest **Unity 6 LTS** (6000.x) with the
   "Windows Build Support (IL2CPP)" module. Sign in with a free Unity account.
3. **Blender** — the current LTS release from blender.org (the download page labels it LTS).
4. **Claude Code** (from Anthropic's docs) signed in to your account.
5. A **GitHub** login that can push to `zubersss/universegame`.
6. Close browsers and other apps while the team works: the laptop has 8 GB of RAM and
   the team schedules its heavy jobs around that.

## Clone the repo (first time only)

In a terminal (PowerShell is fine), run:

`git clone https://github.com/zubersss/universegame.git C:\dev\universegame`

Skip this if the folder `C:\dev\universegame` already exists.

## Starting the team (first time)

Open **three** terminal windows (PowerShell is fine). In each, go to the repo folder,
for example `cd C:\dev\universegame`, then type `claude` to start a session.

1. **Window 1 — Lead Director.** Paste the LEAD kickoff message, then paste the whole
   architect output (all the files). The Lead saves every file, archives the old build,
   pins versions, and writes `coordination/USER_ACTIONS.md`. Wait until the Lead says the
   workers can start.
2. **Window 2 — Unity Engineer.** Paste the UNITY kickoff message.
3. **Window 3 — Blender Artist.** Paste the BLENDER kickoff message.

The kickoff messages are at the end of the architect output and are also saved by the
Lead at `coordination/KICKOFF_MESSAGES.md`.

## If a session stops, crashes, or hits a limit

Start it again the same way and paste the resume message, replacing the role word:

`Resume MERIDIAN as LEAD` / `Resume MERIDIAN as UNITY` / `Resume MERIDIAN as BLENDER`

The session rebuilds its context from the repo files. Nothing is lost between stops
because every result is committed and every status is written to a file.

## Your job while they work

- Check `coordination/USER_ACTIONS.md` once a day. Do the listed items, then tell the
  Lead session "done: <item id>".
- When the Lead reports a milestone build, open Unity (or the build in `Build/`), play
  for 15–30 minutes, and tell the Lead what felt wrong in plain words. You don't need to
  diagnose anything.
- Don't edit files in the repo yourself; tell the Lead what you want instead.
- If two sessions seem stuck for more than a day, paste `Resume MERIDIAN as LEAD` into the
  Lead window and ask it to "run a full review cycle and report".

## Where things are

- `coordination/TASK_BOARD.md` — what everyone is doing.
- `coordination/USER_ACTIONS.md` — the only file you need to act on.
- `docs/PROJECT_BIBLE.md` — the whole game design and technical plan.
- `Build/` — playable Windows builds at each milestone.
