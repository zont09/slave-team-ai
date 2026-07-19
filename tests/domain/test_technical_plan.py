import pytest
from pydantic import ValidationError

from software_team.domain import (
    ApiChange,
    ChangeType,
    ComponentChange,
    ComponentType,
    ImplementationStep,
    TechnicalPlan,
    TestPlanItem as PlanTestItem,
)


def test_create_valid_technical_plan() -> None:
    plan = TechnicalPlan(
        requirement_title="User login",
        architecture_summary="Thêm authentication service và login endpoint.",
        components=[
            ComponentChange(
                component_name="Authentication API",
                component_type=ComponentType.BACKEND,
                change_type=ChangeType.CREATE,
                description="Thêm endpoint đăng nhập.",
                affected_files=["src/software_team/api/auth.py"],
            )
        ],
        implementation_steps=[
            ImplementationStep(
                step_id="STEP-001",
                title="Create login schema",
                description="Tạo request và response schema.",
                component="backend",
                acceptance_criteria=["AC-001"],
            )
        ],
        api_changes=[
            ApiChange(
                method="POST",
                path="/auth/login",
                change_type=ChangeType.CREATE,
                description="API đăng nhập.",
                request_schema="LoginRequest",
                response_schema="LoginResponse",
            )
        ],
        test_plan=[
            PlanTestItem(
                test_id="TEST-001",
                test_type="integration",
                description="Kiểm tra đăng nhập thành công.",
                acceptance_criteria=["AC-001"],
            )
        ],
    )

    assert plan.version == 1
    assert plan.requirement_title == "User login"
    assert len(plan.components) == 1
    assert plan.components[0].component_type == ComponentType.BACKEND
    assert plan.components[0].change_type == ChangeType.CREATE
    assert plan.api_changes[0].method == "POST"
    assert plan.test_plan[0].acceptance_criteria == ["AC-001"]


def test_create_technical_plan_with_empty_optional_lists() -> None:
    plan = TechnicalPlan(
        requirement_title="Documentation update",
        architecture_summary="Chỉ cập nhật tài liệu.",
    )

    assert plan.components == []
    assert plan.implementation_steps == []
    assert plan.api_changes == []
    assert plan.database_changes == []
    assert plan.test_plan == []
    assert plan.risks == []
    assert plan.technical_assumptions == []
    assert plan.open_questions == []


def test_reject_invalid_component_type() -> None:
    invalid_component = {
        "component_name": "Authentication",
        "component_type": "mobile-app",
        "change_type": "create",
        "description": "Thêm authentication.",
    }

    with pytest.raises(ValidationError):
        ComponentChange.model_validate(invalid_component)


def test_reject_invalid_change_type() -> None:
    invalid_component = {
        "component_name": "Authentication",
        "component_type": "backend",
        "change_type": "add",
        "description": "Thêm authentication.",
    }

    with pytest.raises(ValidationError):
        ComponentChange.model_validate(invalid_component)


def test_reject_empty_architecture_summary() -> None:
    with pytest.raises(ValidationError):
        TechnicalPlan(
            requirement_title="User login",
            architecture_summary="",
        )


def test_strip_whitespace_from_technical_plan_fields() -> None:
    plan = TechnicalPlan(
        requirement_title="   User login   ",
        architecture_summary="   Thêm authentication service.   ",
    )

    assert plan.requirement_title == "User login"
    assert plan.architecture_summary == "Thêm authentication service."


def test_implementation_step_dependencies_are_preserved() -> None:
    step = ImplementationStep(
        step_id="STEP-003",
        title="Implement login endpoint",
        description="Thêm API đăng nhập.",
        component="backend",
        depends_on=["STEP-001", "STEP-002"],
    )

    assert step.depends_on == ["STEP-001", "STEP-002"]


def test_technical_plan_instances_have_independent_lists() -> None:
    first_plan = TechnicalPlan(
        requirement_title="First feature",
        architecture_summary="First architecture.",
    )

    second_plan = TechnicalPlan(
        requirement_title="Second feature",
        architecture_summary="Second architecture.",
    )

    first_plan.open_questions.append("Only first plan")

    assert first_plan.open_questions == ["Only first plan"]
    assert second_plan.open_questions == []

def test_create_implementation_step_with_acceptance_criteria() -> None:
    step = ImplementationStep(
        step_id="STEP-001",
        title="Implement login service",
        description="Validate credentials and create access token.",
        component=ComponentType.BACKEND,
        related_acceptance_criteria=["AC-001", "AC-002"],
    )

    assert step.related_acceptance_criteria == [
        "AC-001",
        "AC-002",
    ]