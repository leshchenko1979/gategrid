from __future__ import annotations

import json
import logging
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPORTS_DIR = Path(__file__).resolve().parents[2] / "reports"
TRACES_DIR = REPORTS_DIR / "traces"

_logfire_configured = False


def setup_observability() -> None:
    """Configure stdout logging and optional Logfire when token is present."""
    global _logfire_configured

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    if _logfire_configured:
        return

    try:
        import logfire

        logfire.configure(send_to_logfire="if-token-present")
        logfire.instrument_pydantic_ai()
        _logfire_configured = True
        if os.environ.get("LOGFIRE_TOKEN"):
            logging.getLogger(__name__).info("Logfire enabled (token present)")
        else:
            logging.getLogger(__name__).info(
                "Logfire configured locally only (no LOGFIRE_TOKEN)"
            )
    except Exception as exc:
        logging.getLogger(__name__).warning("Logfire setup skipped: %s", exc)


def get_commit_sha() -> str:
    return os.getenv("GITHUB_SHA", "local-run")[:7]


def append_trace_event(run_id: str, event: dict[str, Any]) -> None:
    TRACES_DIR.mkdir(parents=True, exist_ok=True)
    path = TRACES_DIR / f"{run_id}.jsonl"
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, default=str) + "\n")


def span_context(name: str, **attrs: Any):
    """Context manager: Logfire span when available, else no-op."""
    if os.environ.get("LOGFIRE_TOKEN"):
        try:
            import logfire

            return logfire.span(name, **attrs)
        except Exception:
            pass
    from contextlib import nullcontext

    return nullcontext()


def now_iso() -> str:
    return datetime.now(UTC).isoformat()
