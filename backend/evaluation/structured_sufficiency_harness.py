"""Temporary, read-only cohort and deterministic target support for this experiment."""
from __future__ import annotations

from typing import Any

from evaluation.run_eval import EVALUATION_ROOT, load_cases

EXPERIMENT_CASES = EVALUATION_ROOT / "structured_sufficiency_cases.jsonl"
ALICE_TARGETS = {
    "ALI-001": ["took a watch out of its waistcoat-pocket"],
    "ALI-002": ["One side will make you grow taller, and the other side will make you grow shorter."],
    "ALI-003": ["We quarrelled last March", "he won’t do a thing I ask! It’s always six o’clock now.", "it’s always tea-time"],
    "ALI-004": ["The first witness was the Hatter."],
    "ALI-005": ["took a watch out of its waistcoat-pocket"],
    "ALI-006": ["a White Rabbit with pink eyes ran close by her"],
    "ALI-007": ["she found herself falling down a very deep well"],
    "ALI-008": ["The Rabbit started violently, dropped the white kid gloves and the fan"],
    "ALI-009": ["the Dodo solemnly presented the thimble"],
    "ALI-010": ["it was neither more nor less than a pig"],
    "ALI-011": ["she put them into a large flower-pot that stood near"],
    "ALI-012": ["We called him Tortoise because he taught us"],
    "ALI-013": ["being made entirely of cardboard"],
    "ALI-014": ["No, they’re not,’ said the White Rabbit", "there’s no name signed at the end."],
}

TRACE_FIELDS = frozenset({"normal_decision", "normal_answer", "normal_evidence_ids", "rescue_triggered", "rescue_result", "selected_context_ids", "reranked_atomic_ids", "extraction_records", "validation_results", "verified_spans_reaching_generation", "final_citations", "first_loss_stage"})

def fixed_cases() -> list[Any]:
    base = load_cases()
    alice = [case for case in base if case.id.startswith("ALI-")]
    short = [case for case in base if not case.id.startswith("ALI-")]
    additions = load_cases(EXPERIMENT_CASES)
    if [case.id for case in alice] != [f"ALI-{index:03d}" for index in range(1, 8)]:
        raise ValueError("canonical Alice cohort changed")
    if len(short) != 16 or len(additions) != 7:
        raise ValueError("fixed experimental cohort is incomplete")
    return alice + additions + short

def missing_targets(chunks: list[str]) -> list[str]:
    corpus = "\n".join(chunks)
    return [target for targets in ALICE_TARGETS.values() for target in targets if target not in corpus]

def trace_payload(**values: Any) -> dict[str, Any]:
    payload = {field: None for field in TRACE_FIELDS}
    payload.update(values)
    return payload
