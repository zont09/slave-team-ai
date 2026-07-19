from enum import StrEnum

from pydantic import Field, model_validator
from typing_extensions import Self

from software_team.domain.base import DomainModel


class ValidationSeverity(StrEnum):
    """Mức độ nghiêm trọng của một quality-gate issue."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    BLOCKER = "blocker"


class ValidationIssueCode(StrEnum):
    """Mã lỗi chuẩn hóa của quality gate."""

    UNKNOWN_ACCEPTANCE_CRITERION = "unknown_acceptance_criterion"
    UNPLANNED_ACCEPTANCE_CRITERION = "unplanned_acceptance_criterion"
    DUPLICATE_REFERENCE = "duplicate_reference"
    INVALID_REFERENCE = "invalid_reference"


class ValidationIssue(DomainModel):
    """Một vấn đề được quality gate phát hiện."""

    code: ValidationIssueCode = Field(
        description="Mã lỗi có thể được workflow xử lý bằng chương trình.",
    )

    severity: ValidationSeverity = Field(
        description="Mức độ nghiêm trọng của vấn đề.",
    )

    message: str = Field(
        min_length=1,
        description="Thông báo dễ đọc dành cho agent hoặc người dùng.",
    )

    source_artifact: str = Field(
        min_length=1,
        description="Artifact chứa dữ liệu không hợp lệ.",
    )

    source_field: str | None = Field(
        default=None,
        description="Field hoặc đường dẫn field gây ra lỗi.",
    )

    reference_id: str | None = Field(
        default=None,
        description="ID không hợp lệ hoặc bị thiếu.",
    )

    related_artifact: str | None = Field(
        default=None,
        description="Artifact được dùng để đối chiếu.",
    )

    blocking: bool = Field(
        default=True,
        description="Issue có chặn workflow hay không.",
    )


class ValidationResult(DomainModel):
    """Kết quả chuẩn hóa của một quality gate."""

    gate_name: str = Field(
        min_length=1,
        description="Tên quality gate.",
    )

    passed: bool = Field(
        description="Quality gate có pass hay không.",
    )

    issues: list[ValidationIssue] = Field(
        default_factory=list,
        description="Các vấn đề được phát hiện.",
    )

    checked_rules: list[str] = Field(
        default_factory=list,
        description="Các rule đã được thực thi.",
    )

    @model_validator(mode="after")
    def validate_result_consistency(self) -> Self:
        blocking_issues = [
            issue
            for issue in self.issues
            if issue.blocking
        ]

        if self.passed and blocking_issues:
            raise ValueError(
                "A passed validation result cannot contain blocking issues."
            )

        if not self.passed and not blocking_issues:
            raise ValueError(
                "A failed validation result must contain a blocking issue."
            )

        return self

    