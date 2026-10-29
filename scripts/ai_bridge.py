#!/usr/bin/env python3
"""GPT (OpenAI API) + Claude Code collaboration bridge.

One bounded run:
  1. GPT plans the task                      (OpenAI Responses API)
  2. Claude Code implements it               (claude -p, headless)
  3. GPT reviews Claude's diff + report      (OpenAI Responses API)
  4. Claude Code applies the review          (only if GPT requested changes)
  5. Everything is committed on a work branch, with the full exchange saved
     under agent-runs/<run>/; the workflow then opens a pull request.

Hard limits: 2 GPT calls, at most 2 Claude Code passes, per-pass turn and USD
caps, no pushes from the agents, no edits to protected paths, and nothing is
ever merged automatically.

Standard library only. Configuration comes from environment variables (see
CONFIG below and .github/workflows/ai-collaboration.yml).
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path


def env(name: str, default: str = "") -> str:
    value = os.environ.get(name, "").strip()
    return value or default


CONFIG = {
    "openai_model": env("OPENAI_MODEL", "gpt-6.1-sol"),
    "openai_effort": env("OPENAI_REASONING_EFFORT", "medium"),
    "openai_max_output_tokens": int(env("OPENAI_MAX_OUTPUT_TOKENS", "16000")),
    "openai_base_url": env("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/"),
    "claude_model": env("CLAUDE_MODEL"),  # empty = Claude Code's default model
    "claude_budget_usd": float(env("CLAUDE_MAX_BUDGET_USD", "3")),  # per pass
    "claude_max_turns": int(env("CLAUDE_MAX_TURNS", "40")),  # implementation pass
    "claude_timeout_s": int(env("CLAUDE_TIMEOUT_SECONDS", "1800")),
    "max_diff_chars": int(env("MAX_DIFF_CHARS", "60000")),
    "max_task_chars": 6000,
}

ROOT = Path.cwd()
REPORTS_DIR = "agent-runs"
# Paths the agents must never change. Anything they touch here is reverted.
PROTECTED = (".github/", "scripts/ai_bridge.py", "AGENTS.md", REPORTS_DIR + "/")
MAX_FILE_BYTES = 20 * 1024 * 1024
# Credentials Claude Code does not need. It only receives ANTHROPIC_API_KEY.
STRIP_FROM_CLAUDE_ENV = (
    "OPENAI_API_KEY", "GH_TOKEN", "GITHUB_TOKEN",
    "ACTIONS_RUNTIME_TOKEN", "ACTIONS_ID_TOKEN_REQUEST_TOKEN", "ACTIONS_ID_TOKEN_REQUEST_URL",
)


class BridgeError(RuntimeError):
    """A failure that should stop the run with a clear message."""


# ----------------------------------------------------------------- utilities

def log(msg: str) -> None:
    print(f"[bridge {dt.datetime.now(dt.timezone.utc):%H:%M:%S}] {msg}", flush=True)


def run(*args: str, check: bool = True, input_text: str | None = None,
        timeout: int = 300, env_vars: dict | None = None) -> subprocess.CompletedProcess:
    proc = subprocess.run(list(args), input=input_text, text=True, capture_output=True,
                          timeout=timeout, env=env_vars)
    if check and proc.returncode != 0:
        raise BridgeError(f"`{' '.join(args[:3])} ...` exited {proc.returncode}: "
                          f"{(proc.stderr or proc.stdout)[-2000:]}")
    return proc


def git(*args: str, check: bool = True) -> str:
    return run("git", *args, check=check).stdout.strip()


def is_protected(path: str) -> bool:
    path = path[2:] if path.startswith("./") else path
    return any(path == p.rstrip("/") or path.startswith(p) for p in PROTECTED)


def clip(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n\n[... truncated {len(text) - limit} characters ...]"


# -------------------------------------------------------------------- OpenAI

def openai_get(path: str) -> dict:
    req = urllib.request.Request(
        f"{CONFIG['openai_base_url']}{path}",
        headers={"Authorization": "Bearer " + os.environ["OPENAI_API_KEY"]})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.load(resp)


def openai_error_message(exc: urllib.error.HTTPError) -> str:
    try:
        body = json.loads(exc.read().decode("utf-8", "replace"))
        err = body.get("error") or {}
        return f"HTTP {exc.code} {err.get('type', '')}/{err.get('code', '')}: {err.get('message', '')}"
    except Exception:  # noqa: BLE001 - never echo raw bodies/headers
        return f"HTTP {exc.code}"


def check_openai_model() -> None:
    """Free preflight: fails fast if the key is wrong or the model is not enabled."""
    try:
        openai_get(f"/models/{CONFIG['openai_model']}")
    except urllib.error.HTTPError as exc:
        raise BridgeError(
            f"OpenAI preflight failed for model '{CONFIG['openai_model']}': {openai_error_message(exc).rstrip('.')}. "
            "Check the OPENAI_API_KEY secret, that the OpenAI account has API credits, and that "
            "this model is available to the key (or set the OPENAI_MODEL repository variable).") from None
    except urllib.error.URLError as exc:
        raise BridgeError(f"Cannot reach the OpenAI API: {exc.reason}") from None


def ask_gpt(step: str, instructions: str, prompt: str) -> tuple[str, dict]:
    payload = {
        "model": CONFIG["openai_model"],
        "instructions": instructions,
        "input": prompt,
        "max_output_tokens": CONFIG["openai_max_output_tokens"],
        "store": False,
    }
    if CONFIG["openai_effort"] and CONFIG["openai_effort"] != "default":
        payload["reasoning"] = {"effort": CONFIG["openai_effort"]}
    body = json.dumps(payload).encode()

    data = None
    for attempt in range(3):  # 1 call + at most 2 retries on transient errors
        req = urllib.request.Request(
            f"{CONFIG['openai_base_url']}/responses", data=body, method="POST",
            headers={"Authorization": "Bearer " + os.environ["OPENAI_API_KEY"],
                     "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=600) as resp:
                data = json.load(resp)
            break
        except urllib.error.HTTPError as exc:
            message = openai_error_message(exc)
            if exc.code in (429, 500, 502, 503, 504) and attempt < 2:
                log(f"GPT {step}: transient error ({message}); retrying")
                time.sleep(20 * (attempt + 1))
                continue
            raise BridgeError(f"GPT {step} failed: {message}") from None
        except (urllib.error.URLError, TimeoutError) as exc:
            if attempt < 2:
                log(f"GPT {step}: network error ({exc}); retrying")
                time.sleep(20 * (attempt + 1))
                continue
            raise BridgeError(f"GPT {step} failed: network error {exc}") from None

    texts = [c.get("text", "")
             for item in data.get("output", []) if item.get("type") == "message"
             for c in item.get("content", []) if c.get("type") == "output_text"]
    text = "\n".join(texts).strip()
    usage = data.get("usage") or {}
    meta = {
        "model": data.get("model", CONFIG["openai_model"]),
        "status": data.get("status"),
        "input_tokens": usage.get("input_tokens"),
        "output_tokens": usage.get("output_tokens"),
        "reasoning_tokens": (usage.get("output_tokens_details") or {}).get("reasoning_tokens"),
    }
    if data.get("status") == "incomplete":
        reason = (data.get("incomplete_details") or {}).get("reason")
        if not text:
            raise BridgeError(f"GPT {step} returned no text (incomplete: {reason}). "
                              "Raise OPENAI_MAX_OUTPUT_TOKENS or lower OPENAI_REASONING_EFFORT.")
        text += f"\n\n[Response was cut off: {reason}]"
    if not text:
        raise BridgeError(f"GPT {step} returned no text (status={data.get('status')}).")
    log(f"GPT {step}: ok ({meta['input_tokens']} in / {meta['output_tokens']} out tokens)")
    return text, meta


# --------------------------------------------------------------- Claude Code

def claude_env() -> dict:
    child = {k: v for k, v in os.environ.items() if k not in STRIP_FROM_CLAUDE_ENV}
    child["DISABLE_AUTOUPDATER"] = "1"
    return child


def ask_claude(step: str, prompt: str, max_turns: int, budget_usd: float) -> tuple[str, dict]:
    cmd = ["claude", "--bare", "-p",
           "--output-format", "json",
           "--no-session-persistence",
           "--max-turns", str(max_turns),
           "--max-budget-usd", f"{budget_usd:.2f}",
           "--permission-mode", "dontAsk",
           "--allowedTools", "Bash,Read,Edit,Write,Glob,Grep",
           "--disallowedTools", "Bash(git push *)", "Bash(gh *)", "Bash(git remote *)"]
    if (ROOT / "AGENTS.md").is_file():
        cmd += ["--append-system-prompt-file", str(ROOT / "AGENTS.md")]
    if CONFIG["claude_model"]:
        cmd += ["--model", CONFIG["claude_model"]]

    log(f"Claude {step}: running (max {max_turns} turns, ${budget_usd:.2f} cap)")
    try:
        proc = subprocess.run(cmd, input=prompt, text=True, capture_output=True,
                              timeout=CONFIG["claude_timeout_s"], env=claude_env())
    except FileNotFoundError:
        raise BridgeError("Claude Code CLI ('claude') is not installed on this runner.") from None
    except subprocess.TimeoutExpired:
        raise BridgeError(f"Claude {step} exceeded {CONFIG['claude_timeout_s']}s.") from None

    try:
        out = proc.stdout.strip()
        try:
            data = json.loads(out)
        except json.JSONDecodeError:
            data = json.loads(out.splitlines()[-1])
        if not isinstance(data, dict):
            raise json.JSONDecodeError("not an object", out, 0)
    except (json.JSONDecodeError, IndexError):
        raise BridgeError(f"Claude {step} produced no JSON result (exit {proc.returncode}). "
                          f"stderr: {proc.stderr[-1500:]}") from None

    meta = {
        "model": next(iter(data.get("modelUsage") or {}), CONFIG["claude_model"] or "default"),
        "subtype": data.get("subtype"),
        "is_error": data.get("is_error"),
        "num_turns": data.get("num_turns"),
        "cost_usd": data.get("total_cost_usd"),
        "duration_s": round((data.get("duration_ms") or 0) / 1000),
    }
    result = (data.get("result") or "").strip()
    subtype = str(data.get("subtype") or "")
    hit_limit = "max_turns" in subtype or "budget" in subtype
    if data.get("is_error") or proc.returncode != 0:
        if hit_limit:
            log(f"Claude {step}: stopped at a limit ({subtype}); keeping partial work")
            result = (result + f"\n\n[Claude Code stopped early: {subtype}]").strip()
        else:
            reason = data.get("terminal_reason") or subtype or f"exit {proc.returncode}"
            raise BridgeError(f"Claude {step} failed ({reason}): "
                              f"{clip(result or proc.stderr, 1500)}")
    log(f"Claude {step}: done in {meta['num_turns']} turns, ~${meta['cost_usd']}")
    return result or "(Claude returned no summary.)", meta


# ----------------------------------------------------------------- git scope

def enforce_scope(base_sha: str) -> list[str]:
    """Fold any commits Claude made back into the worktree and undo out-of-scope edits."""
    if git("rev-parse", "HEAD") != base_sha:
        git("reset", "--soft", base_sha)
    git("reset", "-q")
    status = run("git", "status", "--porcelain=v1", "-z", "--untracked-files=all").stdout
    reverted = []
    for entry in filter(None, status.split("\0")):
        path = entry[3:]
        if not is_protected(path):
            continue
        if run("git", "cat-file", "-e", f"{base_sha}:{path}", check=False).returncode == 0:
            git("checkout", base_sha, "--", path)
        else:
            target = ROOT / path
            shutil.rmtree(target) if target.is_dir() else target.unlink(missing_ok=True)
        reverted.append(path)
    if reverted:
        log(f"Reverted out-of-scope changes: {', '.join(reverted)}")
    return reverted


def commit(message: str) -> bool:
    git("add", "-A")
    staged = [p for p in git("diff", "--cached", "--name-only").splitlines() if p]
    too_big = [p for p in staged if (ROOT / p).is_file() and (ROOT / p).stat().st_size > MAX_FILE_BYTES]
    for path in too_big:
        git("reset", "-q", "--", path)
        log(f"Skipped oversized file: {path}")
    if run("git", "diff", "--cached", "--quiet", check=False).returncode == 0:
        return False
    git("commit", "-q", "-m", message)
    return True


def diff_since(base_sha: str) -> tuple[str, str]:
    stat = git("diff", "--stat", base_sha, "HEAD")
    # Lock files are noise for a reviewer and can be huge.
    patch = git("diff", base_sha, "HEAD", "--", ".", ":(exclude)package-lock.json",
                ":(exclude)*.lock", ":(exclude)pnpm-lock.yaml")
    return stat, patch


# ------------------------------------------------------------------- prompts

GPT_PLANNER = """You are GPT, the technical lead in an automated two-agent workflow.
Claude Code (another AI agent with full repository access) will implement your plan
without being able to ask you questions. Write a concise, prioritized, concrete
implementation plan (at most ~700 words): files to create or change, key steps,
acceptance criteria, and the exact checks Claude should run. Stay strictly within the
task. No unrelated refactors or speculative features. Follow these repository rules:

