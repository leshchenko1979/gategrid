from __future__ import annotations

from pydantic_ai import RunContext

from agent_eval_matrix import tools
from agent_eval_matrix.models import FileEditDeps


def ls(ctx: RunContext[FileEditDeps], path: str = ".") -> list[str]:
    """List files and directories at a workspace-relative path."""
    return tools.ls(ctx, path)
