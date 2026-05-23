from __future__ import annotations

from pydantic_ai import RunContext

from agent_eval_matrix import tools
from agent_eval_matrix.models import FileEditDeps


def str_replace_fuzzy(
    ctx: RunContext[FileEditDeps], file_path: str, old_str: str, new_str: str
) -> str:
    """Replace exactly one occurrence of old_str with new_str using fuzzy line matching."""
    return tools.str_replace_fuzzy(ctx, file_path, old_str, new_str)