{rules}"""

GPT_REVIEWER = """You are GPT, the code reviewer in an automated two-agent workflow.
Claude Code implemented a task from your plan. Review the actual diff and Claude's
report. Report at most 6 HIGH-IMPACT, actionable problems (bugs, broken or missing
acceptance criteria, failing checks, security issues, scope creep). Do not nitpick style.

The FIRST line of your reply must be exactly one of:
VERDICT: APPROVE
VERDICT: CHANGES_REQUESTED
Use CHANGES_REQUESTED only if Claude must change code before a human reviews the PR.
Then list each issue with file, problem and the concrete fix."""

CLAUDE_RULES = """Rules for this automated run:
- You were started by a GitHub Actions workflow. Nobody can answer questions; decide sensibly.
- Work only on the task. Do not edit .github/, scripts/ai_bridge.py, AGENTS.md or agent-runs/
  (edits there are reverted automatically). Never add secrets or credentials.
- Do NOT commit, push, or create branches/PRs - the workflow commits your working tree.
- Run the relevant checks (build/tests/lint) that exist or that you add.
- Finish with a short report in Markdown with exactly these headings:
  ## Changes  (files and what changed)
  ## Checks  (each command you ran and its result)
  ## Open issues  (anything incomplete or risky; "None" if none)"""


