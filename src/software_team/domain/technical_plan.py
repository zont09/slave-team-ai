from enum import StrEnum

from pydantic import Field

from software_team.domain.base import DomainModel


class ChangeType(StrEnum):
    """Loại thay đổi dự kiến trên một component."""

    CREATE = "create"
    MODIFY = "modify"
    DELETE = "delete"
    NONE = "none"


class ComponentType(StrEnum):
    """Nhóm component trong hệ thống phần mềm."""

    FRONTEND = "frontend"
    BACKEND = "backend"
    DATABASE = "database"
    INFRASTRUCTURE = "infrastructure"
    TEST = "test"
    DOCUMENTATION = "documentation"
    SHARED = "shared"


class ComponentChange(DomainModel):
    """Một component dự kiến bị ảnh hưởng bởi kế hoạch kỹ thuật."""

    component_name: str = Field(
        min_length=1,
        max_length=200,
        description="Tên component, module hoặc layer bị ảnh hưởng.",
    )

    component_type: ComponentType = Field(
        description="Nhóm kỹ thuật của component.",
    )

    change_type: ChangeType = Field(
        description="Loại thay đổi dự kiến.",
    )

    description: str = Field(
        min_length=1,
        description="Mô tả thay đổi cần thực hiện.",
    )

    affected_files: list[str] = Field(
        default_factory=list,
        description="Danh sách file dự kiến được tạo, sửa hoặc xóa.",
    )


class ImplementationStep(DomainModel):
    """Một bước triển khai cụ thể trong technical plan."""

    step_id: str = Field(
        min_length=1,
        description="Mã định danh của bước, ví dụ STEP-001.",
    )

    title: str = Field(
        min_length=1,
        max_length=200,
        description="Tên ngắn gọn của bước triển khai.",
    )

    description: str = Field(
        min_length=1,
        description="Mô tả chi tiết công việc cần thực hiện.",
    )

    component: str = Field(
        min_length=1,
        description="Component chịu trách nhiệm cho bước này.",
    )

    depends_on: list[str] = Field(
        default_factory=list,
        description="Danh sách step_id phải hoàn thành trước.",
    )

    affected_files: list[str] = Field(
        default_factory=list,
        description="Các file dự kiến bị ảnh hưởng.",
    )

    acceptance_criteria: list[str] = Field(
        default_factory=list,
        description="Danh sách criterion_id mà bước này hỗ trợ.",
    )


class ApiChange(DomainModel):
    """Một thay đổi dự kiến đối với API contract."""

    method: str = Field(
        min_length=1,
        description="HTTP method, ví dụ POST hoặc GET.",
    )

    path: str = Field(
        min_length=1,
        description="Đường dẫn API, ví dụ /auth/login.",
    )

    change_type: ChangeType = Field(
        description="API được tạo, sửa hay xóa.",
    )

    description: str = Field(
        min_length=1,
        description="Mô tả hành vi hoặc contract của API.",
    )

    request_schema: str | None = Field(
        default=None,
        description="Tên request schema nếu có.",
    )

    response_schema: str | None = Field(
        default=None,
        description="Tên response schema nếu có.",
    )


class DatabaseChange(DomainModel):
    """Một thay đổi dự kiến đối với database."""

    change_type: ChangeType = Field(
        description="Loại thay đổi database.",
    )

    target: str = Field(
        min_length=1,
        description="Table, collection, index hoặc migration bị ảnh hưởng.",
    )

    description: str = Field(
        min_length=1,
        description="Mô tả thay đổi database.",
    )

    migration_required: bool = Field(
        default=False,
        description="Có cần tạo migration hay không.",
    )


class TestPlanItem(DomainModel):
    """Một trường hợp hoặc nhóm kiểm thử cần triển khai."""

    test_id: str = Field(
        min_length=1,
        description="Mã định danh test plan, ví dụ TEST-001.",
    )

    test_type: str = Field(
        min_length=1,
        description="Loại test: unit, integration, contract hoặc end-to-end.",
    )

    description: str = Field(
        min_length=1,
        description="Nội dung cần kiểm thử.",
    )

    acceptance_criteria: list[str] = Field(
        default_factory=list,
        description="Acceptance criteria được kiểm chứng bởi test.",
    )


class TechnicalRisk(DomainModel):
    """Một rủi ro kỹ thuật được nhận diện trong quá trình thiết kế."""

    risk_id: str = Field(
        min_length=1,
        description="Mã định danh rủi ro, ví dụ RISK-001.",
    )

    description: str = Field(
        min_length=1,
        description="Mô tả rủi ro.",
    )

    impact: str = Field(
        min_length=1,
        description="Ảnh hưởng nếu rủi ro xảy ra.",
    )

    mitigation: str = Field(
        min_length=1,
        description="Biện pháp giảm thiểu.",
    )


class TechnicalPlan(DomainModel):
    """Kế hoạch kỹ thuật được tạo từ một RequirementSpec."""

    version: int = Field(
        default=1,
        ge=1,
        description="Phiên bản technical plan.",
    )

    requirement_title: str = Field(
        min_length=1,
        max_length=200,
        description="Tên requirement mà kế hoạch này xử lý.",
    )

    architecture_summary: str = Field(
        min_length=1,
        description="Tóm tắt giải pháp và hướng kiến trúc.",
    )

    components: list[ComponentChange] = Field(
        default_factory=list,
        description="Các component dự kiến bị ảnh hưởng.",
    )

    implementation_steps: list[ImplementationStep] = Field(
        default_factory=list,
        description="Các bước triển khai theo thứ tự hoặc dependency.",
    )

    api_changes: list[ApiChange] = Field(
        default_factory=list,
        description="Các thay đổi API.",
    )

    database_changes: list[DatabaseChange] = Field(
        default_factory=list,
        description="Các thay đổi database.",
    )

    test_plan: list[TestPlanItem] = Field(
        default_factory=list,
        description="Chiến lược và trường hợp kiểm thử.",
    )

    risks: list[TechnicalRisk] = Field(
        default_factory=list,
        description="Các rủi ro kỹ thuật và cách giảm thiểu.",
    )

    technical_assumptions: list[str] = Field(
        default_factory=list,
        description="Các giả định kỹ thuật được sử dụng.",
    )

    open_questions: list[str] = Field(
        default_factory=list,
        description="Các câu hỏi kỹ thuật chưa được giải quyết.",
    )