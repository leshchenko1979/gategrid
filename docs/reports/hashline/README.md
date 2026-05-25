# OpenCrabs file-editing evaluation

Report for **OpenCrabs** developers (upstream was not consulted before this study). Tests hashline protocol changes, **two edit tools → one** fuzzy replace (H2), and comparison to a **simplified reference** tool set (H4; 8 vs 32 total tool parameters).

| Artifact | Description |
| -------- | ----------- |
| [hashline_hypothesis_report.md](hashline_hypothesis_report.md) | Full report — implementers start at §2; §3 = **single-run snapshot** |
| [figures/](figures/) | Charts (`pass_rate_by_variant.png`, etc.) — from published run unless regenerated |
| `.gategrid/reports/*_matrix.json` | Gategrid bench output (see report §10) |

**Report sections:** [§2 Quick reference](hashline_hypothesis_report.md#2-quick-reference-for-implementers) · [§3 Executive summary](hashline_hypothesis_report.md#3-executive-summary) · [§10 Run stability](hashline_hypothesis_report.md#run-stability)

**Verdicts (§3 snapshot):** H2 fuzzy replace **supported** in that run (10/10, lower tokens); H3 empty-hash collisions **rejected**; H1 inconclusive; H4 mixed. A second bench run at 44/50 had different failing cells — read stability §10 before upstream sign-off. **How to analyze bench JSON:** [docs/guides/bench-analysis.md](../../guides/bench-analysis.md).

```bash
uv sync --extra report
uv run python docs/reports/hashline/_build_report_viz.py
```

Regenerate matrix JSON: `gategrid -v run --matrix examples/opencrabs/matrices/hashline-bench.yaml --root examples/opencrabs` (set `GATEGRID_REPORT_JSON` to a `.gategrid/reports/*_matrix.json` for the viz script).
