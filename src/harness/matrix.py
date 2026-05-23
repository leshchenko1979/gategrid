from __future__ import annotations

import argparse
import asyncio
import logging
import uuid
from pathlib import Path

from dotenv import load_dotenv

from harness.models import ExperimentVariant
from harness.observability import get_commit_sha, setup_observability
from harness.report import new_matrix_report, print_summary, write_aggregate_report
from harness.matrices import resolve_matrix
from harness.task import evaluate_case

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[2]
EXPERIMENTS = ROOT / "experiments"
DEFAULT_MATRIX = EXPERIMENTS / "matrices" / "full.yaml"
DEFAULT_CASES = EXPERIMENTS / "cases"


def filter_variants(
    variants: list[ExperimentVariant], variant_filter: str | None
) -> list[ExperimentVariant]:
    if not variant_filter:
        return variants
    return [v for v in variants if v.variant_id == variant_filter]


async def run_matrix(
    matrix_path: Path,
    cases_path: Path,
    variant_filter: str | None = None,
    trace: bool = False,
) -> int:
    setup_observability()
    load_dotenv(ROOT / ".env")

    matrix_path = matrix_path.resolve()
    resolved = resolve_matrix(matrix_path, EXPERIMENTS, cases_path.resolve())
    variants = filter_variants(resolved.variants, variant_filter)
    if not variants:
        raise ValueError(f"No variants matched filter: {variant_filter!r}")

    run_id = str(uuid.uuid4())[:8] if trace else None
    report = new_matrix_report(
        commit_sha=get_commit_sha(),
        matrix_path=resolved.matrix_path,
        matrix_name=resolved.matrix_name,
        cases_path=str(cases_path),
    )

    logger.info(
        "Running matrix %s: %d variants x %d cases",
        resolved.matrix_name,
        len(variants),
        len(resolved.cases),
    )

    for variant in variants:
        for case in resolved.cases:
            logger.info("Evaluating %s / %s", variant.variant_id, case.name)
            result = await evaluate_case(case, variant, run_id=run_id)
            report.results.append(result)

    write_aggregate_report(report)
    print_summary(report)

    failed = sum(1 for r in report.results if not r.passed)
    return 1 if failed else 0


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run file-editing eval matrix")
    sub = parser.add_subparsers(dest="command", required=True)

    run_parser = sub.add_parser("run", help="Run evaluation matrix")
    run_parser.add_argument(
        "--matrix",
        type=Path,
        default=None,
        help="Path to matrix YAML (default: experiments/matrices/full.yaml)",
    )
    run_parser.add_argument(
        "--cases",
        type=Path,
        default=DEFAULT_CASES,
        help="Path to cases directory",
    )
    run_parser.add_argument(
        "--variant",
        type=str,
        default=None,
        help="Run single variant id, e.g. baseline/minimax-m2.7",
    )
    run_parser.add_argument(
        "--trace",
        action="store_true",
        help="Write JSONL trace events under reports/traces/",
    )

    args = parser.parse_args(argv)
    if args.command == "run":
        matrix_path = args.matrix or DEFAULT_MATRIX
        code = asyncio.run(
            run_matrix(
                matrix_path=matrix_path,
                cases_path=args.cases,
                variant_filter=args.variant,
                trace=args.trace,
            )
        )
        raise SystemExit(code)


if __name__ == "__main__":
    main()