# ---------------------------------------------------------------------- main

def write_outputs(**values: str) -> None:
    out = os.environ.get("GITHUB_OUTPUT")
    if out:
        with open(out, "a", encoding="utf-8") as fh:
            for key, value in values.items():
                fh.write(f"{key}={value}\n")


def step_summary(text: str) -> None:
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if path:
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(text + "\n")


def render_transcript(record: dict) -> str:
    cfg = record["config"]
    md = [f"# Agent run {record['run']}", "", f"**Task:** {record['task']}", "",
          f"- Status: **{record.get('status', 'running')}**",
          f"- GPT model: `{cfg['openai_model']}` (reasoning effort: {cfg['openai_effort']})",
          f"- Claude Code model: `{cfg['claude_model'] or 'CLI default'}`",
          f"- GPT review verdict: **{record.get('verdict', 'n/a')}**",
          f"- Claude Code estimated cost: ${record.get('claude_cost_usd', 0):.2f}"
          f" · GPT tokens (in+out): {record.get('gpt_tokens', 0)}"]
    if record.get("error"):
        md += ["", f"**Error:** {record['error']}"]
    md += ["", "```", record.get("final_diff_stat") or "(no code changes)", "```", ""]
    for s in record["steps"]:
        md += [f"## {s['step']}: {s['from']} → {s['to']}", "",
               f"<sub>{json.dumps(s['meta'])}</sub>", "", s["content"], ""]
    return "\n".join(md)


