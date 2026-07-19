import pytest
from pydantic import ValidationError

from software_team.quality_gates import (
    ValidationIssue,
    ValidationIssueCode,
    ValidationResult,
    ValidationSeverity,
)


def create_blocking_issue() -> ValidationIssue:
    return ValidationIssue(
        code=ValidationIssueCode.INVALID_REFERENCE,
        severity=ValidationSeverity.ERROR,
        message="Invalid reference.",
        source_artifact="TechnicalPlan",
        blocking=True,
    )


def test_create_passed_validation_result() -> None:
    result = ValidationResult(
        gate_name="example_gate",
        passed=True,
        checked_rules=["rule_one"],
    )

    assert result.passed is True
    assert result.issues == []


def test_create_failed_validation_result() -> None:
    result = ValidationResult(
        gate_name="example_gate",
        passed=False,
        issues=[create_blocking_issue()],
    )

    assert result.passed is False
    assert len(result.issues) == 1


def test_reject_passed_result_with_blocking_issue() -> None:
    with pytest.raises(
        ValidationError,
        match=(
            "passed validation result cannot contain blocking issues"
        ),
    ):
        ValidationResult(
            gate_name="example_gate",
            passed=True,
            issues=[create_blocking_issue()],
        )


def test_reject_failed_result_without_blocking_issue() -> None:
    with pytest.raises(
        ValidationError,
        match=(
            "failed validation result must contain a blocking issue"
        ),
    ):
        ValidationResult(
            gate_name="example_gate",
            passed=False,
            issues=[
                ValidationIssue(
                    code=ValidationIssueCode.INVALID_REFERENCE,
                    severity=ValidationSeverity.WARNING,
                    message="Non-blocking warning.",
                    source_artifact="TechnicalPlan",
                    blocking=False,
                )
            ],
        )