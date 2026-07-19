import pytest
from pydantic import ValidationError

from software_team.domain import (
    AcceptanceCriterionResult,
    AcceptanceStatus,
    CoverageSummary,
    TestCaseResult as CaseResult,
    TestCaseStatus as CaseStatus,
    TestExecutionResult as ExecutionResult,
    TestExecutionStatus as ExecutionStatus,
    TestFailure as FailureResult,
)


def test_create_passed_test_execution_result() -> None:
    result = ExecutionResult(
        status=ExecutionStatus.PASSED,
        summary="Toàn bộ test đã pass.",
        test_cases=[
            CaseResult(
                test_id="TEST-001",
                name="Login with valid credentials",
                test_type="integration",
                status=CaseStatus.PASSED,
                duration_seconds=0.2,
                related_acceptance_criteria=["AC-001"],
            )
        ],
        acceptance_results=[
            AcceptanceCriterionResult(
                criterion_id="AC-001",
                status=AcceptanceStatus.PASSED,
                evidence=["TEST-001"],
            )
        ],
        coverage=CoverageSummary(
            lines_percent=90,
            branches_percent=80,
        ),
    )

    assert result.version == 1
    assert result.status == ExecutionStatus.PASSED
    assert result.test_cases[0].status == CaseStatus.PASSED
    assert result.coverage is not None
    assert result.coverage.lines_percent == 90


def test_create_failed_test_execution_result() -> None:
    result = ExecutionResult(
        status=ExecutionStatus.FAILED,
        summary="Login test thất bại.",
        test_cases=[
            CaseResult(
                test_id="TEST-001",
                name="Login with valid credentials",
                test_type="integration",
                status=CaseStatus.FAILED,
            )
        ],
        failures=[
            FailureResult(
                failure_id="FAILURE-001",
                test_id="TEST-001",
                title="Login trả sai status code",
                description="API trả về 500.",
                expected_result="API trả về 200.",
                actual_result="API trả về 500.",
                related_acceptance_criteria=["AC-001"],
            )
        ],
    )

    assert result.status == ExecutionStatus.FAILED
    assert len(result.failures) == 1
    assert result.failures[0].reproducible is True


def test_create_partially_passed_result() -> None:
    result = ExecutionResult(
        status=ExecutionStatus.PARTIALLY_PASSED,
        summary="Unit test pass nhưng integration test fail.",
        test_cases=[
            CaseResult(
                test_id="TEST-001",
                name="Validate login schema",
                test_type="unit",
                status=CaseStatus.PASSED,
            ),
            CaseResult(
                test_id="TEST-002",
                name="Login integration",
                test_type="integration",
                status=CaseStatus.FAILED,
            ),
        ],
    )

    assert result.status == ExecutionStatus.PARTIALLY_PASSED


def test_create_blocked_result_without_test_cases() -> None:
    result = ExecutionResult(
        status=ExecutionStatus.BLOCKED,
        summary="Không thể chạy test vì database không khả dụng.",
        environment_notes=[
            "PostgreSQL test container không khởi động được.",
        ],
    )

    assert result.status == ExecutionStatus.BLOCKED
    assert result.test_cases == []


def test_reject_passed_result_with_failed_test() -> None:
    with pytest.raises(
        ValidationError,
        match="passed test execution cannot contain failed or error tests",
    ):
        ExecutionResult(
            status=ExecutionStatus.PASSED,
            summary="Test đã pass.",
            test_cases=[
                CaseResult(
                    test_id="TEST-001",
                    name="Login integration",
                    test_type="integration",
                    status=CaseStatus.FAILED,
                )
            ],
        )


def test_reject_passed_result_with_failure() -> None:
    with pytest.raises(
        ValidationError,
        match="passed test execution cannot contain failures",
    ):
        ExecutionResult(
            status=ExecutionStatus.PASSED,
            summary="Test đã pass.",
            failures=[
                FailureResult(
                    failure_id="FAILURE-001",
                    title="Unexpected error",
                    description="Có lỗi xảy ra.",
                    expected_result="Không có lỗi.",
                    actual_result="Có lỗi.",
                )
            ],
        )


def test_reject_failed_result_without_failure_evidence() -> None:
    with pytest.raises(
        ValidationError,
        match=(
            "failed test execution must contain a failed test or failure"
        ),
    ):
        ExecutionResult(
            status=ExecutionStatus.FAILED,
            summary="Kiểm thử thất bại.",
        )


def test_reject_partially_passed_without_failed_test() -> None:
    with pytest.raises(
        ValidationError,
        match=(
            "partially passed execution must contain both passed "
            "and failed or error tests"
        ),
    ):
        ExecutionResult(
            status=ExecutionStatus.PARTIALLY_PASSED,
            summary="Kiểm thử hoàn thành một phần.",
            test_cases=[
                CaseResult(
                    test_id="TEST-001",
                    name="Unit test",
                    test_type="unit",
                    status=CaseStatus.PASSED,
                )
            ],
        )


def test_reject_duplicate_test_ids() -> None:
    with pytest.raises(
        ValidationError,
        match="test_cases must not contain duplicate test IDs",
    ):
        ExecutionResult(
            status=ExecutionStatus.PASSED,
            summary="Test hoàn thành.",
            test_cases=[
                CaseResult(
                    test_id="TEST-001",
                    name="First test",
                    test_type="unit",
                    status=CaseStatus.PASSED,
                ),
                CaseResult(
                    test_id="TEST-001",
                    name="Second test",
                    test_type="unit",
                    status=CaseStatus.PASSED,
                ),
            ],
        )


def test_reject_duplicate_acceptance_criterion_results() -> None:
    with pytest.raises(
        ValidationError,
        match=(
            "acceptance_results must not contain duplicate criterion IDs"
        ),
    ):
        ExecutionResult(
            status=ExecutionStatus.PASSED,
            summary="Test hoàn thành.",
            acceptance_results=[
                AcceptanceCriterionResult(
                    criterion_id="AC-001",
                    status=AcceptanceStatus.PASSED,
                ),
                AcceptanceCriterionResult(
                    criterion_id="AC-001",
                    status=AcceptanceStatus.NOT_TESTED,
                ),
            ],
        )


def test_reject_coverage_above_one_hundred_percent() -> None:
    with pytest.raises(ValidationError):
        CoverageSummary(
            lines_percent=105,
        )


def test_strip_whitespace_from_test_execution_fields() -> None:
    result = ExecutionResult(
        status=ExecutionStatus.PASSED,
        summary="   Toàn bộ test đã pass.   ",
    )

    assert result.summary == "Toàn bộ test đã pass."