def main(work: Path) -> int:
    task = os.environ.get("AI_TASK", "").strip()
    if not task or len(task) > CONFIG["max_task_chars"]:
        raise BridgeError(f"The task must contain 1-{CONFIG['max_task_chars']} characters.")
    for key in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY"):
        if not os.environ.get(key):
            raise BridgeError(f"Missing {key}. Add it under Settings > Secrets and variables > Actions.")

    run_id = env("GITHUB_RUN_ID", dt.datetime.now(dt.timezone.utc).strftime("local-%Y%m%d%H%M%S"))
    run_name = f"{dt.datetime.now(dt.timezone.utc):%Y-%m-%d}-run-{run_id}"
    base_sha = git("rev-parse", "HEAD")
    rules = (ROOT / "AGENTS.md").read_text(encoding="utf-8") if (ROOT / "AGENTS.md").is_file() else ""
    files = git("ls-files").splitlines()
    file_list = "\n".join(f for f in files if not f.startswith(REPORTS_DIR + "/"))[:8000] or "(empty repository)"

    record = {"run": run_name, "task": task, "base_sha": base_sha, "status": "running", "steps": [],
              "config": {k: v for k, v in CONFIG.items() if k != "openai_base_url"}}

    def save(step: str, sender: str, receiver: str, content: str, meta: dict) -> None:
        record["steps"].append({"step": step, "from": sender, "to": receiver, "meta": meta,
                                "at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                                "content": content})
        flush()

    def flush() -> None:
        steps = record["steps"]
        record["gpt_tokens"] = sum((s["meta"].get("input_tokens") or 0) + (s["meta"].get("output_tokens") or 0)
                                   for s in steps if s["from"] == "GPT")
        record["claude_cost_usd"] = round(sum((s["meta"].get("cost_usd") or 0)
                                              for s in steps if s["from"] == "Claude Code"), 4)
        record["final_diff_stat"] = git("diff", "--stat", base_sha, "HEAD", check=False)
        (work / "run.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
        (work / "transcript.md").write_text(render_transcript(record), encoding="utf-8")

    try:
        check_openai_model()

        # 1. GPT plans
        plan, meta = ask_gpt("plan", GPT_PLANNER.format(rules=rules),
                             f"TASK:\n{task}\n\nTRACKED FILES:\n{file_list}")
        save("1-plan", "GPT", "Claude Code", plan, meta)

        # 2. Claude implements
        report, meta = ask_claude(
            "implementation",
            f"{CLAUDE_RULES}\n\nUSER TASK:\n{task}\n\nIMPLEMENTATION PLAN FROM GPT:\n{plan}\n",
            CONFIG["claude_max_turns"], CONFIG["claude_budget_usd"])
        meta["reverted_paths"] = enforce_scope(base_sha)
        meta["committed"] = commit("Claude Code: implement task (planned by GPT)\n\n" + clip(task, 500))
        save("2-implementation", "Claude Code", "GPT", report, meta)

        # 3. GPT reviews the real diff plus Claude's report
        stat, patch = diff_since(base_sha)
        review, meta = ask_gpt(
            "review", GPT_REVIEWER,
            f"TASK:\n{task}\n\nYOUR PLAN:\n{plan}\n\nCLAUDE'S REPORT:\n{report}\n\n"
            f"DIFF STAT:\n{stat or '(no changes)'}\n\n"
            f"DIFF:\n{clip(patch, CONFIG['max_diff_chars']) or '(no changes)'}")
        found = re.search(r"VERDICT:\W*(APPROVE|CHANGES_REQUESTED)", review[:400].upper())
        # Anything unclear is treated as "changes requested" (costs at most one bounded pass).
        verdict = "approve" if found and found.group(1) == "APPROVE" else "changes_requested"
        meta["verdict"] = record["verdict"] = verdict
        save("3-review", "GPT", "Claude Code", review, meta)

        # 4. Claude addresses the review: one bounded pass, only when needed
        if verdict == "changes_requested":
            head_before_fix = git("rev-parse", "HEAD")
            fix_report, meta = ask_claude(
                "review fixes",
                f"{CLAUDE_RULES}\n\nUSER TASK:\n{task}\n\nGPT reviewed your implementation. "
                "Fix the genuine high-impact issues below and briefly explain any you disagree with.\n\n"
                f"GPT REVIEW:\n{review}\n",
                max(10, CONFIG["claude_max_turns"] // 2), CONFIG["claude_budget_usd"] / 2)
            meta["reverted_paths"] = enforce_scope(head_before_fix)
            meta["committed"] = commit("Claude Code: address GPT review")
            save("4-fixes", "Claude Code", "GPT", fix_report, meta)
        else:
            log("GPT approved; no correction pass needed")
        record["status"] = "completed"
    except BridgeError as exc:
        record["status"], record["error"] = "failed", str(exc)
        raise
    finally:
        record["finished_at"] = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
        flush()

    # 5. Commit the shared record and prepare the PR text
    run_dir = ROOT / REPORTS_DIR / run_name
    run_dir.mkdir(parents=True, exist_ok=True)
    for name in ("transcript.md", "run.json"):
        shutil.copy(work / name, run_dir / name)
    commit(f"Agent run record: {run_name}")

    last_claude = [s["content"] for s in record["steps"] if s["from"] == "Claude Code"][-1]
    fixed = " - Claude Code applied one correction pass" if verdict == "changes_requested" else ""
    body = "\n".join([
        f"Automated GPT + Claude Code run (workflow run {run_id}).", "",
        f"**Task:** {clip(task, 1500)}", "",
        f"**GPT review verdict:** `{verdict}`{fixed}", "",
        f"Full exchange between the agents: `{REPORTS_DIR}/{run_name}/transcript.md`", "",
        "```", record["final_diff_stat"] or "(no code changes)", "```", "",
        "<details><summary>GPT review</summary>", "", clip(review, 5000), "", "</details>", "",
        "### Claude Code's final report", "", clip(last_claude, 5000), "",
        "---", "Nothing was merged automatically. Review and test before merging.",
    ])
    (work / "pr-title.txt").write_text("AI collab: " + re.sub(r"\s+", " ", task)[:70], encoding="utf-8")
    (work / "pr-body.md").write_text(body, encoding="utf-8")
    write_outputs(run_name=run_name)
    step_summary(f"### GPT + Claude Code run\n\nVerdict: **{verdict}**\n\n"
                 f"```\n{record['final_diff_stat']}\n```\n"
                 f"Transcript: `{REPORTS_DIR}/{run_name}/transcript.md`")
    log("Collaboration finished; ready to open the pull request")
    return 0


if __name__ == "__main__":
    work_dir = Path(env("AGENT_WORK_DIR") or tempfile.mkdtemp(prefix="agent-run-"))
    work_dir.mkdir(parents=True, exist_ok=True)
    try:
        sys.exit(main(work_dir))
    except BridgeError as exc:
        print(f"::error title=AI bridge::{exc}", flush=True)
        step_summary(f"### AI bridge failed\n\n{exc}\n\nThe partial transcript is attached to this "
                     "workflow run as the `agent-run` artifact.")
        sys.exit(1)
