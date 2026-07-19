from enum import StrEnum
from typing import Self

from pydantic import Field, model_validator

from software_team.domain.base import DomainModel

class ReviewDecision(StrEnum):
    """Quyết định tổng thể của Reviewer Agent."""

    APPROVED = "approved"
    APPROVED_WITH_NOTES = "approved_with_notes"
    CHANGES_REQUESTED = "changes_requested"
    REJECTED = "rejected"


class ReviewSeverity(StrEnum):
    """Mức độ nghiêm trọng của một review finding."""

    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    BLOCKER = "blocker"


class ReviewCategory(StrEnum):
    """Nhóm vấn đề được phát hiện khi review."""

    REQUIREMENT = "requirement"
    ARCHITECTURE = "architecture"
    IMPLEMENTATION = "implementation"
    SECURITY = "security"
    PERFORMANCE = "performance"
    TESTING = "testing"
    MAINTAINABILITY = "maintainability"
    DOCUMENTATION = "documentation"
    CONSISTENCY = "consistency"


class FindingStatus(StrEnum):
    """Trạng thái xử lý của một review finding."""

    OPEN = "open"
    RESOLVED = "resolved"
    ACCEPTED_RISK = "accepted_risk"

class ReviewFinding(DomainModel):
    """Một vấn đề hoặc nhận xét được phát hiện khi review."""

    finding_id: str = Field(
        min_length=1,
        description="Mã finding, ví dụ REVIEW-001.",
    )

    title: str = Field(
        min_length=1,
        description="Tiêu đề ngắn gọn của finding.",
    )

    description: str = Field(
        min_length=1,
        description="Mô tả chi tiết vấn đề.",
    )

    category: ReviewCategory = Field(
        description="Nhóm vấn đề.",
    )

    severity: ReviewSeverity = Field(
        description="Mức độ nghiêm trọng.",
    )

    status: FindingStatus = Field(
        default=FindingStatus.OPEN,
        description="Trạng thái xử lý finding.",
    )

    file_path: str | None = Field(
        default=None,
        description="File liên quan nếu xác định được.",
    )

    line_number: int | None = Field(
        default=None,
        ge=1,
        description="Dòng code liên quan nếu xác định được.",
    )

    related_steps: list[str] = Field(
        default_factory=list,
        description="Implementation step liên quan.",
    )

    related_acceptance_criteria: list[str] = Field(
        default_factory=list,
        description="Acceptance criterion bị ảnh hưởng.",
    )

    recommendation: str = Field(
        default="",
        description="Cách khắc phục hoặc cải tiến.",
    )

    blocking: bool = Field(
        default=False,
        description="Finding có chặn việc approve hay không.",
    )

    @model_validator(mode="after")
    def validate_location(self) -> Self:
        if self.line_number is not None and self.file_path is None:
            raise ValueError(
                "A finding with line_number must also contain file_path."
            )

        return self

    @model_validator(mode="after")
    def validate_finding_consistency(self) -> Self:
        if self.line_number is not None and self.file_path is None:
            raise ValueError(
                "A finding with line_number must also contain file_path."
            )

        if (
            self.severity == ReviewSeverity.BLOCKER
            and not self.blocking
        ):
            raise ValueError(
                "A blocker finding must have blocking set to true."
            )

        if (
            self.status == FindingStatus.RESOLVED
            and self.blocking
        ):
            raise ValueError(
                "A resolved finding cannot remain blocking."
            )

        return self

class ReviewResult(DomainModel):
    """Artifact đầu ra của Reviewer Agent."""

    version: int = Field(
        default=1,
        ge=1,
        description="Phiên bản artifact.",
    )

    decision: ReviewDecision = Field(
        description="Quyết định tổng thể sau review.",
    )

    summary: str = Field(
        min_length=1,
        description="Tóm tắt kết quả review.",
    )

    findings: list[ReviewFinding] = Field(
        default_factory=list,
        description="Các finding được phát hiện.",
    )

    required_changes: list[str] = Field(
        default_factory=list,
        description="Các thay đổi bắt buộc trước khi approve.",
    )

    suggestions: list[str] = Field(
        default_factory=list,
        description="Các cải tiến không bắt buộc.",
    )

    positive_observations: list[str] = Field(
        default_factory=list,
        description="Các điểm được triển khai tốt.",
    )

    residual_risks: list[str] = Field(
        default_factory=list,
        description="Các rủi ro vẫn còn sau review.",
    )

    reviewed_acceptance_criteria: list[str] = Field(
        default_factory=list,
        description="Các acceptance criterion đã được reviewer xem xét.",
    )

    reviewed_steps: list[str] = Field(
        default_factory=list,
        description="Các implementation step đã được reviewer xem xét.",
    )

    @model_validator(mode="after")
    def validate_review_consistency(self) -> Self:
        finding_ids = [
            finding.finding_id
            for finding in self.findings
        ]

        if len(finding_ids) != len(set(finding_ids)):
            raise ValueError(
                "findings must not contain duplicate finding IDs."
            )

        open_blocking_findings = [
            finding
            for finding in self.findings
            if finding.blocking
            and finding.status == FindingStatus.OPEN
        ]

        open_high_findings = [
            finding
            for finding in self.findings
            if finding.severity
            in {
                ReviewSeverity.HIGH,
                ReviewSeverity.BLOCKER,
            }
            and finding.status == FindingStatus.OPEN
        ]

        if self.decision == ReviewDecision.APPROVED:
            if open_blocking_findings:
                raise ValueError(
                    "An approved review cannot contain open blocking findings."
                )

            if open_high_findings:
                raise ValueError(
                    "An approved review cannot contain open high-severity findings."
                )

            if self.required_changes:
                raise ValueError(
                    "An approved review cannot contain required changes."
                )

        if self.decision == ReviewDecision.APPROVED_WITH_NOTES:
            if open_blocking_findings:
                raise ValueError(
                    "An approved-with-notes review cannot contain "
                    "open blocking findings."
                )

            if self.required_changes:
                raise ValueError(
                    "An approved-with-notes review cannot contain "
                    "required changes."
                )

        if self.decision == ReviewDecision.CHANGES_REQUESTED:
            if not self.required_changes and not open_blocking_findings:
                raise ValueError(
                    "A changes-requested review must contain required changes "
                    "or open blocking findings."
                )

        if self.decision == ReviewDecision.REJECTED:
            if not open_high_findings:
                raise ValueError(
                    "A rejected review must contain an open high-severity "
                    "or blocker finding."
                )

        return self