"""Quick smoke test for the Claude Agent SDK's query() function."""

import anyio

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
    TextBlock,
    query,
)


async def main() -> None:
    options = ClaudeAgentOptions(
        system_prompt="You are a concise assistant. Answer in one sentence.",
        cwd=".",
        max_turns=1,
    )

    async for message in query(prompt="What is 2 + 2?", options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print("Claude:", block.text)
        elif isinstance(message, ResultMessage):
            print(f"--- done in {message.duration_ms}ms, cost ${message.total_cost_usd}")


if __name__ == "__main__":
    anyio.run(main)
