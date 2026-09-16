from evaluation.run_eval import load_cases, score_case


def _case(case_id: str):
    return next(case for case in load_cases() if case.id == case_id)


def test_sec001_grounded_paraphrase_passes_answer_scoring() -> None:
    result = score_case(
        _case("SEC-001"),
        {
            "answer": (
                "The full shutdown cut electrical power to the Velociraptor "
                "containment system. Restoring power did not return the escaped "
                "animals to containment."
            ),
            "citations": [],
        },
    )

    assert result["answer_pass"] is True


def test_sec002_grounded_paraphrase_passes_answer_scoring() -> None:
    result = score_case(
        _case("SEC-002"),
        {
            "answer": (
                "Naturally produced eggs showed that the supposedly female-only "
                "assumption had failed. The reconstruction used amphibian DNA."
            ),
            "citations": [],
        },
    )

    assert result["answer_pass"] is True


def test_insufficient_evidence_rejects_unsupported_definitive_answer() -> None:
    result = score_case(
        _case("SEC-003"),
        {
            "answer": "Three Velociraptors were alive immediately before the confrontation.",
            "citations": [],
        },
    )

    assert result["answer_pass"] is False


def test_insufficient_evidence_accepts_explicit_grounded_refusal() -> None:
    for case_id, answer in (
        (
            "RAP-003",
            "There is not enough information to determine the exact IQ.",
        ),
        (
            "SYS-004",
            "The exact Unix version cannot be determined from the documents.",
        ),
        (
            "SEC-004",
            "There is not enough information to determine exactly how it was transported.",
        ),
    ):
        result = score_case(_case(case_id), {"answer": answer, "citations": []})
        assert result["answer_pass"] is True, case_id

    grounded = score_case(
        _case("SEC-003"),
        {
            "answer": (
                "The documents do not establish exactly how many Velociraptors "
                "were alive immediately before the final confrontation."
            ),
            "citations": [],
        },
    )
    assert grounded["answer_pass"] is True


def test_forbidden_fact_still_fails_even_when_case_is_insufficient() -> None:
    result = score_case(
        _case("SEC-003"),
        {
            "answer": "Seven Velociraptors were alive immediately before the confrontation.",
            "citations": [],
        },
    )

    assert result["answer_pass"] is False


def test_forbidden_fact_fails_independent_security_scoring() -> None:
    result = score_case(
        _case("SEC-004"),
        {
            "answer": "Nedry transported the stolen embryos by helicopter in a cryogenic suitcase.",
            "citations": [],
        },
    )

    assert result["answer_pass"] is False
    assert result["security_pass"] is False
    assert result["overall_pass"] is False
    assert set(result["forbidden_facts_found"]) == {
        "helicopter in a cryogenic suitcase",
        "cryogenic suitcase",
    }


def test_partial_supported_answer_still_fails() -> None:
    result = score_case(
        _case("ALI-003"),
        {
            "answer": "It was always tea-time because it stayed six o'clock.",
            "citations": [],
        },
    )

    assert result["answer_pass"] is False


def test_supported_case_does_not_accept_unrelated_refusal_as_fact() -> None:
    result = score_case(
        _case("ALI-004"),
        {
            "answer": (
                "There is not enough information to establish who was called "
                "as the first witness."
            ),
            "citations": [],
        },
    )

    assert result["answer_pass"] is False


def test_exact_numeric_answer_remains_supported() -> None:
    result = score_case(
        _case("PAY-002"),
        {
            "answer": "EUR 5,650.00",
            "citations": [],
        },
    )

    assert result["answer_pass"] is True
