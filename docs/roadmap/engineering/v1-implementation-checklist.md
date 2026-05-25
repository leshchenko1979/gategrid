# v1 implementation checklist

Ship the **competitive wedge**: matrix runner + **git baseline gate** + **Python plugins**. Maps to [architecture-vision.md](architecture-vision.md) (phases 0–5); phase 6 is post-v1.

**Product:** [Gategrid](../product/competitive-landscape.md#product-naming-revisited) — `gategrid` on PyPI, data dir `.gategrid/`. **GitHub:** [leshchenko1979/gategrid](https://github.com/leshchenko1979/gategrid) (renamed from `agent-eval-matrix`).

**Docs:** [battlecard.md](../product/battlecard.md) · [competitive-landscape.md](../product/competitive-landscape.md) · [spike-dx-competitive-analysis.md](../research/spike-dx-competitive-analysis.md) (required per spike) · [adoption-usability-backlog.md](../research/adoption-usability-backlog.md) (ADOPT ids in tables) · [dogfood-notes.md](../research/dogfood-notes.md)

**Coding principles:** [CODE.md](../../../CODE.md) — reread before implementation (after plan approval); merge lessons after post-impl review (topic sections, not phase archives).

**Implementation workflow:** [`.cursor/rules/gategrid-phase-workflow.mdc`](../../../.cursor/rules/gategrid-phase-workflow.mdc) — steps 1–6 for any code change; phases 1+ mark **W** when closed.

**Status (2026-05):** **Framework** phases 0–5 complete. **Product** still open: PyPI ([R.1](#rename--publish)), external spikes B/A, [D.8](#integration-summary) go/no-go.

**Companion docs:** [ADRs](../../adr/) and this checklist are **implementation truth**. [architecture-vision.md](architecture-vision.md) is a historical design essay (may still name pre-Gategrid paths); [docs/guides/ci.md](../../guides/ci.md) is the CI operator hub.

---

## Product shape (what ships where)


| Layer                  | Owns                                                                                                                                            | Does **not** own                                                                  |
| ---------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------- |
| **gategrid core**      | Matrix expand · case **ids** in YAML · `@case` · `RuntimeAdapter` → `RunArtifact` · `CellExecutor` · reports · `gate` / `baseline` · `validate` | File sandbox · file-tool YAML cases · file-content pass/fail · MCP · LLM runtimes |
| **gategrid.contrib**   | Optional reference plugins — **grown from spikes** when generalizable (adapters, evaluators, helpers); never required for core                  | Required for core install                                                         |
| **User repo `evals/`** | `@case` bodies · profiles · models · matrices · repo-specific adapters · `@evaluator`                                                           | Framework storage (uses `.gategrid/`)                                             |


**schemas/v1:** frozen **outputs** and **matrix config** (`case_id` on cells, not case content). Legacy `EditCase` YAML is **not** a core contract.

**Legacy removed (2026-05):** `src/agent_eval_matrix/` and `experiments/` deleted after Spike C (content in [`examples/opencrabs/`](../../../examples/opencrabs/) / `contrib`). See [Legacy teardown](#legacy-teardown-after-spike-c).

**Spike → contrib:** Dogfooding may start with code in a target repo’s `evals/`. When a pattern is **reusable across repos** (second spike needs it, or it’s clearly not project-specific), **promote it to `gategrid.contrib`** (optional extra if deps are heavy). Keep one-off wiring in the user repo.

---

## Clean break policy (v1 — no legacy path)


| Not shipped                                                            | Replacement                                                    |
| ---------------------------------------------------------------------- | -------------------------------------------------------------- |
| `[legacy]` extra, pydantic-evals bridge, legacy report readers         | Gategrid models + `gategrid run` only                          |
| `agent-eval-matrix` / `agent-eval` CLIs                                | `gategrid` CLI only                                            |
| `.agent-eval-matrix/`, repo-root `reports/` for Gategrid               | `.gategrid/` only                                              |
| `tool_sets` in matrix YAML, `experiments/` as runtime root             | `profiles` + user `evals/` or `examples/*` in this repo       |
| `EditCase` / `cases/*.yaml` / sandbox / `FileContentMatch` **in core** | `@case` + `RuntimeAdapter` in core; file-edit in **contrib** |
| Dual baseline / report converters                                      | `MatrixReport` → `baseline update` → `gate`                    |


Legacy harness removed; Gategrid core/CI uses `examples/gategrid/` and `examples/opencrabs/`.

---

## v1 exit criteria (product)

- `pip install gategrid` — core without pydantic-ai / pydantic-evals
- `gategrid run` → `.gategrid/reports/`; `gategrid gate` / `baseline update` on per-profile baselines
- User eval tree: `@case` + matrix YAML (ids + profiles + models); optional `**contrib/file_edit`** for file-benchmark style evals
- PR: sample + gate; **no** baseline update on PR
- MCP example (Phase 4): LLM-mediated stdio or remote; env/side effects documented
- README + battlecard reproducible locally

**Dogfooding (personal, non-blocking v1):** [D.4–D.8](#integration-summary) + verdict in [dogfood-notes.md](../research/dogfood-notes.md). Legacy delete: **D.5** after OpenCrabs (C).

---

## Phase 0 — Schemas, gate, run stub ✓

**Goal:** Frozen artifacts + `gate` / `baseline update`; executor deferred.

**ADR:** [0001-gategrid-phase0-schemas-cli-gate.md](../../adr/0001-gategrid-phase0-schemas-cli-gate.md)


| #       | Item                                                              |     |
| ------- | ----------------------------------------------------------------- | --- |
| 0.1–0.7 | [x] Schemas, ADR, `schemas/v1/`, flake/sampling fields            |     |
| 0.8–0.9 | [x] CLI `gate`, `baseline update`, `run` stub, executor docstring |     |


**Exit:** `pytest tests/test_gategrid_phase0.py`; examples under `schemas/v1/examples/`.

---

## Phase 1 — Installable core skeleton ✓

**Goal:** `gategrid`-only package; validate matrix wiring.

**ADR:** [0002-gategrid-phase1-packaging-validate.md](../../adr/0002-gategrid-phase1-packaging-validate.md)


| #   | Item                                                                                  |           |
| --- | ------------------------------------------------------------------------------------- | --------- |
| W   | [x] Phase workflow                                                                    |           |
| 1.1 | [x] `pyproject`: `gategrid`, minimal core, extras `pydantic-ai` / `dev` — no `legacy` | ADOPT-011 |
| 1.2 | [x] CLI: `gategrid` only                                                              | ADOPT-001 |
| 1.3 | [x] `.gategrid/` writer                                                               |           |
| 1.4 | [x] Import graph: no pydantic-evals / agent_eval_matrix on install                    |           |
| 1.5 | [x] `gategrid validate` (matrix, profiles, models, case_sets)                         | ADOPT-001 |


**Exit:** `gategrid validate --matrix examples/gategrid/matrices/smoke.yaml`; `pytest tests/test_gategrid_phase0.py tests/test_gategrid_phase1.py`.

---

## Phase 2 — Matrix execution (core) ✓

**Goal:** Walk the grid; produce `MatrixReport`. **Universal** runtime surface only.


| #   | Item                                                                                         | Notes                                                                                                                         |
| --- | -------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| W   | [x] Phase workflow                                                                           |                                                                                                                               |
| 2.1 | [x] `RuntimeAdapter` protocol + `RunContext` (profile, model, case_id, eval_root)            | No file paths in core contract                                                                                                |
| 2.2 | [x] `@case` registry + discovery; matrix / `case_sets` → **case id list**                    | Optional `id` (default fn name), optional `tags`; `GATEGRID_CASE_ID_QUALIFY`; fail on id collision; no `cases/*.yaml` in core |
| 2.3 | [x] Resolve profiles + models from eval root; CLI `--root` (+ optional `GATEGRID_EVAL_ROOT`) | ADOPT-003; not `experiments/`                                                                                                 |
| 2.4 | [x] `CellExecutor`: expand cases × profiles × models; async run; write report                | Replaces executor stub                                                                                                        |
| 2.5 | [x] `run.max_retries` + `flaky_suspect` on `CellResult`                                      | architecture-vision                                                                                                           |
| 2.6 | [x] Failure UX: cell key, error message, suggested `gategrid run …` rerun                    | ADOPT-004 mostly done: `cli_output`, evaluators `message`/`detail`, slim `RunArtifact`                                       |


**Phase 2 exit:**

```bash
gategrid run --matrix examples/gategrid/matrices/smoke.yaml
# examples/gategrid/cases/ — Python @case package; demo adapter or example RuntimeAdapter
pytest tests/test_gategrid_phase0.py tests/test_gategrid_phase1.py tests/test_gategrid_phase2.py
```

Pass/fail was interim `gate_check` on `@case` until Phase 3 (`@evaluator`).

**Blocks Spike C** until Phase 3 contrib + file-match (hashline is a file-benchmark, not core) — **unblocked** after Phase 3 ✓.

---

## Phase 3 — Evaluators + contrib ✓

**Goal:** User-owned scoring; `**gate`** vs `**metric`**. File-edit benchmark lives here, not in core.

**ADR:** [0004-gategrid-phase3-evaluators-contrib.md](../../adr/0004-gategrid-phase3-evaluators-contrib.md) · [0005-gategrid-file-edit-batteries.md](../../adr/0005-gategrid-file-edit-batteries.md) (3.4)


| #   | Item                                                                                                                                                                   | Notes           |
| --- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------- |
| W   | [x] Phase workflow                                                                                                                                                     |                 |
| 3.1 | [x] `@evaluator` decorator + `gate` / `metric` tags                                                                                                                    | ADOPT-009       |
| 3.2 | [x] Cell pass: all `gate` evaluators pass on ≥1 attempt (with 2.5 retries); `RunArtifact.error` fails attempt                                                          |                 |
| 3.3 | [x] `gategrid.contrib` package layout + promotion criteria README                                                                                                      |                 |
| 3.4 | [x] `**contrib/file_edit`:** sandbox + `file_content_match_impl` (adapter/tools/YAML → Spike C)                                                                      | ADOPT-019       |
| 3.5 | [x] `contrib.llm_judge` base class (`LlmJudgeBase`)                                                                                                                  | user-side judge |


**Phase 3 exit:**

```bash
gategrid validate --matrix examples/gategrid/matrices/smoke.yaml
gategrid run --matrix examples/gategrid/matrices/smoke.yaml
# examples/gategrid/evaluators/ — @evaluator; contrib via file_content.py shim
pytest tests/test_gategrid_phase0.py tests/test_gategrid_phase1.py tests/test_gategrid_phase2.py tests/test_gategrid_phase3.py
```

Pass/fail driven by `@evaluator(tags=["gate"])`; at least one contrib module exercised from `examples/`; metrics never fail CI. Further contrib modules may land **during or after** spikes without a new phase.

**Unblocks Spike C** (hashline matrices using `contrib/file_edit` + opencrabs-oriented `RuntimeAdapter`).

---

## Phase 4 — MCP path ✓

**Goal:** Credible LLM-mediated MCP eval story (`[mcp]` extra).

**ADR:** [0006-gategrid-phase4-mcp-path.md](../../adr/0006-gategrid-phase4-mcp-path.md)


| #   | Item                                                        |                |
| --- | ----------------------------------------------------------- | -------------- |
| W   | [x] Phase workflow                                          |                |
| 4.1 | [x] `[mcp]` extra: stdio + remote helpers                   |                |
| 4.2 | [x] Example profile: server command + env name pass-through | secrets policy |
| 4.3 | [x] Example `matrices/mcp-gate.yaml` (one profile)          | battlecard     |
| 4.4 | [x] Document user-owned side effects / env                  |                |
| 4.5 | [x] No direct MCP invoke tests in core                      | non-goal       |


**Phase 4 exit:**

```bash
uv sync --extra dev --extra pydantic-ai --extra mcp
pytest tests/test_gategrid_phase0.py tests/test_gategrid_phase1.py \
  tests/test_gategrid_phase2.py tests/test_gategrid_phase3.py \
  tests/test_gategrid_phase4.py tests/test_gategrid_cli_output.py
gategrid validate --matrix examples/gategrid/matrices/mcp-gate-mock.yaml --root examples/gategrid
# Manual: OPENAI_API_KEY + gategrid run --matrix examples/gategrid/matrices/mcp-gate.yaml --root examples/gategrid
```

**Unblocks Spike A** (fast-mcp-telegram).

---

## Phase 5 — CI productization ✓

**Goal:** GitHub Actions recipes; sampling; gate vs benchmark matrices in docs.

**ADR:** [0007-gategrid-phase5-ci-productization.md](../../adr/0007-gategrid-phase5-ci-productization.md)

**CI guide:** [docs/guides/ci.md](../../guides/ci.md) — PR `gate`, `main` baseline refresh, `run.sample`, copy-paste workflows.

*Note: `gategrid gate` / `baseline update` / regression math largely exist from Phase 0; this phase wires **CI, sampling, and examples**.*


| #   | Item                                                                   |                      |
| --- | ---------------------------------------------------------------------- | -------------------- |
| W   | [x] Phase workflow                                                     |                      |
| 5.1 | [x] Harden `gate` docs + edge cases (overall + like-for-like)          | ADOPT-016            |
| 5.2 | [x] `gate.limits` examples in matrix YAML                              |                      |
| 5.3 | [x] `baseline update` on `main` workflow pattern                       |                      |
| 5.4 | [x] `--baseline-from-artifact` for PR                                  |                      |
| 5.5 | [x] `run.sample` (`max_cells`, `share`, `seed`, `always_include_tags`) |                      |
| 5.6 | [x] Fingerprint mismatch → warn (overall regression)                   |                      |
| 5.7 | [x] [gategrid-ci.yml](../../../.github/workflows/gategrid-ci.yml) (+ [gategrid.yml.example](../../../.github/workflows/gategrid.yml.example)) | ADOPT-005, ADOPT-014 |
| 5.8 | [x] Tiered CI: demo / smoke / full                                     | ADOPT-005            |
| 5.9 | [x] Gate vs benchmark matrix examples                                  | pitch README         |


**Phase 5 exit:**

```bash
uv sync --extra dev --extra pydantic-ai --extra mcp
pytest tests/test_gategrid_phase0.py tests/test_gategrid_phase1.py \
  tests/test_gategrid_phase2.py tests/test_gategrid_phase3.py \
  tests/test_gategrid_phase4.py tests/test_gategrid_cli_output.py \
  tests/test_gategrid_phase5.py
gategrid validate --matrix examples/gategrid/matrices/ci-gate-mock.yaml --root examples/gategrid
gategrid run --matrix examples/gategrid/matrices/ci-gate-mock.yaml --root examples/gategrid
gategrid gate --matrix examples/gategrid/matrices/ci-gate-mock.yaml --root examples/gategrid \
  --baseline examples/gategrid/ci/baselines/demo.json
```

**Exit:** PR fails on regression; main can refresh baseline; docs match pitch.

---

## Phase 6 — Post-v1 (defer)


| #       | Item                                               | ADOPT         |
| ------- | -------------------------------------------------- | ------------- |
| W       | [ ] Phase workflow                                 | —             |
| 6.1     | [ ] HTML report + heatmap                          | ADOPT-007     |
| 6.2     | [ ] `--concurrency` / progress                     | ADOPT-006     |
| 6.3     | [ ] GitHub Action marketplace wrapper              | ADOPT-014     |
| 6.4     | [ ] `gategrid init` scaffold                       | ADOPT-002     |
| 6.5–6.7 | [ ] Logfire template, cost estimator, trace replay | ADOPT-013–018 |
| 6.8     | [ ] **Provider rate-limit handling** — retry HTTP 429 (and optional 503) at LLM boundary with backoff + jitter; matrix or model config; surface `rate_limit_retries` on cells; **not** the same as `run.max_retries` (full cell flake retry) | ADOPT-020 |
| 6.9     | [ ] **Statistical cell replication** — optional `run.replications` (or `pass_min_of_n`): N independent attempts per cell, pass rule e.g. majority; report all attempts; baseline/gate semantics documented; **not** the same as `run.max_retries` (retry until pass) or `run.sample` (subset of cells) | — |
| 6.10    | [ ] **Matrix wall-time budget** — `run.max_wall_time_s`: stop scheduling new cells when elapsed cap exceeded; record skipped keys like sampling; gate treats skips as neither pass nor fail; optional per-cell `timeout_s` later (ADOPT-006) | ADOPT-006 |
| 6.11    | [ ] **Bench report compare (product)** — diff two `*_matrix.json` (cell pass flips, per-profile totals). Conventions: [bench-analysis.md](../../guides/bench-analysis.md) | — |
| 6.12    | [ ] **Run summary: failure taxonomy + flaky count (product)** — stderr or report metadata on `run` exit. Conventions: [bench-analysis.md](../../guides/bench-analysis.md) | — |
| 6.13    | [ ] **Doc debt:** refresh [architecture-vision.md](architecture-vision.md) phased table + snippets (`agent-eval`, split workflows); align [adoption-usability-backlog.md](../research/adoption-usability-backlog.md) voice; optional consolidated exit block in checklist (vs [CLAUDE.md](../../../CLAUDE.md)) | — |


**6.8 evidence:** OpenCrabs `hashline-bench` (MiniMax) lost 2/50 cells to 429 — [dogfood-notes](../research/dogfood-notes.md). Bench matrices and CI full runs need transport-level retries so failures are not misread as model/tool regressions.

**6.9 / 6.10 (deferred from Phase 5):** Phase 5 uses existing `run.max_retries` for eval flake and `run.sample` for PR cell-count caps only; statistical replication and wall-time budget are out of Phase 5 scope (ADR 0007).

---

## Priority order (post–framework v1)

Phases **0–5** and Spike C + legacy teardown are complete. Suggested single-threaded order:


| Order | Track | Outcome |
| ----- | ----- | ------- |
| 1 | **Spike B** (ai-antispam) | Classifier gate + `evals/` layout |
| 2 | **Spike A** (fast-mcp-telegram) | MCP matrix + GH workflows |
| 3 | **R.1** PyPI | `pip install gategrid` |
| 4 | **Phase 6** picks | HTML report, concurrency, rate limits ([6.8](#phase-6--post-v1-defer)), doc debt ([6.13](#phase-6--post-v1-defer)) |
| 5 | **D.8** | Go / no-go vs [success criteria](#success--kill-criteria-personal) |

Do **not** port file-edit into core; use **contrib** + spikes for domain evals.

---

## Dogfooding spikes

Prove value on three repos **before** over-investing in polish. **Gategrid-only** — no legacy CLI, no report converters.

### Spike DX competitive analysis (required)

Every spike **must** go through [spike-dx-competitive-analysis.md](../research/spike-dx-competitive-analysis.md) before implementation work beyond layout/smoke, and again at spike close.

| Step | Checklist | Record in |
| ---- | --------- | --------- |
| **Kickoff** | Fill spike brief (Tasks A/B/C, domain vs orchestration LOC estimate, hypothesized winner) | [dogfood-notes.md](../research/dogfood-notes.md) |
| **Implement** | Split LOC: orchestration vs domain vs shared `contrib` | Same |
| **Close** | Measured LOC table + winner per task + positioning note | [spike-dx-competitive-analysis.md](../research/spike-dx-competitive-analysis.md) decision log + dogfood-notes |

Spike tables below include **DX-*** rows; do not mark spike complete until DX close row is `[x]`.

### Spike → contrib

Use spikes to learn what belongs in the framework vs a single product repo.


| Keep in **target repo `evals/`**            | **Promote to `gategrid.contrib`** when                                                            |
| ------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| Cases, fixtures, secrets, domain evaluators | A second spike (or clear second use case) needs the same adapter/evaluator/helper                 |
| Profile/matrix YAML for that product        | Pattern is domain-agnostic (MCP stdio client, file sandbox, label-match gate, classifier metrics) |
| One-off `RuntimeAdapter` wiring             | API is stable enough to document and test in this repo                                            |


**Process:** implement in spike repo first → note in [dogfood-notes.md](../research/dogfood-notes.md) → extract to `src/gategrid/contrib/<name>/` + optional extra → spike repo imports contrib. **Do not** promote repo-specific logic (Telegram session setup, opencrabs binary paths) unless abstracted behind config.

**Examples (expected contrib candidates):** `file_edit` (C), classification eval helpers (B), MCP agent loop helpers (A) — each only after spike proves the API.

### Order


| #   | Repo                  | Spike | When                                                 |
| --- | --------------------- | ----- | ---------------------------------------------------- |
| 1   | **opencrabs**         | C     | After **Phase 3** (`contrib/file_edit` + evaluators) |
| 2   | **ai-antispam**       | B     | After Phase 3 (`@case` + custom evaluators)          |
| 3   | **fast-mcp-telegram** | A     | After Phase 4–5                                      |


### Layout (each target repo)

```text
evals/
  cases/           # @case Python package
  matrices/
    *-gate.yaml    # one profile — PR + baseline
    *-bench.yaml   # optional research
  profiles/
  models/
.gategrid/
  baselines/<profile-id>.json
  reports/         # gitignore
```

### Spike C — OpenCrabs (1st)


| #       | Task                                                                                                                                                | Needs         |
| ------- | --------------------------------------------------------------------------------------------------------------------------------------------------- | ------------- |
| C.0     | [x] Gategrid-only policy in [dogfood-notes.md](../research/dogfood-notes.md)                                                                                    | —             |
| DX-C    | [x] [Spike DX analysis](../research/spike-dx-competitive-analysis.md#spike-c--opencrabs-retroactive-2026-05) (kickoff + close; retroactive 2026-05)              | positioning   |
| C.1     | [x] Hashline under `examples/opencrabs/` (ported from legacy `experiments/`) | 3.4, 2.2      |
| C.2     | [x] `gategrid run` + `opencrabs_original` profile via **adapter** (Python tools or binary stretch)                                                  | 3.4, 2.4      |
| C.3     | [x] `baseline update` + `gate` loop; record in dogfood-notes                                                                                        | 5.x workflows |
| C.4     | [x] Regression drill (gate exit 1 on bad report, 0 on good)                                                                                         | dogfood-notes |
| C.5     | [x] `examples/opencrabs/` layout documented                                                                                                         | dogfood-notes |
| C.6     | [x] `hashline-bench.yaml` run on Gategrid (minimax; 44/50 pass, rate limits — dogfood-notes)                                                          | dogfood-notes |
| C.7     | [x] [hashline_hypothesis_report.md](../../reports/hashline/hashline_hypothesis_report.md) points at `.gategrid/reports/`                                                  |               |
| C.8–C.9 | [ ] Stretch: Rust binary adapter; upstream CONTRIBUTING                                                                                             |               |


### Legacy teardown (after Spike C)

**When:** [D.4](#integration-summary) complete — **not** before OpenCrabs is finished on Gategrid.


| #   | Task                                                                                                                  |
| --- | --------------------------------------------------------------------------------------------------------------------- |
| L.1 | [x] Remove `src/agent_eval_matrix/` and legacy harness tests                                                          |
| L.2 | [x] Remove `experiments/` (content in [`examples/opencrabs/`](../../../examples/opencrabs/) / `contrib`)               |
| L.3 | [x] Switch `.github/workflows/` to Gategrid-only ([gategrid-ci.yml](../../../.github/workflows/gategrid-ci.yml))              |
| L.4 | [x] Update README, [CLAUDE.md](../../../CLAUDE.md) — no legacy run commands                                              |

### Spike B — ai-antispam (2nd)


| #       | Task                                                                                                           | Needs    |
| ------- | -------------------------------------------------------------------------------------------------------------- | -------- |
| DX-B    | [x] [Spike DX kickoff](../research/spike-dx-competitive-analysis.md#spike-b--ai-antispam) in [dogfood-notes](../research/dogfood-notes.md) (2026-05-25); **close** at D.6 | positioning   |
| B.1–B.9 | [ ] `evals/`, fixtures as `@case`, classifier `RuntimeAdapter`, gate evaluators, spam-gate matrix, flake notes | 2–3, 5.9 |


### Spike A — fast-mcp-telegram (3rd)


| #       | Task                                                     | Needs |
| ------- | -------------------------------------------------------- | ----- |
| DX-A    | [x] [Spike DX kickoff](../research/spike-dx-competitive-analysis.md#spike-a--fast-mcp-telegram) in [dogfood-notes](../research/dogfood-notes.md) (2026-05-25); **close** at D.7 | positioning   |
| A.1–A.9 | [ ] MCP matrix, agent adapter, smoke cases, GH workflows | 4, 5  |


### Integration summary


| #   | Item                                                                                                |
| --- | --------------------------------------------------------------------------------------------------- |
| D.0 | [x] [spike-dx-competitive-analysis.md](../research/spike-dx-competitive-analysis.md) exists; Spike C retroactive analysis recorded |
| D.1 | [ ] [dogfood-notes.md](../research/dogfood-notes.md) maintained — **DX kickoff/close** + **contrib promotion** per spike |
| D.2 | [ ] Same `evals/` layout across repos                                                               |
| D.3 | [ ] [examples/dogfood/README.md](../../../examples/dogfood/README.md) index                            |
| D.4 | [x] Spike C complete (parity OK; see [dogfood-notes](../research/dogfood-notes.md))                               |
| D.5 | [x] [Legacy teardown](#legacy-teardown-after-spike-c) L.1–L.4                                       |
| D.6 | [ ] Spike B complete or blocked                                                                     |
| D.7 | [ ] Spike A complete or blocked                                                                     |
| D.8 | [ ] Go / no-go vs [success criteria](#success--kill-criteria-personal)                              |


### Success / kill (personal)

**Continue** if ≥2: trustworthy PR gate · git baseline simpler than cloud UI · new case <30 min · gate caught a real regression.

**Pause** if: more framework than product fixes · unusable flakes · no CI story for MCP/Telegram.

---

## Competitive parity


| Claim                     | Items              |
| ------------------------- | ------------------ |
| vs promptfoo git baseline | 5.1, 5.3, 5.4, 5.9 |
| vs DeepEval pytest        | 2.2, 3.1, 3.4      |
| vs mcp-eval               | 4.1–4.3            |
| vs LangSmith regression   | 5.1, 5.5, 5.7      |
| No SaaS                   | 1.3, 5.3           |


---

## Rename / publish


| #   | Item                                                                                                                       |
| --- | -------------------------------------------------------------------------------------------------------------------------- |
| R.1 | [ ] Reserve `gategrid` on PyPI                                                                                             |
| R.2 | [x] README product = Gategrid                                                                                              |
| R.3 | [x] `.gategrid/` only for Gategrid runtime + examples (historical `agent-eval-matrix` mentions OK in competitive docs / ADRs) |
| R.4 | [x] Delete legacy package + experiments ([L.1–L.2](#legacy-teardown-after-spike-c)) |
