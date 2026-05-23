from __future__ import annotations

from pathlib import Path

import yaml

from agent_eval_matrix.models import EditCase


def load_cases_by_names(cases_path: Path, names: list[str]) -> list[EditCase]:
    all_cases = load_cases(cases_path)
    by_name = {c.name: c for c in all_cases}
    missing = [n for n in names if n not in by_name]
    if missing:
        raise ValueError(f"Unknown case names: {missing}")
    return [by_name[n] for n in names]


def load_cases(cases_path: Path) -> list[EditCase]:
    if cases_path.is_file():
        return [_load_case_file(cases_path)]

    cases: list[EditCase] = []
    for path in sorted(cases_path.glob("*.yaml")):
        cases.append(_load_case_file(path))
    if not cases:
        raise FileNotFoundError(f"No case YAML files in {cases_path}")
    return cases


def _load_case_file(path: Path) -> EditCase:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Case file {path} must be a YAML mapping")
    name = data.get("name") or path.stem
    return EditCase(
        name=name,
        instruction=str(data["instruction"]),
        file_name=str(data["file_name"]),
        initial_content=str(data["initial_content"]),
        expected_output=str(data["expected_output"]),
        tags=list(data.get("tags") or []),
    )
