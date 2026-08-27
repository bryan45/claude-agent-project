# claude-agent-project

Small starter project for [`claude-agent-sdk`](https://pypi.org/project/claude-agent-sdk/), the Python packaging of Claude Code as a library.

## Contents

- **`test_query.py`** — minimal smoke test for the SDK's `query()` function: sends a one-off prompt and prints the reply.
- **`multi_agent_starter.py`** — a two-step pipeline example. `call_researcher()` calls the Anthropic API directly with structured outputs (`client.messages.parse(..., output_format=ResearcherOutput)`) to gather evidence for the question, then the result is handed to a `synthesizer` step run through `claude-agent-sdk` to compose the final answer.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install claude-agent-sdk anthropic
```

The SDK shells out to the `claude` CLI (`@anthropic-ai/claude-code` on npm) as its transport, so that must be installed and on `PATH` (`npm install -g @anthropic-ai/claude-code`).

## Authentication

Either of the following works — the SDK/CLI picks up whichever is available:

- **Interactive / local dev:** `claude login` (or `claude auth status` to check) authenticates via your claude.ai account. No `ANTHROPIC_API_KEY` needed.
- **Scripted / non-interactive:** set `ANTHROPIC_API_KEY` in the environment before running.

**Note:** `call_researcher()` in `multi_agent_starter.py` uses the raw `anthropic` SDK client directly, which does **not** share `claude login`'s credential store. It needs `ANTHROPIC_API_KEY` set, or `ant auth login` run separately, even if `claude login` is already configured for the Agent SDK's synthesizer step.

## Usage

```powershell
.\.venv\Scripts\Activate.ps1
python test_query.py
python multi_agent_starter.py
```

## Deployment

This project is a local starter, not a deployed service — there's no server, container, or CI config here. If you take it further:

- **Credentials:** don't rely on `claude login`'s stored session in a deployed environment. Set `ANTHROPIC_API_KEY` as a secret/environment variable on whatever runs the code (CI job, container, scheduled task).
- **Runtime dependency:** the `claude` CLI must be present in that environment too (it's what the SDK actually invokes) — install it via npm as part of your build/image step, not just locally.
- **Don't commit `.venv`** — it's excluded via `.gitignore`; rebuild it from `pip install claude-agent-sdk` on the target machine instead.
- **Cost:** every `query()` call is a billed API call (see the `--- done in ...ms, cost $...` line each script prints) — factor that into any scheduled or automated deployment.
