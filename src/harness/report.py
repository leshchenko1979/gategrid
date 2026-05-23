from __future__ import annotations

import json
import logging
from pathlib import Path

from harness.models import MatrixReport
from harness.observability import REPORTS_DIR, now_iso

logger = logging.getLogger(__name__)


def write_report(report: MatrixReport) -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    safe_variant = (
        report.results[0].variant_id.replace("/", "_") if report.results else "run"
    )
    filename = (
        f"{report.timestamp.replace(':', '-')}_{report.commit_sha}_{safe_variant}.json"
    )
    path = REPORTS_DIR / filename
    path.write_text(
        json.dumps(report.model_dump(), indent=2, default=str),
        encoding="utf-8",
    )
    logger.info("Wrote report to %s", path)
    return path


def write_aggregate_report(report: MatrixReport) -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{report.timestamp.replace(':', '-')}_{report.commit_sha}_matrix.json"
    path = REPORTS_DIR / filename
    path.write_text(
        json.dumps(report.model_dump(), indent=2, default=str),
        encoding="utf-8",
    )
    logger.info("Wrote aggregate report to %s", path)
    return path


def print_summary(report: MatrixReport) -> None:
    total = len(report.results)
    passed = sum(1 for r in report.results if r.passed)
    rate = report.pass_rate * 100 if total else 0.0

    print("\n" + "=" * 60)
    print(
        f"Matrix eval summary  matrix={report.matrix_name}  commit={report.commit_sha}"
    )
    print(f"Cases: {total}  Passed: {passed}  Pass rate: {rate:.1f}%")
    print("=" * 60)

    by_variant: dict[str, list] = {}
    for r in report.results:
        by_variant.setdefault(r.variant_id, []).append(r)

    for variant_id, rows in sorted(by_variant.items()):
        v_pass = sum(1 for r in rows if r.passed)
        n = len(rows)
        avg_turns = sum(r.turns for r in rows) / n if n else 0.0
        avg_tokens = sum(r.tokens_spent for r in rows) / n if n else 0.0
        avg_failures = sum(r.tool_failures for r in rows) / n if n else 0.0
        print(f"\n  [{variant_id}] {v_pass}/{n} passed")
        print(
            f"    avg: {avg_turns:.1f} turns, {avg_tokens:.0f} tokens, "
            f"{avg_failures:.1f} failures"
        )
        for row in rows:
            status = "PASS" if row.passed else "FAIL"
            print(
                f"    {status}  {row.case_name}  "
                f"({row.duration_ms:.0f}ms, {row.turns} turns, "
                f"{row.tokens_spent} tokens, {row.tool_failures} failures)"
            )
            if row.error:
                print(f"           error: {row.error[:120]}")

    if report.matrix_name == "hashline_hypotheses":
        _print_hashline_hypothesis_analysis(report, by_variant)

    print("=" * 60 + "\n")


_CONTROL = "opencrabs_original/minimax-m2.7"


def _variant_tooling(variant_id: str) -> str:
    return variant_id.rsplit("/", 1)[0]


def _print_hashline_hypothesis_analysis(
    report: MatrixReport, by_variant: dict[str, list]
) -> None:
    control_rows = by_variant.get(_CONTROL, [])
    if not control_rows:
        print("\n  [hashline hypotheses] control variant not found; skip deltas")
        return

    control_by_case = {r.case_name: r.passed for r in control_rows}
    print("\n  --- Hashline hypothesis deltas (pass vs opencrabs_original) ---")
    for variant_id, rows in sorted(by_variant.items()):
        tooling = _variant_tooling(variant_id)
        if tooling == "opencrabs_original":
            continue
        if tooling == "baseline":
            label = "H4 reference"
        elif tooling == "opencrabs_h1_docs":
            label = "H1 docs"
        elif tooling == "opencrabs_h2_fuzzy":
            label = "H2 fuzzy"
        elif tooling == "opencrabs_h3_collision":
            label = "H3 collision"
        else:
            label = tooling
        deltas: list[str] = []
        for row in rows:
            ctrl = control_by_case.get(row.case_name)
            if ctrl is None:
                continue
            if row.passed and not ctrl:
                deltas.append(f"+{row.case_name}")
            elif not row.passed and ctrl:
                deltas.append(f"-{row.case_name}")
        delta_str = ", ".join(deltas) if deltas else "(no pass changes)"
        v_pass = sum(1 for r in rows if r.passed)
        print(f"  {label}: {v_pass}/{len(rows)} passed  {delta_str}")

    print("\n  --- H4 by language tag ---")
    for tag in ("language:python", "language:yaml"):
        print(f"  [{tag}]")
        for variant_id, rows in sorted(by_variant.items()):
            tagged = [r for r in rows if tag in r.tags]
            if not tagged:
                continue
            p = sum(1 for r in tagged if r.passed)
            print(f"    {_variant_tooling(variant_id)}: {p}/{len(tagged)} passed")

    print("\n  --- By size:large tag ---")
    for variant_id, rows in sorted(by_variant.items()):
        large = [r for r in rows if "size:large" in r.tags]
        small = [r for r in rows if "size:large" not in r.tags]
        if not large and not small:
            continue
        parts: list[str] = []
        if large:
            lp = sum(1 for r in large if r.passed)
            parts.append(f"large {lp}/{len(large)}")
        if small:
            sp = sum(1 for r in small if r.passed)
            parts.append(f"small {sp}/{len(small)}")
        print(f"    {_variant_tooling(variant_id)}: {', '.join(parts)}")


def new_matrix_report(
    commit_sha: str,
    matrix_path: str,
    matrix_name: str,
    cases_path: str,
) -> MatrixReport:
    return MatrixReport(
        commit_sha=commit_sha,
        timestamp=now_iso(),
        matrix_path=matrix_path,
        matrix_name=matrix_name,
        cases_path=cases_path,
    )
