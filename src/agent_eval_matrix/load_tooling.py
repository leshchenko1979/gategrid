from __future__ import annotations

import importlib.util
import sys
from collections.abc import Callable
from pathlib import Path
from types import ModuleType


def resolve_experiments_path(entry: str, experiments_dir: Path) -> Path:
    path = Path(entry)
    if not path.is_absolute():
        path = experiments_dir / path
    path = path.resolve()
    if path.suffix != ".py" or not path.is_file():
        raise ValueError(
            f"Tool entry {entry!r} must resolve to an existing .py file, got {path}"
        )
    return path


def _ensure_tooling_import_paths(tool_path: Path) -> None:
    tooling_dir = tool_path.parent
    if tooling_dir.name == "opencrabs":
        tooling_dir = tooling_dir.parent
    if str(tooling_dir) not in sys.path:
        sys.path.insert(0, str(tooling_dir))


def _module_import_name(path: Path) -> str:
    return "agent_eval_matrix_tool_" + "_".join(path.with_suffix("").parts[-3:])


def load_tool_function(path: Path) -> Callable:
    """Load a single-tool module; exported callable name matches file stem."""
    _ensure_tooling_import_paths(path)
    name = _module_import_name(path)
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load tool module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    tool_name = path.stem
    fn = getattr(module, tool_name, None)
    if fn is None or not callable(fn):
        raise AttributeError(f"{path}: expected callable {tool_name!r}")
    return fn


def load_tool_functions(entries: list[str], experiments_dir: Path) -> tuple:
    return tuple(
        load_tool_function(resolve_experiments_path(entry, experiments_dir))
        for entry in entries
    )
