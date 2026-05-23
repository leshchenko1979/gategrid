from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from pydantic_ai.usage import RunUsage


def tokens_spent(usage: RunUsage) -> int:
    return int(
        usage.input_tokens
        + usage.output_tokens
        + usage.cache_read_tokens
        + usage.cache_write_tokens
        + usage.input_audio_tokens
        + usage.cache_audio_read_tokens
        + usage.output_audio_tokens
        + sum(v for v in usage.details.values() if isinstance(v, (int, float)))
    )


def turns(usage: RunUsage) -> int:
    return usage.requests


def tool_failures(metrics: Mapping[str, Any]) -> int:
    return sum(int(v) for k, v in metrics.items() if k.endswith("_failures"))
