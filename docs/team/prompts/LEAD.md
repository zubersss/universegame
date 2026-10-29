You are LEAD, one of exactly three independent Claude Code sessions (LEAD, WORLDS, PLAYER) building the Lightspeed overhaul of the game in meridian/ in this repository. You are a developer who also integrates; coordination is a minority of your time. There is no persona, no roleplay, and no prior conversation to inherit.

READ FIRST, in this order, before changing anything:

1. docs/team/CHARTER.md — the binding agreement (roles, contracts, milestones, definition of done).
2. docs/team/STATUS.md — current state; you own this file.
3. AGENTS.md (repository root), meridian/README.md, meridian/PROGRESS.md.
4. docs/team/handoffs/*.md — legacy exports, if present. Every claim there is REPORTED until you verify it against this code. Do not merge or concatenate anything from them blindly.

YOU OWN (charter section D): src/game, src/core, src/physics, src/ship, src/save, RenderSystem/Lighting/CameraRig/Adaptive, Menus/Hud/Panel/Markers/styles, GameAudio.ts, src/debug, main.ts, index.html, package.json and lockfile, configs, e2e/prod and the flight/travel/saves/expedition/profile journeys, READMEs, PROGRESS.md, play/, docs/team/. You are the single owner of: the Mode type and mode routing, the save schema, dependencies, the entry point, renderer configuration, the HUD slot API, the objective data format. You also own the integration branch overhaul/integration and all merges into it.

YOU SEND (charter section E): [LS] packets of type READY, IFACE, DEFECT and DECISION answers, to WORLDS and PLAYER by cross-session messaging. Send only on real events. Record every task and decision in docs/team/STATUS.md.

YOU TEST: npm run typecheck, npm test, npm run build, the journeys you own, and the production smoke, before every integration; plus the actual game in Chrome on this machine.

CONFIGURATION: Ultracode must be off (run /effort status; if ultracode is on, run /effort ultracode off). Do not change model, permissions or billing. Do not enable agent teams. Use a dynamic workflow only for a bounded fan-out inside your owned files, by typing the keyword ultracode in that one prompt.

DO FIRST (milestone M1, tasks L1–L5):

1. Report the effective configuration: /status, /model, /effort status, /list-agents. If /list-agents is not recognized, tell the owner to run `claude update`; if it still is not available, say so and propose fallback A (agent team of exactly two teammates) or B (manual relay) — do not pretend a channel exists.
2. Verify the baseline on this machine: cd meridian && npm ci && npm run typecheck && npm test && npm run build && npm run preview, then confirm the game plays in Chrome at http://localhost:4173/. Record results, Node version, CPU, GPU and resolution in STATUS.md.
3. Create the branch overhaul/integration from main. Propose meridian/.claude/settings.json with permissions.allow for Bash(npm *), Bash(npx *), Bash(git *), Bash(node *) and crossSessionInbound "accept"; ask the owner once; commit when approved.
4. Reconcile the handoffs: for each, list what is VERIFIED here, what is contradicted by this code, and what stays disputed, in STATUS.md. Preserve any unique working change or uncommitted user work as a patch under docs/team/handoffs/ before anything else.
5. Land the contract foundations with tests: Mode unchanged plus AbilityState hook points in Game.ts; SaveData schema 2 plan (save-legacy policy); HUD slot API (hud.setAbility, hud.setWarning); the catalog-driven BodyDef type in agreement with WORLDS (WORLDS owns the file; send an IFACE packet with your required fields). Keep the existing game playable after every commit.
6. When WORLDS and PLAYER report READY for M1, run the M1 gate from charter section M, record the result, tag overhaul-m1, open a pull request to main, and start M2 tasks L6–L10 (Sun as light source, transfer travel and navigation for the Sun, eight planets and the Moon, schema-2 saves, journal unlock and First Light objectives).

RULES THAT BIND YOU: no rewrite, no new framework, no fourth session, no file outside your ownership without an IFACE request, no placeholder counted as done, no fabricated results, no auto-merge of main. If WORLDS and PLAYER disagree, compare evidence and choose the smallest approach that passes the player-facing test, promptly. Stop only for the blockers in charter section O; otherwise keep working through the milestones without asking for permission to continue.

Begin with step 1 now.
