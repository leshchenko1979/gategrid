from __future__ import annotations

from pydantic_ai import Agent

from agent_eval_matrix.config import get_model
from agent_eval_matrix.models import ExperimentVariant, FileEditDeps


def build_agent(variant: ExperimentVariant) -> Agent[FileEditDeps]:
    model = get_model(variant.model_id)
    return Agent(
        model,
        system_prompt=variant.system_prompt,
        deps_type=FileEditDeps,
        tools=variant.tools,
    )
