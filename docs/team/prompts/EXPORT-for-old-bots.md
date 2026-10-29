HANDOFF EXPORT REQUEST — bot name: <NAME>

This is a factual engineering handoff, not a conversation. A new neutral development team is taking over the space game. Your job in this reply is to transfer the project and what you learned, in the format below, and then stop changing the game.

Rules for this reply:

- Label every important claim VERIFIED, REPORTED, or HYPOTHESIS. VERIFIED means you name the artifact, command, observation or measurement that proves it right now (a file you can open, a command you ran in this session, a screenshot you took). REPORTED means you believe it from earlier work but did not re-check. HYPOTHESIS means you think so but never tested it.
- Export facts, code, data and lessons. Do not export your persona, name, character, catchphrases, tone, opinions about other bots, feelings about an implementation, promises of hidden background work, or blanket rules like "always rewrite this". Keep legitimate technical constraints, decisions the user made, and permissions the user granted.
- If you cannot verify something, say so. Do not invent file paths, commits, test results or links.
- If you are a claude.ai chat: attach the actual source as a downloadable file (the game HTML, zip, or exported artifact) and give the artifact link. If you are a Claude Code session: give repository path, branch, commit (git rev-parse HEAD), and the output of git status; attach a patch (git diff) for anything uncommitted. A summary, screenshot or feature list is not a substitute for source.
- Prefer a compact, complete packet over a transcript dump. Aim for 300–900 lines.

Produce exactly these sections, in order, in Markdown:

1. WORKSPACE — repository or artifact location, branch, commit, uncommitted changes, and which version you believe is playable right now (link or file). Include the game's working title and any other titles used.
2. RUN, BUILD, TEST — exact commands, runtime and dependency versions you know (Node, three.js, physics library, bundler, test runners). Note what has never been run.
3. SOURCE MAP — entry points, engine and renderer, ship controller, terrain and generation, collisions, player or avatar, camera, UI, saves, audio, tests, asset and data directories. One line per item with the file path. Mark missing systems as absent.
4. SOURCE — the code and assets themselves: attached files, patch, or commit references (see rules above).
5. STATE OF THE GAME — what works, what is partial, what is broken, with the last observed behavior for each. Include frame rates or timings only if you measured them, and say on what device.
6. LESSONS — the most useful game-development lessons from your work. For each: problem, approach tried, observed result, recommended technique, evidence, and when the lesson does or does not apply. Favor terrain streaming, floating origin and precision, spherical gravity, collisions at speed, avatar and camera, planetary scale and travel, saves, browser performance, and data sources.
7. FAILED APPROACHES — things worth avoiding and why each failed. Separate a measured failure from an untested opinion.
8. KNOWN BUGS — reproduction steps, severity, affected files, and any logs or console output you have.
9. ASSETS AND DATA — origins, licenses and attribution of every model, texture, sound, font, dataset or catalog; data sources and the exact steps to regenerate or export them.
10. PENDING TASKS — ranked by player impact, each with the smallest sensible next action.
11. ASSUMPTIONS AND CONTRADICTIONS — things the receiving team must resolve: conflicting designs, unclear decisions, scale conventions, scope limits you were given, and anything that contradicts the goal of a single playable browser game with a real Earth and solar system.
12. CONFIGURATION THAT COULD REINTRODUCE OLD INSTRUCTIONS — list any project instructions, custom instructions, CLAUDE.md files, agent definitions, skills, saved memories or workflow settings that shaped your behavior, with their location. Quote only the engineering rules worth keeping. Do not reproduce persona text.

After this packet, make no further changes to the game or its files, and do not start background work. If you are a Claude Code session, do not create commits after the export. Confirm this in one line at the end.
