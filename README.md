# Universe Game

Shared repository for a browser-based 3D sci-fi exploration game, built with an automated **GPT + Claude Code** collaboration workflow.

## Games in this repository

- [`meridian/`](meridian/): **MERIDIAN — The Quiet System**. Fly a survey ship between two planets and a moon, land, walk, scan, activate three relays and transmit the survey. Play locally: `cd meridian && npm ci && npm run build && npm run preview`, then open http://localhost:4173/. Details in [`meridian/README.md`](meridian/README.md); verification record in [`meridian/PROGRESS.md`](meridian/PROGRESS.md).

## How the collaboration works

One manual trigger runs one bounded cycle in GitHub Actions — no copying messages between chats:

1. **GPT** (OpenAI API, `gpt-6.1-sol` by default) writes an implementation plan.
2. **Claude Code** (Anthropic API, headless CLI) implements the plan and runs checks.
3. **GPT** reviews Claude's actual diff and report, and gives a verdict.
4. **Claude Code** makes one correction pass, only if GPT requested changes.
5. The workflow commits everything to an `ai/run-<id>` branch, saves the full exchange in `agent-runs/<date>-run-<id>/transcript.md`, and opens a **pull request for you to review**.

Limits: 2 GPT calls and at most 2 Claude Code passes per run, a per-pass turn cap and USD budget cap for Claude, a 90-minute job timeout, one run at a time, and nothing is ever merged automatically. The agents get no GitHub credentials, Claude never sees the OpenAI key, and edits to `.github/`, `scripts/ai_bridge.py`, `AGENTS.md` or `agent-runs/` are reverted.

This is API-based coordination. The GPT here is a fresh API call, not your ChatGPT conversation, and it can't see that chat history. API usage is billed separately from ChatGPT or Claude subscriptions.

## One-time setup

1. **Settings → Secrets and variables → Actions → Secrets**: add `OPENAI_API_KEY` (platform.openai.com) and `ANTHROPIC_API_KEY` (platform.claude.com).
2. **Settings → Actions → General → Workflow permissions**: tick **Allow GitHub Actions to create and approve pull requests**.
3. Optional, under **Variables**: `OPENAI_MODEL`, `OPENAI_REASONING_EFFORT` (`low`–`max`, default `medium`), `CLAUDE_MODEL` (e.g. `sonnet`, `opus`; default: Claude Code's default), `CLAUDE_MAX_BUDGET_USD` (per pass, default `3`), `CLAUDE_MAX_TURNS` (default `40`).

## Start a run

**From GitHub:** Actions → **AI Collaboration (GPT + Claude Code)** → **Run workflow** → type the task → **Run workflow**. When it finishes, the run summary links the pull request.

**From a terminal or Claude Code** (with the GitHub CLI signed in):

```bash
gh workflow run ai-collaboration.yml --repo zubersss/universegame --ref main \
  -f task="Add a pause menu that opens with Esc and shows Resume / Restart buttons"
gh run watch --repo zubersss/universegame   # follow it live
gh pr list --repo zubersss/universegame     # the PR it opened
```

Write concrete tasks with clear acceptance criteria. Each run is independent; to continue work, merge (or check out) the PR first and then start a new run.

## If a run fails

The job summary says which step failed and why: missing secret, model not available to the key, auth or billing error, Claude limits, or PR permission. The partial transcript is attached to the run as the `agent-run` artifact.

## Files

- `AGENTS.md`: development rules both agents follow
- `scripts/ai_bridge.py`: the bounded coordinator (Python standard library only)
- `.github/workflows/ai-collaboration.yml`: the manual workflow
- `agent-runs/`: saved transcripts of every run
