# Universe Game — agent operating rules

Objective: build the highest-quality **playable browser-based 3D sci-fi exploration game** per unit of development effort, not the largest codebase.

1. Start with a playable vertical slice. Make the browser launch path obvious.
2. Prefer proven libraries (for example Three.js and Vite) over custom rendering engines, unnecessary abstractions, or elaborate bespoke frameworks.
3. Work on the exact assigned task. Do not redesign unrelated systems.
4. Measure progress by visible behavior, control responsiveness, stable frame pacing, test results, and visual quality.
5. Keep a short TODO list, prioritize blockers, and complete the highest-impact changes first.
6. Prefer minimal cohesive changes and reuse existing working code; avoid rewrites.
7. Handle errors, resize, input focus, WebGL fallback, and resource disposal where applicable.
8. Run available lint/build/test checks. If no checks exist, add only small essential smoke checks.
9. Never add secrets, external telemetry, crypto miners, paid assets, or license-incompatible dependencies.
10. Do not modify CI/security workflows, credentials, billing, or repository access policy during a gameplay task.
11. Avoid speculative polish until the requested behavior works and has been exercised.
12. Summarize changes, validation, caveats, and next prioritized step.

## Automated GPT + Claude Code collaboration

The workflow `.github/workflows/ai-collaboration.yml` (run by `scripts/ai_bridge.py`) connects two agents through the APIs:

- **GPT** (OpenAI API) is the planner and reviewer: one plan, one review per run.
- **Claude Code** (Anthropic API, headless CLI) is the implementer: one implementation pass, plus one correction pass only if GPT's review says `VERDICT: CHANGES_REQUESTED`.
- The agents never push, merge, or open PRs themselves. The workflow commits their work to an `ai/run-<id>` branch and opens a pull request for a human.
- `.github/`, `scripts/ai_bridge.py`, `AGENTS.md`, and `agent-runs/` are off-limits to the agents; edits there are reverted automatically.
- Every run's full exchange is saved in `agent-runs/<date>-run-<id>/transcript.md` (plus `run.json`).
