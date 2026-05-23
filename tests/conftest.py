"""Pytest configuration."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLING_DIR = ROOT / "experiments" / "tooling"

# Append so installed `agent_eval_matrix` is not shadowed by experiments/tooling/reference/
if str(TOOLING_DIR) not in sys.path:
    sys.path.append(str(TOOLING_DIR))
