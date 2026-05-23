from __future__ import annotations

from pydantic_ai import RunContext

from agent_eval_matrix import tools
from agent_eval_matrix.models import FileEditDeps


def str_replace_strict(
    ctx: RunContext[FileEditDeps], file_path: str, old_str: str, new_str: str
) -> str:
    """Replace exactly ONE literal occurrence of old_str with new_str (byte-for-byte match)."""
    return tools.str_replace(ctx, file_path, old_str, new_str, strict_messages=True)
