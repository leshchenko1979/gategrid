from __future__ import annotations

from pydantic_ai import RunContext

from agent_eval_matrix import tools
from agent_eval_matrix.models import FileEditDeps


def read_file(ctx: RunContext[FileEditDeps], file_path: str) -> str:
    """Read the full contents of a file (workspace-relative path)."""
    return tools.read_file(ctx, file_path)
