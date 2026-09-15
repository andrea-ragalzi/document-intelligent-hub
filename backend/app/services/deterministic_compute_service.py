"""Bounded arithmetic over already validated source evidence."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from app.services.deterministic_evidence_service import GroundedEvidence
from app.services.query_routing_service import ComputeOperation


@dataclass(frozen=True)
class ComputeResult:
    value: Decimal | int | list[Decimal] | int
    evidence: list[GroundedEvidence]


class DeterministicComputeService:
    """Explicit operations only. No evaluation of user-provided expressions."""

    def compute(
        self, operation: ComputeOperation, values: list[Decimal], evidence: list[GroundedEvidence]
    ) -> ComputeResult:
        if not evidence or len(values) != len(evidence):
            raise ValueError("validated evidence is required for every value")
        if operation is ComputeOperation.COUNT:
            return ComputeResult(len(values), evidence)
        if operation is ComputeOperation.SUM:
            return ComputeResult(sum(values, Decimal("0")), evidence)
        if operation is ComputeOperation.DIFFERENCE and len(values) == 2:
            return ComputeResult(values[0] - values[1], evidence)
        if operation is ComputeOperation.AVERAGE:
            return ComputeResult(sum(values, Decimal("0")) / len(values), evidence)
        if operation is ComputeOperation.PERCENTAGE and len(values) == 2 and values[1] != 0:
            return ComputeResult(values[0] * Decimal("100") / values[1], evidence)
        if operation is ComputeOperation.MIN:
            return ComputeResult(min(values), evidence)
        if operation is ComputeOperation.MAX:
            return ComputeResult(max(values), evidence)
        if operation is ComputeOperation.SORT:
            return ComputeResult(sorted(values), evidence)
        raise ValueError("unsupported operation or invalid operands")

    @staticmethod
    def date_difference(first: date, second: date, evidence: list[GroundedEvidence]) -> ComputeResult:
        if len(evidence) != 2:
            raise ValueError("validated evidence is required for every value")
        return ComputeResult(abs((first - second).days), evidence)
