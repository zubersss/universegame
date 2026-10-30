# What I need from you

Owner: LEAD (only the Lead edits this). Do the open items below, then tell the Lead session
`done: USER-0X`. Each item has exact steps. Everything here fits in one sitting (about
90 minutes, mostly downloads).

## Open

### USER-03 — Install Unity Hub and Unity 6 LTS (40 min, mostly download)
1. Open https://unity.com/download and install Unity Hub. Open it and sign in (create a free
   Personal account if asked).
2. In Unity Hub click "Installs" → "Install Editor" → pick the newest version labelled
   **LTS** that starts with **6000** → tick **Windows Build Support (IL2CPP)** → Install.
3. When it finishes, tell the Lead the exact version number shown in Hub (for example
   6000.0.58f1).

### USER-04 — Install Blender LTS (10 min)
1. Open https://www.blender.org/download/lts/ and download the newest **LTS** installer for
   Windows. Run it with defaults.
2. Tell the Lead the version number (shown on the download page, for example 4.5.x LTS).

### USER-07 — Start the worker sessions (after the Lead writes READY FOR WORKERS below)
1. Open two more PowerShell windows. In each: `cd C:\dev\universegame` then `claude`.
2. Paste the UNITY kickoff into one and the BLENDER kickoff into the other
   (`coordination/KICKOFF_MESSAGES.md`).

### USER-08 — Optional: let the team run PowerShell commands without prompts (2 min)
On Windows, Claude Code runs commands through PowerShell as well as Bash, and the
`Bash(...)` allow rules in `.claude/settings.json` don't cover PowerShell. The Lead added
matching PowerShell *deny* rules, but isn't allowed to grant itself new *allow* rules.
If you get too many "allow this command?" prompts, tell the Lead "approve PowerShell
allow rules" and accept the edit when Claude Code asks you. Otherwise skip this.

## Done
- 2026-10-30 · USER-01 (Git 2.56 and Git LFS 3.8 already installed; the Lead ran
  `git lfs install --local`), USER-02 (repo already at `C:\dev\universegame`),
  USER-05 (Claude Code 2.1.314 already running), USER-06 (89 GB free, 7.6 GB RAM) —
  verified by the Lead.

## Status
(the Lead writes READY FOR WORKERS here when USER-01…06 are confirmed)
