import pytest
from pydantic import ValidationError

from software_team.domain import AcceptanceCriterion, RequirementSpec


def test_create_valid_requirement_spec() -> None:
    requirement = RequirementSpec(
        title="User login",
        summary="Cho phép người dùng đăng nhập.",
        business_goal="Xác định danh tính người dùng.",
        in_scope=[
            "Đăng nhập bằng email và mật khẩu",
        ],
        out_of_scope=[
            "Đăng nhập bằng Google",
        ],
        functional_requirements=[
            "Hệ thống phải xác thực email và mật khẩu.",
        ],
        non_functional_requirements=[
            "Mật khẩu không được ghi vào log.",
        ],
        acceptance_criteria=[
            AcceptanceCriterion(
                criterion_id="AC-001",
                description="Người dùng đăng nhập thành công với thông tin hợp lệ.",
            )
        ],
        assumptions=[
            "Người dùng đã có tài khoản.",
        ],
        constraints=[
            "Backend sử dụng Python.",
        ],
        open_questions=[
            "Có cần khóa tài khoản sau nhiều lần đăng nhập sai không?",
        ],
    )

    assert requirement.version == 1
    assert requirement.title == "User login"
    assert requirement.business_goal == "Xác định danh tính người dùng."
    assert len(requirement.acceptance_criteria) == 1
    assert requirement.acceptance_criteria[0].criterion_id == "AC-001"

def test_strip_whitespace_from_string_fields() -> None:
    requirement = RequirementSpec(
        title="   User login   ",
        summary="   Cho phép người dùng đăng nhập.   ",
        business_goal="   Xác định danh tính người dùng.   ",
    )

    assert requirement.title == "User login"
    assert requirement.summary == "Cho phép người dùng đăng nhập."
    assert requirement.business_goal == "Xác định danh tính người dùng."

def test_reject_missing_required_field() -> None:
    with pytest.raises(ValidationError):
        RequirementSpec(
            title="User login",
            summary="Cho phép người dùng đăng nhập.",
        )

def test_reject_empty_title() -> None:
    with pytest.raises(ValidationError):
        RequirementSpec(
            title="",
            summary="Cho phép người dùng đăng nhập.",
            business_goal="Xác định danh tính người dùng.",
        )

def test_reject_title_containing_only_whitespace() -> None:
    with pytest.raises(ValidationError):
        RequirementSpec(
            title="     ",
            summary="Cho phép người dùng đăng nhập.",
            business_goal="Xác định danh tính người dùng.",
        )

def test_reject_unknown_field() -> None:
    with pytest.raises(ValidationError):
        RequirementSpec(
            title="User login",
            summary="Cho phép người dùng đăng nhập.",
            business_goal="Xác định danh tính người dùng.",
            unknown_field="Dữ liệu không tồn tại trong schema",
        )

def test_validate_data_when_assigning_new_value() -> None:
    requirement = RequirementSpec(
        title="User login",
        summary="Cho phép người dùng đăng nhập.",
        business_goal="Xác định danh tính người dùng.",
    )

    with pytest.raises(ValidationError):
        requirement.version = 0

def test_requirement_instances_have_independent_lists() -> None:
    first_requirement = RequirementSpec(
        title="First feature",
        summary="First summary",
        business_goal="First goal",
    )

    second_requirement = RequirementSpec(
        title="Second feature",
        summary="Second summary",
        business_goal="Second goal",
    )

    first_requirement.in_scope.append("Only in first requirement")

    assert first_requirement.in_scope == ["Only in first requirement"]
    assert second_requirement.in_scope == []