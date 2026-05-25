# Gategrid — coding principles

Durable **implementation guardrails** for agents and humans. Not product spec, phase plan, or command cheatsheets. **Overview:** [README.md](README.md).

**When:** Reread after plan approval (step 3), before coding. Read the phase [ADR](docs/adr/) for decisions. After post-impl review, add bullets here only if non-obvious in ADR/code — merge into topic sections below, not new phase archives.

**Workflow (steps 1–6):** [`.cursor/rules/gategrid-phase-workflow.mdc`](.cursor/rules/gategrid-phase-workflow.mdc)

---

## What belongs here

| Include | Example |
| ------- | ------- |
| Cross-phase invariants easy to violate while coding | adapters don’t score; metrics never fail CI |
| Discovery / executor gotchas | global gate registry; contrib registration on import |
| Test expectations | import-guard tests; subprocess CLI smoke |

| Do **not** include | Put it in |
| ------------------ | --------- |
| Steps 1–6, plan gates | [gategrid-phase-workflow.mdc](.cursor/rules/gategrid-phase-workflow.mdc) |
| Phase scope, exits, checklist rows | [v1-implementation-checklist.md](docs/roadmap/engineering/v1-implementation-checklist.md) |
| Decision tables, schema fields | [docs/adr/](docs/adr/) |
| Product layers, clean-break tables | Checklist [Product shape](docs/roadmap/engineering/v1-implementation-checklist.md#product-shape-what-ships-where), [Clean break](docs/roadmap/engineering/v1-implementation-checklist.md#clean-break-policy-v1--no-legacy-path) |
| Run/setup commands | [CLAUDE.md](CLAUDE.md) |
| CI operator steps, bench playbook | [docs/guides/ci.md](docs/guides/ci.md), [docs/guides/bench-analysis.md](docs/guides/bench-analysis.md) |

**Before adding a bullet:** Needed in the first 60 seconds of a future change? If ADR states it, link ADR — don’t copy.

---

## Packaging and clean break

- **Install surface = `gategrid` only.** Core deps minimal; optional stacks in extras. No `pydantic-evals` / legacy harness in default install.
- **Ship only `gategrid*`** from `pyproject.toml`. Legacy `agent_eval_matrix` + `experiments/` removed after Spike C ([legacy teardown](docs/roadmap/engineering/v1-implementation-checklist.md#legacy-teardown-after-spike-c)).
- **No legacy bridges** (`[legacy]` extra, `tool_sets`, dual report formats). [Clean break policy](docs/roadmap/engineering/v1-implementation-checklist.md#clean-break-policy-v1--no-legacy-path).
- **File-edit in `contrib`, not core.** `@case` + matrix case ids in core; sandbox / file-match in `gategrid.contrib`. Promote contrib only when generalizable — [contrib README](src/gategrid/contrib/README.md).

## Code style

- **Export public config models** from `gategrid.models` when part of the plugin/YAML contract.
- **Prefer one obvious code path** over single-call helpers — match surrounding module style.

## Paths and on-disk layout

- **Artifacts under `.gategrid/`** (`GATEGRID_HOME`). Do not write Gategrid matrix JSON to repo-root `/reports/` (gitignored). Published bench write-ups live under **`docs/reports/`** (tracked).
- **`ensure_home()` only when writing under the active home** — pass `home=` through `save_json` for custom homes.
- **Eval tree:** `matrices/`, `profiles/`, `models/`, `case_sets/`, optional `cases/`, `evaluators/`; matrix uses `profiles:` not `tool_sets`.

## Config and validation

- **Pydantic `BaseModel` for YAML**; defer `pydantic-settings` until needed.
- **`gategrid validate`** mirrors `run`: same eval-root resolution; case ids via builtin batteries + optional `cases/`; validate `evaluators/` when present (tags, duplicate ids, `GATEGRID_EVALUATOR_ID_QUALIFY`).
- **Core `ProfileConfig`:** only `name`, `runtime_adapter`, opaque `data`. File-edit uses `data.system_prompt` and `data.tools` (contrib helpers) — not top-level profile fields.

## Cases and discovery

- **Discovery:** builtin file-edit cases always loaded; optional `eval_root/cases/` via `pkgutil` merges with collision errors; put eval root **first** on `sys.path` when switching projects in one process.
- **Case ids:** default function name; `GATEGRID_CASE_ID_QUALIFY=module` for dotted ids; fail on collisions.
- **No `gate_check` on `@case`** — scoring only via `@evaluator`.

## Runtime adapters and executor

- **Adapters return `RunArtifact` only** — no pass/fail. [ADR 0003](docs/adr/0003-gategrid-phase2-executor.md).
- **`profile.runtime_adapter` required** for `run` — no silent default.
- **`RunArtifact.error` set** → attempt fails (adapter need not raise); artifact still stored. [ADR 0004](docs/adr/0004-gategrid-phase3-evaluators-contrib.md).
- **Pass/fail:** all `role="gate"` evaluators must return `EvaluatorOutcome(pass_=True)`; if none registered, adapter success (no error) passes.
- **Global gate registry** — every `role="gate"` evaluator runs on **every** cell; contrib gates **no-op** when prerequisites absent (e.g. missing `file_edit` tag).
- **`role="metric"`** never flips `CellResult.passed`; merge via `EvaluatorOutcome.metrics` — prefixed `{evaluator_id}.{key}` unless `@evaluator(canonical=True)`.
- **Pydantic observability (Option A):** not a core evaluator — adapters call `run_agent` + `enrich_artifact_from_run` in `gategrid.integrations.pydantic_ai`; mock via `mock_run_result()`. Core never imports pydantic for evaluator registration. Slim transcript: one `role: tool` row per tool-call + return; `tools_called` is `dict[str, int]`; no `tool_call_count` in `metrics`.
- **`RunArtifact` shape:** `messages`, `metrics`, `evaluators`, `error` only — no `files` / `final_text` / `tool_calls` in matrix JSON ([ADR 0004](docs/adr/0004-gategrid-phase3-evaluators-contrib.md)).

| Layer | Contents |
| ----- | -------- |
| `artifact.metrics` | Adapter / pydantic enrich + evaluator patches (deep-merge; duplicates → `ArtifactMergeError`) |
| `artifact.tools_called` | Pydantic enrich only — evaluators must not patch |
| `artifact.evaluators` | Gates only — from `EvaluatorOutcome`; metrics never stored here |
| `cell.metrics` | `artifact.metrics` numerics + merged metric-evaluator keys (aggregates / gate YAML) |

- **Scratchpad:** per-attempt, not serialized; file-edit sets `actual_content` for `file_content_match` only.
- **Evaluator patches:** must not set `messages` or `evaluators` on `artifact`.
- **Gate failures:** `CellResult.error` = failing gate id; CLI reads `artifact.evaluators[id].message` / `.detail` ([`cli_output.py`](src/gategrid/cli_output.py)).
- **Aggregates / gate:** `compute_overall` and gate checks use matrix YAML keys only — core never hardcodes `turns` ([ADR 0001](docs/adr/0001-gategrid-phase0-schemas-cli-gate.md)).
- **Builtin gates:** `import gategrid.contrib.file_edit` registers `file_content_match`; user `evaluators/` must not re-register the same id.

## CI gates, sampling, and baselines

[ADR 0007](docs/adr/0007-gategrid-phase5-ci-productization.md) · operator detail: [docs/guides/ci.md](docs/guides/ci.md)

- **`gate --baseline-from-artifact`** — resolve file, `baselines/<profile>.json`, or `<profile>.json` under artifact dir.
- **`baseline update --matrix`** — pass matrix YAML so `metric_keys_from_gate` populate baseline `overall.metrics`.
- **PR never `baseline update`**; committed fixture (e.g. `examples/gategrid/ci/baselines/`) for forks; `main` uploads `$GATEGRID_HOME/baselines/` artifact.
- **`run.sample`** — executor runs subset; full-grid `fingerprint.case_ids`; aggregates on executed cells only. Sampled PR matrices: **`like_for_like` regression only**, not `overall` vs full baseline.
- **LFL representativeness** — when `gate.regression.bounds.like_for_like` is set, require `intersection_share ≥ min_like_for_like_share` (default **1.0** vs baseline cell count). PR samples may set a lower share (e.g. `0.5`). See [ci.md — LFL](docs/guides/ci.md#like-for-like-representativeness).
- **`run --model` / `validate --model`** — replaces matrix `models:` for that invocation; presets under `eval_root/models/`. Env `{PREFIX}_MODEL` swaps API model name without changing `model_id` (not baseline-comparable).
- **`run.max_retries`** — cell-level eval flake retry (distinct from adapter tool retries and from statistical replication in checklist 6.9 / wall-time 6.10).

## Bench vs gate (analytics)

[docs/guides/bench-analysis.md](docs/guides/bench-analysis.md)

- **Bench matrices** (`*-bench.yaml`, no `gate:`) — compare profiles in report JSON; do not use headline `pass_rate` as a PR gate or single-run proof.
- **Gate matrices** — `gategrid gate` vs baseline; prefer like-for-like / per-cell regression over overall pass rate alone.
- **`run.sample`** caps executed cells for cost — not the same as bench exploration across profiles.
- Report JSON: read **`run_max_retries`** when comparing runs; do not conflate with tool-level or replication retries.

## MCP

[ADR 0006](docs/adr/0006-gategrid-phase4-mcp-path.md)

- **Config under `profile.data` only** — `data.mcp` (`transport`, `command`/`args` or `url`); `data.env_pass_through` lists env **names**; values resolved in adapter, not in core `validate`.
- **`contrib/mcp`** — `mcp_from_profile`, `resolve_env_pass_through`; no `mcp` / pydantic-ai import at contrib load.
- **Pydantic-ai MCP** — `mcp_toolset_from_data` in `integrations/pydantic_ai/mcp_servers`; requires `gategrid[pydantic-ai,mcp]`. Stdio spawn uses `cwd=eval_root`.
- **Shared eval roots:** MCP gates no-op without `mcp` case tag; other gates no-op outside their tags — global registry still runs all gates on every cell.
- **CI:** `examples/gategrid/matrices/mcp-gate-mock.yaml` for pytest; live `mcp-gate.yaml` is manual README exit.

## Tests

- **Import-guard tests** assert the **installed core** (optional deps not importable), not monorepo `PYTHONPATH` side effects.
- **Exit suite:** `pytest tests/test_gategrid_phase*.py` (through phase 5) + `test_gategrid_cli_output.py` + `test_gategrid_spike_c.py`. CI `test` job syncs `--extra pydantic-ai` because CLI subprocess covers OpenCrabs hashline-smoke.
- **CLI smoke in a subprocess** when in-process imports can mask evaluator registration bugs (duplicate `@evaluator` on contrib + example shim).

## Doc hub

[docs/README.md](docs/README.md) — `guides/`, `adr/`, `roadmap/{product,engineering,research}/`, `reports/`. Checklist: [v1-implementation-checklist.md](docs/roadmap/engineering/v1-implementation-checklist.md).
