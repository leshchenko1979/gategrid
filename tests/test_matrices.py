from pathlib import Path

import pytest
from pydantic import ValidationError

from harness.matrices import resolve_matrix
from harness.models import MatrixConfig

ROOT = Path(__file__).resolve().parents[1]
EXPERIMENTS = ROOT / "experiments"
CASES = EXPERIMENTS / "cases"


def test_resolve_matrix_ci() -> None:
    resolved = resolve_matrix(EXPERIMENTS / "matrices" / "ci.yaml", EXPERIMENTS, CASES)
    assert resolved.matrix_name == "ci"
    assert len(resolved.variants) == 1
    assert resolved.variants[0].tooling_name == "baseline"
    assert len(resolved.cases) == 2
    assert resolved.variants[0].variant_id == "baseline/minimax-m2.7"
    assert len(resolved.variants[0].tools) == 5


def test_resolve_matrix_full() -> None:
    resolved = resolve_matrix(
        EXPERIMENTS / "matrices" / "full.yaml", EXPERIMENTS, CASES
    )
    assert resolved.matrix_name == "full"
    assert len(resolved.variants) == 4
    assert len(resolved.cases) == 5
    assert len(resolved.variants) * len(resolved.cases) == 20


def test_resolve_matrix_hashline_hypotheses() -> None:
    resolved = resolve_matrix(
        EXPERIMENTS / "matrices" / "hashline_hypotheses.yaml", EXPERIMENTS, CASES
    )
    assert resolved.matrix_name == "hashline_hypotheses"
    assert len(resolved.variants) == 5
    assert len(resolved.cases) == 10
    assert len(resolved.variants) * len(resolved.cases) == 50
    toolings = {v.tooling_name for v in resolved.variants}
    assert toolings == {
        "opencrabs_original",
        "opencrabs_h1_docs",
        "opencrabs_h3_collision",
        "opencrabs_h2_fuzzy",
        "baseline",
    }


def test_matrix_requires_cases() -> None:
    with pytest.raises(ValidationError):
        MatrixConfig.model_validate(
            {
                "tool_sets": ["baseline"],
                "models": ["minimax-m2.7"],
                "cases": [],
                "case_sets": [],
            }
        )
