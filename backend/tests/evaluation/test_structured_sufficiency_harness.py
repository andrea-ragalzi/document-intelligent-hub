from evaluation.structured_sufficiency_harness import ALICE_TARGETS, TRACE_FIELDS, fixed_cases, trace_payload

def test_fixed_experiment_cohorts_are_complete() -> None:
    cases = fixed_cases()
    assert [case.id for case in cases[:14]] == [f"ALI-{index:03d}" for index in range(1, 15)]
    assert len(cases) == 30

def test_trace_contract_is_read_only_and_complete() -> None:
    assert set(trace_payload()) == TRACE_FIELDS
    assert len(ALICE_TARGETS) == 14
