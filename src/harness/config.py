from __future__ import annotations

import os
from pathlib import Path

from pydantic_ai.models import Model

from harness.models import ModelPreset

ROOT = Path(__file__).resolve().parents[2]
EXPERIMENTS = ROOT / "experiments"

_model_registry: dict[str, ModelPreset] | None = None


def _env_prefix(api_key_env: str) -> str:
    if api_key_env.endswith("_API_KEY"):
        return api_key_env[: -len("_API_KEY")]
    return api_key_env.rsplit("_", 1)[0]


def _get_model_registry() -> dict[str, ModelPreset]:
    global _model_registry
    if _model_registry is None:
        from harness.matrices import build_model_registry

        _model_registry = build_model_registry(EXPERIMENTS)
    return _model_registry


def resolve_model_name(preset: ModelPreset) -> str:
    prefix = _env_prefix(preset.api_key_env)
    return os.getenv(f"{prefix}_MODEL", preset.model_name)


def resolve_base_url(preset: ModelPreset) -> str | None:
    prefix = _env_prefix(preset.api_key_env)
    override = os.getenv(f"{prefix}_BASE_URL")
    if override:
        return override.rstrip("/")
    if preset.base_url:
        return preset.base_url.rstrip("/")
    return None


def get_model(model_id: str) -> Model:
    registry = _get_model_registry()
    preset = registry.get(model_id)
    if preset is None:
        raise ValueError(f"Unknown model_id {model_id!r}. Known: {sorted(registry)}")

    api_key = os.environ.get(preset.api_key_env)
    if not api_key:
        raise ValueError(
            f"Missing API key env var {preset.api_key_env!r} for model {model_id!r}"
        )

    model_name = resolve_model_name(preset)

    if preset.provider == "openai":
        from pydantic_ai.models.openai import OpenAIChatModel
        from pydantic_ai.providers.openai import OpenAIProvider

        base_url = resolve_base_url(preset)
        if not base_url:
            raise ValueError(
                f"openai provider requires base_url for model {model_id!r}"
            )
        return OpenAIChatModel(
            model_name,
            provider=OpenAIProvider(base_url=base_url, api_key=api_key),
        )

    if preset.provider == "anthropic":
        from pydantic_ai.models.anthropic import AnthropicModel
        from pydantic_ai.providers.anthropic import AnthropicProvider

        base_url = resolve_base_url(preset)
        provider_kwargs: dict[str, str] = {"api_key": api_key}
        if base_url:
            provider_kwargs["base_url"] = base_url
        return AnthropicModel(
            model_name,
            provider=AnthropicProvider(**provider_kwargs),
        )

    if preset.provider == "google":
        from pydantic_ai.models.google import GoogleModel
        from pydantic_ai.providers.google import GoogleProvider

        base_url = resolve_base_url(preset)
        provider_kwargs = {"api_key": api_key}
        if base_url:
            provider_kwargs["base_url"] = base_url
        return GoogleModel(
            model_name,
            provider=GoogleProvider(**provider_kwargs),
        )

    raise ValueError(f"Unsupported provider {preset.provider!r} for model {model_id!r}")
