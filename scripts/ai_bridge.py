#!/usr/bin/env python3
"""Bounded OpenAI planner/reviewer + Claude Code implementation bridge."""
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

TASK = os.environ["GAME_TASK"].strip()
MODEL = os.getenv("OPENAI_MODEL", "gpt-6.1-sol")
if not TASK or len(TASK) > 4000:
    sys.exit("GAME_TASK must contain 1–4000 characters")

def command(*args, input_text=None, timeout=1800, check=True):
    result = subprocess.run(args, input=input_text, text=True, capture_output=True, timeout=timeout)
    if check and result.returncode:
        print(result.stdout[-5000:], result.stderr[-5000:], file=sys.stderr)
        raise RuntimeError(f"Command failed: {args[0]} ({result.returncode})")
    return result.stdout.strip()

def openai(prompt, max_output_tokens=3000):
    payload = json.dumps({
        "model": MODEL, "input": prompt,
        "max_output_tokens": max_output_tokens
    }).encode()
    request = urllib.request.Request(
        "https://api.openai.com/v1/responses",
        data=payload,
        headers={"Authorization": "Bearer " + os.environ["OPENAI_API_KEY"],
                 "Content-Type": "application/json"},
        method="POST")
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            data = json.load(response)
    except urllib.error.HTTPError as exc:
        # Do not print headers, API keys, or full request payload.
        raise RuntimeError(f"OpenAI API error: HTTP {exc.code}") from None
    parts = []
    for item in data.get("output", []):
        for content in item.get("content", []):
            if content.get("type") == "output_text":
                parts.append(content.get("text", ""))
    result = "\n".join(parts).strip()
    if not result:
        raise RuntimeError("OpenAI provided no text response; inspect model and API limits.")
    return result

def claude(instructions, max_turns):
    # This runs ONLY on manually triggered trusted-repo GitHub runners.
    # The CLI needs edit and test permissions to implement a task.
    print("Claude Code implementation pass...", flush=True)
    output = command("claude", "-p", "--permission-mode", "bypassPermissions",
                     "--max-turns", str(max_turns), input_text=instructions,
                     timeout=2700)
    print(output[-3500:])

def commit_if_changed(message):
    command("git", "add", "-A")
    changed = subprocess.run(["git", "diff", "--cached", "--quiet"]).returncode != 0
    if changed:
        command("git", "commit", "-m", message)
    return changed

def main():
    Path("agent-reports").mkdir(exist_ok=True)
    files = command("git", "ls-files").splitlines()
    tracked = "\n".join(files[:160])
    plan = openai(f"""You are the technical director of a high-quality browser game.
Use AGENTS.md's principles. Give Claude Code a prioritized concrete plan of <= 900 words.
Avoid unrelated refactors, excessive abstraction or scope creep.
Task:\n{TASK}\nTracked files:\n{tracked}""")
    Path("agent-reports/plan.md").write_text("# GPT implementation plan\n\n" + plan + "\n")
    claude(f"""Implement this task within the existing repository.
Read AGENTS.md first. Work strictly within scope. Do not edit .github, scripts/ai_bridge.py,
agent-reports, or credentials. Make the game launchable and run available tests/build.
USER TASK:\n{TASK}\n\nGPT PLAN:\n{plan}
""", 32)
    commit_if_changed("Claude: first implementation pass")
    diff = command("git", "diff", "origin/main...HEAD", "--", ".", ":!.github",
                   ":!scripts/ai_bridge.py", ":!agent-reports", timeout=60)
    review = openai(f"""Review this browser game code change as a senior engineer.
Identify up to 6 HIGH IMPACT actionable defects, not style preferences.
If the diff is too large, prioritize the most severe problems.
If it is good, explicitly say 'No critical issues found'.
USER TASK:\n{TASK}\n\nDIFF (truncated):\n{diff[:70000]}""")
    Path("agent-reports/review.md").write_text("# GPT code review\n\n" + review + "\n")
    if "No critical issues found" not in review:
        claude(f"""Address only the genuine high-impact issues in the following review.
Read AGENTS.md. Do not edit .github, scripts/ai_bridge.py, agent-reports, or credentials.
Run build/tests. Do not introduce unrelated features.
TASK:\n{TASK}\nREVIEW:\n{review}""", 16)
    commit_if_changed("Claude: apply GPT review and save reports")
    print("Two-pass collaboration completed; ready to open PR.")

if __name__ == "__main__":
    main()
