from enum import StrEnum
from typing import Self

from pydantic import Field, model_validator

from software_team.domain.base import DomainModel
from software_team.domain.code_change import CommandExecution


class TestExecutionStatus(StrEnum):
    """Trạng thái tổng thể của quá trình kiểm thử."""

    PASSED = "passed"
    FAILED = "failed"
    PARTIALLY_PASSED = "partially_passed"
    BLOCKED = "blocked"


class TestCaseStatus(StrEnum):
    """Trạng thái của một test case riêng lẻ."""

    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


class AcceptanceStatus(StrEnum):
    """Trạng thái kiểm chứng của một acceptance criterion."""

    PASSED = "passed"
    FAILED = "failed"
    NOT_TESTED = "not_tested"
    BLOCKED = "blocked"


class TestCaseResult(DomainModel):
    """Kết quả thực thi của một test case."""

    test_id: str = Field(
        min_length=1,
        description="Mã định danh test, ví dụ TEST-001.",
    )

    name: str = Field(
        min_length=1,
        description="Tên test case.",
    )

    test_type: str = Field(
        min_length=1,
        description="Loại test: unit, integration, contract hoặc end-to-end.",
    )

    status: TestCaseStatus = Field(
        description="Kết quả thực thi test case.",
    )

    duration_seconds: float | None = Field(
        default=None,
        ge=0,
        description="Thời gian chạy test tính bằng giây.",
    )

    related_acceptance_criteria: list[str] = Field(
        default_factory=list,
        description="Các acceptance criterion được test case kiểm chứng.",
    )

    details: str = Field(
        default="",
        description="Thông tin bổ sung về kết quả test.",
    )


class TestFailure(DomainModel):
    """Một lỗi hoặc failure được phát hiện khi kiểm thử."""

    failure_id: str = Field(
        min_length=1,
        description="Mã định danh failure, ví dụ FAILURE-001.",
    )

    test_id: str | None = Field(
        default=None,
        description="Test case phát hiện failure, nếu có.",
    )

    title: str = Field(
        min_length=1,
        description="Tên ngắn gọn của failure.",
    )

    description: str = Field(
        min_length=1,
        description="Mô tả failure.",
    )

    expected_result: str = Field(
        min_length=1,
        description="Kết quả mong đợi.",
    )

    actual_result: str = Field(
        min_length=1,
        description="Kết quả thực tế.",
    )

    reproducible: bool = Field(
        default=True,
        description="Failure có thể tái hiện ổn định hay không.",
    )

    related_files: list[str] = Field(
        default_factory=list,
        description="Các file có thể liên quan đến failure.",
    )

    related_acceptance_criteria: list[str] = Field(
        default_factory=list,
        description="Các acceptance criterion bị ảnh hưởng.",
    )


class CoverageSummary(DomainModel):
    """Tóm tắt code coverage của lần kiểm thử."""

    lines_percent: float | None = Field(
        default=None,
        ge=0,
        le=100,
        description="Phần trăm line coverage.",
    )

    branches_percent: float | None = Field(
        default=None,
        ge=0,
        le=100,
        description="Phần trăm branch coverage.",
    )

    functions_percent: float | None = Field(
        default=None,
        ge=0,
        le=100,
        description="Phần trăm function coverage.",
    )

    measured_command: str | None = Field(
        default=None,
        description="Command được dùng để đo coverage.",
    )


class AcceptanceCriterionResult(DomainModel):
    """Kết quả kiểm chứng của một acceptance criterion."""

    criterion_id: str = Field(
        min_length=1,
        description="Mã acceptance criterion, ví dụ AC-001.",
    )

    status: AcceptanceStatus = Field(
        description="Trạng thái kiểm chứng criterion.",
    )

    evidence: list[str] = Field(
        default_factory=list,
        description="Các test ID hoặc bằng chứng hỗ trợ kết luận.",
    )

    notes: str = Field(
        default="",
        description="Giải thích thêm về kết quả.",
    )

    @model_validator(mode="after")
    def validate_evidence(self) -> Self:
        if (
            self.status == AcceptanceStatus.PASSED
            and not self.evidence
        ):
            raise ValueError(
                "A passed acceptance criterion must contain evidence."
            )

        if (
            self.status == AcceptanceStatus.FAILED
            and not self.evidence
            and not self.notes
        ):
            raise ValueError(
                "A failed acceptance criterion must contain evidence or notes."
            )

        return self


class TestExecutionResult(DomainModel):
    """Artifact đầu ra của Tester Agent."""

    version: int = Field(
        default=1,
        ge=1,
        description="Phiên bản artifact.",
    )

    status: TestExecutionStatus = Field(
        description="Trạng thái tổng thể của quá trình kiểm thử.",
    )

    summary: str = Field(
        min_length=1,
        description="Tóm tắt kết quả kiểm thử.",
    )

    test_cases: list[TestCaseResult] = Field(
        default_factory=list,
        description="Danh sách kết quả test case.",
    )

    commands: list[CommandExecution] = Field(
        default_factory=list,
        description="Các command đã chạy để kiểm thử.",
    )

    failures: list[TestFailure] = Field(
        default_factory=list,
        description="Các failure được phát hiện.",
    )

    acceptance_results: list[AcceptanceCriterionResult] = Field(
        default_factory=list,
        description="Kết quả theo từng acceptance criterion.",
    )

    coverage: CoverageSummary | None = Field(
        default=None,
        description="Thông tin coverage nếu được đo.",
    )

    environment_notes: list[str] = Field(
        default_factory=list,
        description="Thông tin và giới hạn của môi trường test.",
    )

    recommendations: list[str] = Field(
        default_factory=list,
        description="Các đề xuất sau quá trình kiểm thử.",
    )

    @model_validator(mode="after")
    def validate_result_consistency(self) -> Self:
        test_ids = [test.test_id for test in self.test_cases]

        if len(test_ids) != len(set(test_ids)):
            raise ValueError(
                "test_cases must not contain duplicate test IDs."
            )

        criterion_ids = [
            result.criterion_id
            for result in self.acceptance_results
        ]

        if len(criterion_ids) != len(set(criterion_ids)):
            raise ValueError(
                "acceptance_results must not contain duplicate criterion IDs."
            )

        failed_tests = [
            test
            for test in self.test_cases
            if test.status in {
                TestCaseStatus.FAILED,
                TestCaseStatus.ERROR,
            }
        ]

        passed_tests = [
            test
            for test in self.test_cases
            if test.status == TestCaseStatus.PASSED
        ]

        if self.status == TestExecutionStatus.PASSED:
            if failed_tests:
                raise ValueError(
                    "A passed test execution cannot contain failed or error tests."
                )

            if self.failures:
                raise ValueError(
                    "A passed test execution cannot contain failures."
                )

        if self.status == TestExecutionStatus.FAILED and not (
            failed_tests or self.failures
        ):
            raise ValueError(
                "A failed test execution must contain a failed test or failure."
            )

        if self.status == TestExecutionStatus.PARTIALLY_PASSED:
            if not passed_tests or not failed_tests:
                raise ValueError(
                    "A partially passed execution must contain both passed "
                    "and failed or error tests."
                )

        return self