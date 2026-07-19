from pydantic import Field

from software_team.domain.base import DomainModel


class AcceptanceCriterion(DomainModel):
    """Một điều kiện dùng để xác định requirement đã hoàn thành hay chưa."""

    criterion_id: str = Field(
        min_length=1,
        description="Mã định danh của acceptance criterion, ví dụ AC-001.",
    )

    description: str = Field(
        min_length=1,
        description="Điều kiện có thể kiểm chứng để chấp nhận tính năng.",
    )


class RequirementSpec(DomainModel):
    """Đặc tả nghiệp vụ đã được chuẩn hóa từ yêu cầu của người dùng."""

    version: int = Field(
        default=1,
        ge=1,
        description="Phiên bản của requirement.",
    )

    title: str = Field(
        min_length=1,
        max_length=200,
        description="Tên ngắn gọn của tính năng.",
    )

    summary: str = Field(
        min_length=1,
        description="Tóm tắt requirement.",
    )

    business_goal: str = Field(
        min_length=1,
        description="Mục tiêu nghiệp vụ cần đạt được.",
    )

    in_scope: list[str] = Field(
        default_factory=list,
        description="Những nội dung nằm trong phạm vi triển khai.",
    )

    out_of_scope: list[str] = Field(
        default_factory=list,
        description="Những nội dung không nằm trong phạm vi triển khai.",
    )

    functional_requirements: list[str] = Field(
        default_factory=list,
        description="Các hành vi mà hệ thống phải thực hiện.",
    )

    non_functional_requirements: list[str] = Field(
        default_factory=list,
        description="Các yêu cầu về hiệu năng, bảo mật và chất lượng.",
    )

    acceptance_criteria: list[AcceptanceCriterion] = Field(
        default_factory=list,
        description="Các điều kiện dùng để nghiệm thu tính năng.",
    )

    assumptions: list[str] = Field(
        default_factory=list,
        description="Các giả định được sử dụng khi phân tích.",
    )

    constraints: list[str] = Field(
        default_factory=list,
        description="Các giới hạn kỹ thuật hoặc nghiệp vụ.",
    )

    open_questions: list[str] = Field(
        default_factory=list,
        description="Các câu hỏi chưa đủ thông tin để kết luận.",
    )