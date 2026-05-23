from pydantic_ai.usage import RunUsage

from agent_eval_matrix.run_metrics import tokens_spent, tool_failures, turns


def test_tokens_spent() -> None:
    usage = RunUsage(input_tokens=4430, output_tokens=359, cache_read_tokens=3328)
    assert tokens_spent(usage) == 8117


def test_turns() -> None:
    usage = RunUsage(requests=6)
    assert turns(usage) == 6


def test_tool_failures() -> None:
    metrics = {
        "str_replace_failures": 1,
        "hashline_edit_failures": 2,
        "tool_calls": 5,
    }
    assert tool_failures(metrics) == 3
