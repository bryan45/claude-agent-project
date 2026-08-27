"""Mocked tests for call_researcher(): structured-output validation and
rate-limit fallback. No real API calls -- messages.parse is patched."""

import sys
from unittest.mock import MagicMock, patch

import httpx2

import multi_agent_starter as mas
from multi_agent_starter import Citation, ResearcherOutput, call_researcher

QUERIES = [f"What does module {i} of this project do?" for i in range(20)]


def _fake_parse_response(parsed_output: ResearcherOutput) -> MagicMock:
    response = MagicMock()
    response.parsed_output = parsed_output
    return response


def _fake_rate_limit_error() -> mas.anthropic.RateLimitError:
    request = httpx2.Request("POST", "https://api.anthropic.com/v1/messages")
    response = httpx2.Response(429, request=request)
    return mas.anthropic.RateLimitError(
        "Rate limited (simulated)",
        response=response,
        body={"error": {"type": "rate_limit_error", "message": "simulated"}},
    )


def test_twenty_trials_validate() -> bool:
    all_ok = True
    for i, question in enumerate(QUERIES):
        expected = ResearcherOutput(
            citations=(
                [Citation(file=f"file_{i}.py", snippet=f"snippet {i}", line_start=i, line_end=i + 5)]
                if i % 4 != 0
                else []
            ),
            confidence=["low", "medium", "high"][i % 3],
            refusal_reason="no relevant evidence found" if i % 4 == 0 else None,
        )
        with patch.object(mas._anthropic_client.messages, "parse", return_value=_fake_parse_response(expected)):
            result = call_researcher(question)
        ok = isinstance(result, ResearcherOutput) and result == expected
        status = "OK" if ok else "FAIL"
        print(f"[{i + 1:2d}/20] {status}: confidence={result.confidence!r} citations={len(result.citations)}")
        all_ok = all_ok and ok
    return all_ok


def test_rate_limit_fallback() -> bool:
    success = ResearcherOutput(citations=[], confidence="low", refusal_reason=None)
    side_effects = [_fake_rate_limit_error(), _fake_parse_response(success)]

    def fake_parse(*args, **kwargs):
        effect = side_effects.pop(0)
        if isinstance(effect, Exception):
            raise effect
        return effect

    with (
        patch.object(mas._anthropic_client.messages, "parse", side_effect=fake_parse),
        patch.object(mas.time, "sleep", return_value=None),
    ):
        result = call_researcher("trigger a rate limit")

    ok = isinstance(result, ResearcherOutput) and result == success
    print(f"Rate-limit fallback: {'OK' if ok else 'FAIL'} (retried after simulated RateLimitError, got {result!r})")
    return ok


if __name__ == "__main__":
    trials_ok = test_twenty_trials_validate()
    fallback_ok = test_rate_limit_fallback()

    print()
    print(f"20-trial validation: {'PASS' if trials_ok else 'FAIL'}")
    print(f"Rate-limit fallback: {'PASS' if fallback_ok else 'FAIL'}")

    sys.exit(0 if (trials_ok and fallback_ok) else 1)
