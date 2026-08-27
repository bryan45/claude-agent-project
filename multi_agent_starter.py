"""Starter for a researcher -> synthesizer pipeline: direct Anthropic API for
research, Claude Agent SDK for synthesis."""

import asyncio
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")

import anthropic
from pydantic import BaseModel
from typing import Literal

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
    TextBlock,
    query,
)


class Citation(BaseModel):
    file: str
    snippet: str
    line_start: int
    line_end: int


class ResearcherOutput(BaseModel):
    citations: list[Citation]
    confidence: Literal["low", "medium", "high"]
    refusal_reason: str | None = None

RESEARCHER_PROMPT = """
Find evidence in the project files relevant to the user's question.
Return a JSON object with a "citations" array of {file, snippet, line_start, line_end}
and a "confidence" field of "low", "medium", or "high".
If you cannot find relevant evidence, return citations: [] and confidence: "low".
"""

SYNTHESIZER_PROMPT = """
Compose a final answer that cites only the material the researcher returned.
"""

SYNTHESIZER_OPTIONS = ClaudeAgentOptions(
    system_prompt=SYNTHESIZER_PROMPT,
    cwd=".",
    max_turns=6,
)

_anthropic_client = anthropic.Anthropic()


def call_researcher(user_query: str, max_retries: int = 3) -> ResearcherOutput:
    delay = 1.0
    for attempt in range(max_retries):
        try:
            response = _anthropic_client.messages.parse(
                model="claude-opus-5",
                max_tokens=2048,
                system=RESEARCHER_PROMPT,
                messages=[{"role": "user", "content": user_query}],
                output_format=ResearcherOutput,
            )
            return response.parsed_output
        except anthropic.RateLimitError:
            if attempt == max_retries - 1:
                raise
            time.sleep(delay)
            delay *= 2
    raise AssertionError("unreachable")


async def main() -> None:
    question = "What does this project do?"

    researcher_output = call_researcher(question)
    print(
        f"--- researcher confidence: {researcher_output.confidence}, "
        f"citations: {len(researcher_output.citations)}"
    )

    synthesizer_prompt = (
        f"User question: {question}\n\n"
        f"Researcher findings (JSON):\n{researcher_output.model_dump_json()}"
    )

    last_result: ResultMessage | None = None
    async for message in query(prompt=synthesizer_prompt, options=SYNTHESIZER_OPTIONS):
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
