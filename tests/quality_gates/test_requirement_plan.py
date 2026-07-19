from software_team.domain import (
    AcceptanceCriterion,
    ImplementationStep,
    ComponentType,
    RequirementSpec,
    TechnicalPlan,
    TestPlanItem as PlanTestItem,
)
from software_team.quality_gates import (
    RequirementPlanValidator,
    ValidationIssueCode,
    ValidationSeverity,
)

def create_requirement() -> RequirementSpec:
    return RequirementSpec(
        title="User login",
        summary="Cho phép người dùng đăng nhập.",
        business_goal=(
            "Cho phép người dùng xác thực để truy cập "
            "các chức năng được bảo vệ."
        ),
        functional_requirements=[
            "Người dùng có thể đăng nhập bằng email và password.",
        ],
        acceptance_criteria=[
            AcceptanceCriterion(
                criterion_id="AC-001",
                description="Thông tin hợp lệ trả về access token.",
            ),
            AcceptanceCriterion(
                criterion_id="AC-002",
                description="Sai password trả về lỗi xác thực.",
            ),
        ],
    )

def create_valid_plan() -> TechnicalPlan:
    return TechnicalPlan(
        requirement_title="User login",
        architecture_summary="Triển khai login endpoint.",
        implementation_steps=[
            ImplementationStep(
                step_id="STEP-001",
                title="Tạo login service",
                description="Thêm logic xác thực credentials.",
                component=ComponentType.BACKEND,
                related_acceptance_criteria=["AC-001", "AC-002"],
            ),
        ],
        test_plan=[
            PlanTestItem(
                test_id="TEST-001",
                description="Kiểm tra login thành công.",
                test_type="integration",
                related_acceptance_criteria=["AC-001"],
            ),
            PlanTestItem(
                test_id="TEST-002",
                description="Kiểm tra password không hợp lệ.",
                test_type="integration",
                related_acceptance_criteria=["AC-002"],
            ),
        ],
    )

def test_pass_when_plan_references_valid_acceptance_criteria() -> None:
    validator = RequirementPlanValidator()

    result = validator.validate(
        requirement=create_requirement(),
        plan=create_valid_plan(),
    )

    assert result.passed is True
    assert result.issues == []
    assert result.gate_name == "requirement_plan"
    assert len(result.checked_rules) == 4

def test_fail_when_step_references_unknown_acceptance_criterion() -> None:
    validator = RequirementPlanValidator()
    plan = create_valid_plan()

    plan.implementation_steps[0].related_acceptance_criteria.append(
        "AC-999"
    )

    result = validator.validate(
        requirement=create_requirement(),
        plan=plan,
    )

    assert result.passed is False
    assert len(result.issues) == 1

    issue = result.issues[0]

    assert (
        issue.code
        == ValidationIssueCode.UNKNOWN_ACCEPTANCE_CRITERION
    )
    assert issue.severity == ValidationSeverity.BLOCKER
    assert issue.reference_id == "AC-999"
    assert issue.source_artifact == "TechnicalPlan"
    assert issue.related_artifact == "RequirementSpec"
    assert issue.blocking is True

def test_fail_when_test_plan_references_unknown_criterion() -> None:
    validator = RequirementPlanValidator()
    plan = create_valid_plan()

    plan.test_plan[0].related_acceptance_criteria.append("AC-404")

    result = validator.validate(
        requirement=create_requirement(),
        plan=plan,
    )

    assert result.passed is False

    matching_issues = [
        issue
        for issue in result.issues
        if issue.reference_id == "AC-404"
    ]

    assert len(matching_issues) == 1

    issue = matching_issues[0]

    assert (
        issue.code
        == ValidationIssueCode.UNKNOWN_ACCEPTANCE_CRITERION
    )
    assert issue.source_field == (
        "test_plan[0].related_acceptance_criteria"
    )

def test_fail_when_acceptance_criterion_has_no_implementation_step() -> None:
    validator = RequirementPlanValidator()
    plan = create_valid_plan()

    plan.implementation_steps[0].related_acceptance_criteria = [
        "AC-001"
    ]

    result = validator.validate(
        requirement=create_requirement(),
        plan=plan,
    )

    assert result.passed is False

    matching_issues = [
        issue
        for issue in result.issues
        if issue.code
        == ValidationIssueCode.UNPLANNED_ACCEPTANCE_CRITERION
    ]

    assert len(matching_issues) == 1
    assert matching_issues[0].reference_id == "AC-002"
    assert matching_issues[0].source_artifact == "RequirementSpec"

def test_collect_all_requirement_plan_issues() -> None:
    validator = RequirementPlanValidator()
    plan = create_valid_plan()

    plan.implementation_steps[0].related_acceptance_criteria = [
        "AC-999"
    ]

    plan.test_plan[0].related_acceptance_criteria = [
        "AC-404"
    ]

    result = validator.validate(
        requirement=create_requirement(),
        plan=plan,
    )

    assert result.passed is False

    issue_codes = [
        issue.code
        for issue in result.issues
    ]

    assert issue_codes.count(
        ValidationIssueCode.UNKNOWN_ACCEPTANCE_CRITERION
    ) == 2

    assert issue_codes.count(
        ValidationIssueCode.UNPLANNED_ACCEPTANCE_CRITERION
    ) == 2

def test_fail_when_step_contains_duplicate_criterion_reference() -> None:
    validator = RequirementPlanValidator()
    plan = create_valid_plan()

    plan.implementation_steps[0].related_acceptance_criteria = [
        "AC-001",
        "AC-001",
        "AC-002",
    ]

    result = validator.validate(
        requirement=create_requirement(),
        plan=plan,
    )

    duplicate_issues = [
        issue
        for issue in result.issues
        if issue.code == ValidationIssueCode.DUPLICATE_REFERENCE
    ]

    assert result.passed is False
    assert len(duplicate_issues) == 1
    assert duplicate_issues[0].reference_id == "AC-001"