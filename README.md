# Universe Game

Shared browser-game development repository with an opt-in GPT + Claude Code collaboration workflow.

## One-time setup
1. Open this repository's **Settings → Secrets and variables → Actions** and add repository secrets `OPENAI_API_KEY` and `ANTHROPIC_API_KEY`. Obtain API keys separately from https://platform.openai.com/api-keys and https://console.anthropic.com/.
2. In **Settings → Actions → General → Workflow permissions**, set **Read and write permissions**, and enable **Allow GitHub Actions to create and approve pull requests** if available.
3. Open **Actions → GPT + Claude Game Builder → Run workflow**; enter a concrete task.

The workflow executes once per manual trigger: GPT plans → Claude Code edits → GPT reviews → Claude Code repairs → GitHub pull request for your review. No auto-merge, no automatic recurring runs. Both model APIs may charge usage separately from ChatGPT/Claude subscriptions. Workflow uses GPT via OpenAI API (default model `gpt-6.1-sol`, configurable in YAML) and Anthropic's Claude Code CLI (account default model). To use a different supported model, edit the workflow.

This is *API-based coordination*, not a direct connection to this ChatGPT conversation. Never paste credentials into issues or commit them.

Key files: `AGENTS.md` (development rules), `scripts/ai_bridge.py` (bounded coordination), and `.github/workflows/ai-collaboration.yml` (manual trigger).
