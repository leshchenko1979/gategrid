"""Shared helpers for OpenCrabs tooling modules."""

from __future__ import annotations

from pathlib import Path

from pydantic_ai import RunContext
from pydantic_evals import increment_eval_metric, set_eval_attribute

from agent_eval_matrix.models import FileEditDeps
from agent_eval_matrix.sandbox import SandboxError, resolve_workspace_path


def bump_tool(name: str) -> None:
    increment_eval_metric("tool_calls", 1)
    set_eval_attribute("last_tool", name)


def resolve(ctx: RunContext[FileEditDeps], user_path: str) -> Path | str:
    try:
        return resolve_workspace_path(ctx.deps.workspace, user_path)
    except SandboxError as exc:
        return str(exc)


def build_edit_diff(old: str, new: str, max_diff_lines: int = 40) -> str:
    """Compact diff from opencrabs edit.rs build_edit_diff."""
    old_lines = old.splitlines()
    new_lines = new.splitlines()
    diff: list[str] = []
    diff_lines = 0
    i = j = 0
    while i < len(old_lines) or j < len(new_lines):
        if diff_lines >= max_diff_lines:
            diff.append("... (diff truncated)\n")
            break
        if i < len(old_lines) and j < len(new_lines) and old_lines[i] == new_lines[j]:
            i += 1
            j += 1
            continue
        new_ahead = None
        if i < len(old_lines):
            for k, nl in enumerate(new_lines[j:], start=j):
                if nl == old_lines[i]:
                    new_ahead = k - j
                    break
        old_ahead = None
        if j < len(new_lines):
            for k, ol in enumerate(old_lines[i:], start=i):
                if ol == new_lines[j]:
                    old_ahead = k - i
                    break
        if new_ahead is not None and old_ahead is not None:
            if new_ahead <= old_ahead:
                for line in new_lines[j : j + new_ahead]:
                    diff.append(f"+ {line}\n")
                    diff_lines += 1
                j += new_ahead
            else:
                for line in old_lines[i : i + old_ahead]:
                    diff.append(f"- {line}\n")
                    diff_lines += 1
                i += old_ahead
        elif new_ahead is not None:
            for line in new_lines[j : j + new_ahead]:
                diff.append(f"+ {line}\n")
                diff_lines += 1
            j += new_ahead
        elif old_ahead is not None:
            for line in old_lines[i : i + old_ahead]:
                diff.append(f"- {line}\n")
                diff_lines += 1
            i += old_ahead
        else:
            if i < len(old_lines):
                diff.append(f"- {old_lines[i]}\n")
                diff_lines += 1
                i += 1
            if diff_lines < max_diff_lines and j < len(new_lines):
                diff.append(f"+ {new_lines[j]}\n")
                diff_lines += 1
                j += 1
    return "".join(diff)
