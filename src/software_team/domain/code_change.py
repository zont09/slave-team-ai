from enum import StrEnum

from typing import Self

from pydantic import Field, model_validator

from software_team.domain.base import DomainModel
from software_team.domain.technical_plan import ChangeType


class CodeChangeStatus(StrEnum):
    """Trạng thái tổng thể của quá trình triển khai code."""

    COMPLETED = "completed"
    PARTIALLY_COMPLETED = "partially_completed"
    FAILED = "failed"


class CommandStatus(StrEnum):
    """Trạng thái của một command đã được thực thi."""

    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


class IssueSeverity(StrEnum):
    """Mức độ nghiêm trọng của vấn đề phát sinh."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    BLOCKER = "blocker"


class FileChange(DomainModel):
    """Một thay đổi thực tế đã xảy ra trên file."""

    path: str = Field(
        min_length=1,
        description="Đường dẫn tương đối của file trong repository.",
    )

    change_type: ChangeType = Field(
        description="File được tạo, sửa hay xóa.",
    )

    summary: str = Field(
        min_length=1,
        description="Tóm tắt thay đổi được thực hiện.",
    )

    related_steps: list[str] = Field(
        default_factory=list,
        description="Các implementation step liên quan đến thay đổi này.",
    )

    related_acceptance_criteria: list[str] = Field(
        default_factory=list,
        description="Các acceptance criterion được hỗ trợ bởi thay đổi này.",
    )


class CommandExecution(DomainModel):
    """Kết quả của một command được Coding Agent chạy."""

    command: str = Field(
        min_length=1,
        description="Command đã được thực thi.",
    )

    status: CommandStatus = Field(
        description="Trạng thái thực thi command.",
    )

    exit_code: int | None = Field(
        default=None,
        description="Exit code của command, nếu command thực sự được chạy.",
    )

    stdout: str = Field(
        default="",
        description="Nội dung standard output.",
    )

    stderr: str = Field(
        default="",
        description="Nội dung standard error.",
    )

    purpose: str = Field(
        min_length=1,
        description="Mục đích chạy command.",
    )

    @model_validator(mode="after")
    def validate_status_and_exit_code(self) -> Self:
        if self.status == CommandStatus.SUCCESS and self.exit_code != 0:
            raise ValueError(
                "A successful command must have exit_code equal to 0."
            )

        if self.status == CommandStatus.FAILED:
            if self.exit_code is None or self.exit_code == 0:
                raise ValueError(
                    "A failed command must have a non-zero exit_code."
                )

        if self.status == CommandStatus.SKIPPED and self.exit_code is not None:
            raise ValueError(
                "A skipped command must not have an exit_code."
            )

        return self


class ImplementationIssue(DomainModel):
    """Một vấn đề được phát hiện trong quá trình triển khai."""

    issue_id: str = Field(
        min_length=1,
        description="Mã định danh vấn đề, ví dụ ISSUE-001.",
    )

    severity: IssueSeverity = Field(
        description="Mức độ nghiêm trọng.",
    )

    description: str = Field(
        min_length=1,
        description="Mô tả vấn đề.",
    )

    impact: str = Field(
        min_length=1,
        description="Ảnh hưởng của vấn đề đến feature hoặc hệ thống.",
    )

    resolution: str | None = Field(
        default=None,
        description="Cách xử lý nếu vấn đề đã được giải quyết.",
    )

    blocking: bool = Field(
        default=False,
        description="Vấn đề có chặn việc hoàn thành feature hay không.",
    )


class CodeChangeResult(DomainModel):
    """Kết quả có cấu trúc được tạo bởi Coding Agent."""

    version: int = Field(
        default=1,
        ge=1,
        description="Phiên bản của artifact.",
    )

    status: CodeChangeStatus = Field(
        description="Trạng thái tổng thể của quá trình coding.",
    )

    summary: str = Field(
        min_length=1,
        description="Tóm tắt kết quả triển khai.",
    )

    file_changes: list[FileChange] = Field(
        default_factory=list,
        description="Danh sách file thực tế đã thay đổi.",
    )

    commands: list[CommandExecution] = Field(
        default_factory=list,
        description="Danh sách command đã được thực thi.",
    )

    completed_steps: list[str] = Field(
        default_factory=list,
        description="Các implementation step đã hoàn thành.",
    )

    incomplete_steps: list[str] = Field(
        default_factory=list,
        description="Các implementation step chưa hoàn thành.",
    )

    issues: list[ImplementationIssue] = Field(
        default_factory=list,
        description="Các vấn đề phát sinh trong quá trình triển khai.",
    )

    assumptions: list[str] = Field(
        default_factory=list,
        description="Các giả định Coding Agent đã sử dụng.",
    )

    handoff_notes: list[str] = Field(
        default_factory=list,
        description="Ghi chú dành cho Tester, Reviewer hoặc người bàn giao.",
    )

    @model_validator(mode="after")
    def validate_result_consistency(self) -> Self:
        completed = set(self.completed_steps)
        incomplete = set(self.incomplete_steps)

        overlapping_steps = completed & incomplete

        if overlapping_steps:
            overlapping = ", ".join(sorted(overlapping_steps))
            raise ValueError(
                f"Steps cannot be both completed and incomplete: {overlapping}"
            )

        if (
            self.status == CodeChangeStatus.COMPLETED
            and self.incomplete_steps
        ):
            raise ValueError(
                "A completed result cannot contain incomplete steps."
            )

        if (
            self.status == CodeChangeStatus.PARTIALLY_COMPLETED
            and not self.incomplete_steps
        ):
            raise ValueError(
                "A partially completed result must contain incomplete steps."
            )

        return self