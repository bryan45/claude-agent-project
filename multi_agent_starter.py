"""Starter for a two-agent researcher -> synthesizer pipeline using the Claude Agent SDK."""

import asyncio
import sys

sys.stdout.reconfigure(encoding="utf-8")

from claude_agent_sdk import (
    AgentDefinition,
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
    TextBlock,
    query,
)

RESEARCHER_PROMPT = """
Find evidence in the project files relevant to the user's question.
Return a JSON object with a "citations" array of {file, snippet, line_start, line_end}
and a "confidence" field of "low", "medium", or "high".
If you cannot find relevant evidence, return citations: [] and confidence: "low".
"""

SYNTHESIZER_PROMPT = """
Compose a final answer that cites only the material the researcher returned.
"""

ORCHESTRATOR_PROMPT = """
You have two subagents available via the Agent tool: "researcher" and "synthesizer".
For every user question:
1. Call "researcher" with the user's question to gather evidence.
2. Call "synthesizer", passing it the researcher's JSON output verbatim, to compose the final answer.
3. Return the synthesizer's answer to the user as your final response.
Do not answer from your own knowledge without going through this pipeline.
"""

OPTIONS = ClaudeAgentOptions(
    system_prompt=ORCHESTRATOR_PROMPT,
    cwd=".",
    max_turns=6,
    agents={
        "researcher": AgentDefinition(
            description=(
                "Searches project files for evidence relevant to a question "
                "and returns structured citations."
            ),
            prompt=RESEARCHER_PROMPT,
            tools=["Read", "Grep", "Glob"],
        ),
        "synthesizer": AgentDefinition(
            description="Writes the final answer using only the researcher's cited evidence.",
            prompt=SYNTHESIZER_PROMPT,
            tools=[],
        ),
    },
)


async def main() -> None:
    question = "What does this project do?"

    last_result: ResultMessage | None = None
    async for message in query(prompt=question, options=OPTIONS):
        if isinstance(message, AssistantMessage) and message.parent_tool_use_id is None:
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(block.text)
        elif isinstance(message, ResultMessage):
            last_result = message

    if last_result is not None:
        print(f"--- done in {last_result.duration_ms}ms, cost ${last_result.total_cost_usd}")


if __name__ == "__main__":
    asyncio.run(main())
