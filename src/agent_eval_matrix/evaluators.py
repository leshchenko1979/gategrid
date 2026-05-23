from __future__ import annotations

from dataclasses import dataclass

from pydantic_evals.evaluators import Evaluator, EvaluatorContext


def _normalize(text: str) -> str:
    return text.replace("\r\n", "\n").strip()


@dataclass
class FileContentMatch(Evaluator):
    """Score 1.0 when final file content matches expected_output."""

    def evaluate(self, ctx: EvaluatorContext) -> float:
        if ctx.expected_output is None:
            return 0.0
        actual = _normalize(str(ctx.output))
        expected = _normalize(str(ctx.expected_output))
        return 1.0 if actual == expected else 0.0


@dataclass
class ToolUsageEvaluator(Evaluator):
    """When case is tagged needs_search, require grep before a successful edit."""

    def evaluate(self, ctx: EvaluatorContext) -> dict[str, bool | float]:
        tags: list[str] = []
        if hasattr(ctx.inputs, "tags"):
            tags = list(ctx.inputs.tags)
        elif ctx.metadata and isinstance(ctx.metadata, dict):
            tags = list(ctx.metadata.get("tags") or [])
        needs_search = "needs_search" in tags
        used_grep = bool(ctx.attributes.get("used_grep"))
        str_replace_ok = bool(ctx.attributes.get("str_replace_succeeded"))
        return {
            "used_grep_when_needed": (not needs_search) or used_grep,
            "edit_attempted": str_replace_ok
            or ctx.metrics.get("str_replace_calls", 0) > 0,
        }


@dataclass
class EfficiencyEvaluator(Evaluator):
    max_tool_calls: int = 15
    max_str_replace_failures: int = 3
    max_bytes_read: int = 50_000

    def evaluate(self, ctx: EvaluatorContext) -> dict[str, bool | int | float]:
        tool_calls = int(ctx.metrics.get("tool_calls", 0))
        failures = int(ctx.metrics.get("str_replace_failures", 0))
        bytes_read = int(ctx.metrics.get("bytes_read", 0))
        return {
            "within_tool_budget": tool_calls <= self.max_tool_calls,
            "low_replace_failures": failures <= self.max_str_replace_failures,
            "reasonable_read_size": bytes_read <= self.max_bytes_read,
            "tool_call_count": tool_calls,
            "str_replace_failures": failures,
            "bytes_read": bytes_read,
        }
