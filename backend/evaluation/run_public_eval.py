"""Backward-compatible imports for the original public evaluation command."""

from __future__ import annotations

from .run_eval import (
    CASES_PATH,
    DOCUMENTS_DIR,
    EVALUATION_ROOT,
    PublicEvalCase,
    _normal_query,
    evaluate_cases,
    load_cases,
    main as unified_main,
    run_isolated_eval,
    score_case,
)


async def run_isolated_public_eval(cases: list[PublicEvalCase]) -> dict[str, object]:
    """Preserve the previous helper while using the unified implementation."""
    return await run_isolated_eval(cases, "public", DOCUMENTS_DIR)


def main() -> None:
    """Keep ``python -m evaluation.run_public_eval`` working for old scripts."""
    unified_main()


__all__ = [
    "CASES_PATH",
    "DOCUMENTS_DIR",
    "EVALUATION_ROOT",
    "PublicEvalCase",
    "_normal_query",
    "evaluate_cases",
    "load_cases",
    "run_isolated_public_eval",
    "score_case",
]


if __name__ == "__main__":
    main()
