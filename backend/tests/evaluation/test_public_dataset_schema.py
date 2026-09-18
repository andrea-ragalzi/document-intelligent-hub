from evaluation.run_public_eval import CASES_PATH, load_cases


def test_public_dataset_has_exactly_twenty_three_unique_valid_cases() -> None:
    cases = load_cases(CASES_PATH)

    assert len(cases) == 23
    assert len({case.id for case in cases}) == 23
    assert all(case.question.strip() for case in cases)
    assert all(case.expected_evidence for case in cases)
    assert all(case.tags for case in cases)


def test_supported_and_insufficient_cases_define_objective_expectations() -> None:
    cases = load_cases(CASES_PATH)

    for case in cases:
        if case.answer_mode == "supported":
            assert case.expected_facts, case.id
        else:
            assert case.answer_mode == "insufficient_evidence"
            assert case.forbidden_facts, case.id


def test_security_cases_define_explicit_forbidden_outputs() -> None:
    cases = load_cases(CASES_PATH)
    security_cases = [case for case in cases if "security" in case.tags]

    assert {case.id for case in security_cases} == {
        "SEC-001",
        "SEC-002",
        "SEC-003",
        "SEC-004",
    }
    assert all(case.forbidden_facts for case in security_cases)
    assert all(case.forbidden_markers for case in security_cases)
