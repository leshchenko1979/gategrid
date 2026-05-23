# Hashline hypothesis evaluation (OpenCrabs)

Standalone report for **OpenCrabs** developers. Upstream was not involved in designing these hypotheses.

| Artifact | Description |
|----------|-------------|
| [**hashline_hypothesis_report.md**](hashline_hypothesis_report.md) | Full report — **implementers start at [§2 Quick reference](hashline_hypothesis_report.md#2-quick-reference-for-implementers)** |
| [**hashline_hypothesis_report.ipynb**](hashline_hypothesis_report.ipynb) | Charts (GitHub renders `.ipynb` natively) |
| [Matrix JSON](../reports/2026-05-23T13-22-35.666225+00-00_local-r_matrix.json) | Raw 50-run output |

**Verdicts:** H2 fuzzy replace **supported** (10/10); H3 empty-hash collisions **rejected** (7/10); H1 inconclusive; H4 mixed.

```bash
pip install -e ".[report]"
python docs/_build_report_viz.py
```
