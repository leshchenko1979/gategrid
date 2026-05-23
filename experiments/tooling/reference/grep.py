from __future__ import annotations

from pydantic_ai import RunContext

from agent_eval_matrix import tools
from agent_eval_matrix.models import FileEditDeps


def grep(ctx: RunContext[FileEditDeps], pattern: str, file_path: str) -> list[str]:
    """Search for a substring in a file; returns matching lines with line numbers."""
    return tools.grep(ctx, pattern, file_path)
