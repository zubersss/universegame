# What I need from you

Owner: LEAD (only the Lead edits this). Do the open items below, then tell the Lead session
`done: USER-0X`. Each item has exact steps. Everything here fits in one sitting (about
90 minutes, mostly downloads).

## Open

### USER-01 — Install Git for Windows and Git LFS (10 min)
1. Open https://git-scm.com/download/win and run the installer. Keep every default; on the
   "Adjusting your PATH" page choose "Git from the command line and also from 3rd-party
   software".
2. Open https://git-lfs.com and run the installer.
3. Open PowerShell (Start → type "PowerShell" → Enter) and run: `git lfs install`
   You should see "Git LFS initialized."

### USER-02 — Clone the repo (5 min)
1. In PowerShell run: `mkdir C:\dev` then
   `git clone https://github.com/zubersss/universegame.git C:\dev\universegame`
2. If a GitHub sign-in window appears, sign in (Git Credential Manager stores it).
3. Run `cd C:\dev\universegame` then `git status`. You should see "On branch main".
If you already have the repo somewhere else, use that folder everywhere instead of
`C:\dev\universegame`.

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

### USER-05 — Install Claude Code (10 min)
1. Follow https://docs.claude.com/en/docs/claude-code/overview for the Windows install
   (it needs Git for Windows from USER-01).
2. In PowerShell run `cd C:\dev\universegame` then `claude`. Sign in when asked. Type
   `/exit` to leave. Repeat once more to confirm it starts without errors.

### USER-06 — Laptop settings for an 8 GB machine (5 min)
1. Windows Settings → System → Storage: make sure the drive has at least 40 GB free.
2. Close browsers and other apps while the team works.
3. Optional but helpful: Settings → System → About → Advanced system settings → Performance
   Settings → Advanced → Virtual memory → "Automatically manage paging file size".

### USER-07 — Start the worker sessions (after the Lead writes READY FOR WORKERS below)
1. Open two more PowerShell windows. In each: `cd C:\dev\universegame` then `claude`.
2. Paste the UNITY kickoff into one and the BLENDER kickoff into the other
   (`coordination/KICKOFF_MESSAGES.md`).

## Done
(the Lead moves items here with the date)

## Status
(the Lead writes READY FOR WORKERS here when USER-01…06 are confirmed)
