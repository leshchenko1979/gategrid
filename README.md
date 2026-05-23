# LLM File-Editing Eval Harness

Matrix evaluation for **pure file-editing** agents built with [pydantic-ai](https://ai.pydantic.dev/). Experiments are declared in YAML; Python under `experiments/tooling/` supplies one tool function per file.

**Matrix** = `tool_sets` × `models` × `cases` (inline or via `case_sets`). Pass/fail is **exact file content match** against `expected_output`.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

cp .env.example .env
# Set API keys required by your matrix's model presets (see src/harness/config.py)
```

## Run

Default matrix: [`experiments/matrices/full.yaml`](experiments/matrices/full.yaml).

```bash
python -m harness.matrix run
python -m harness.matrix run --matrix experiments/matrices/ci.yaml
python -m harness.matrix run --variant <tool-set>/<model-preset>
python -m harness.evals run --case <case_name> --tool-set <tool_set>
python -m harness.matrix run --trace   # JSONL traces → reports/traces/
```

Installed entry points: `harness-matrix`, `harness-evals`.

## Layout

| Path | Role |
|------|------|
| `experiments/cases/` | One YAML per edit task |
| `experiments/case_sets/` | Named lists of case names |
| `experiments/tool_sets/` | `system_prompt` + `tools:` path list |
| `experiments/tooling/` | Per-tool `.py` modules (no prompt bundling) |
| `experiments/matrices/` | Runnable matrix definitions (`tool_sets` × `models` × cases) |
| `src/harness/` | Loader, sandbox, CLI, model presets |

**Tooling rules:** no `SYSTEM_PROMPT` / `TOOLS` / `register(agent)` bundles in tool `.py` files. Harness wrappers live in `tooling/harness/` (delegate to `harness.tools`); other families (e.g. `tooling/opencrabs/`) compose via their own tool-set YAML.

Models should use **workspace-relative** paths (`app.py`). The sandbox accepts absolutes inside the workspace and normalizes macOS `/private/var` vs `/var`.

## Matrix

```yaml
# experiments/matrices/example.yaml
tool_sets:
  - baseline
  - minimal
models:
  - minimax-m2.7          # key in MODEL_PRESETS (src/harness/config.py)
case_sets:
  - smoke                 # or list cases inline under cases:
```

Matrix `name` is optional (defaults to the file stem).

## Tool set

```yaml
# experiments/tool_sets/example.yaml
name: example
system_prompt: |
  You are a precise file editing agent...
tools:
  - tooling/harness/ls.py
  - tooling/harness/read_file.py
```

Paths are relative to `experiments/`.

**Add a tool set:** (1) add one-tool modules under `experiments/tooling/`, (2) create `experiments/tool_sets/<name>.yaml`, (3) reference `<name>` in a matrix `tool_sets` list.

## Case

```yaml
# experiments/cases/example.yaml
name: example
instruction: Describe the edit for the model.
file_name: target.py
initial_content: |
  ...
expected_output: |
  ...
tags: []   # optional; surfaced in reports
```

**Case set** (`experiments/case_sets/example.yaml`): `name` + `cases: [case_stem, ...]` (stems match `experiments/cases/<stem>.yaml`).

## Models

Presets live in [`src/harness/config.py`](src/harness/config.py) (`MODEL_PRESETS`). Each preset defines `model_name`, `base_url`, and `api_key_env`. Matrix `models` lists preset keys.

Optional overrides (any preset): `OPENAI_BASE_URL`, `HARNESS_MODEL`.

This repo ships `minimax-m2.7` → set `MINIMAX_API_KEY` (see `.env.example`). Add presets and env vars when wiring other providers.

## Reports & metrics

- Aggregate JSON: `reports/{timestamp}_{sha}_matrix.json`
- Traces: `reports/traces/{run_id}.jsonl` (with `--trace`)
- Optional Logfire: `LOGFIRE_TOKEN` (`send_to_logfire='if-token-present'`)

Comparison metrics (pass/fail remains file match only): **turns**, **tokens_spent**, **tool_failures**, **duration_ms**. See project notes in `CLAUDE.md` for definitions.

## CI

[`.github/workflows/evals.yml`](.github/workflows/evals.yml) — configure secrets for the model presets your matrix uses (e.g. `MINIMAX_API_KEY`); optional `LOGFIRE_TOKEN`.

## Extending this repo

- **New cases / tool sets / matrices:** add YAML under `experiments/` and reference them in a matrix file.
- **Specialized studies:** e.g. hashline hypotheses — `experiments/matrices/hashline_hypotheses.yaml` and [`docs/README.md`](docs/README.md).
