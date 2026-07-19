from software_team.domain import RequirementSpec, TechnicalPlan
from software_team.quality_gates.models import (
    ValidationIssue,
    ValidationIssueCode,
    ValidationResult,
    ValidationSeverity,
)


class RequirementPlanValidator:
    """Kiểm tra traceability giữa RequirementSpec và TechnicalPlan."""

    GATE_NAME = "requirement_plan"

    RULE_STEP_REFERENCES_EXISTING_CRITERIA = (
        "implementation_steps_reference_existing_acceptance_criteria"
    )

    RULE_TESTS_REFERENCE_EXISTING_CRITERIA = (
        "test_plan_references_existing_acceptance_criteria"
    )

    RULE_ALL_CRITERIA_HAVE_IMPLEMENTATION_STEP = (
        "all_acceptance_criteria_have_implementation_step"
    )

    RULE_REFERENCES_ARE_UNIQUE = (
        "acceptance_criterion_references_are_unique"
    )

    def validate(
        self,
        requirement: RequirementSpec,
        plan: TechnicalPlan,
    ) -> ValidationResult:
        issues: list[ValidationIssue] = []

        criterion_ids = {
            criterion.criterion_id
            for criterion in requirement.acceptance_criteria
        }

        issues.extend(
            self._validate_step_references(
                plan=plan,
                valid_criterion_ids=criterion_ids,
            )
        )

        issues.extend(
            self._validate_test_plan_references(
                plan=plan,
                valid_criterion_ids=criterion_ids,
            )
        )

        issues.extend(
            self._validate_acceptance_criterion_coverage(
                requirement=requirement,
                plan=plan,
            )
        )

        issues.extend(
            self._validate_duplicate_references(plan=plan)
        )

        passed = not any(issue.blocking for issue in issues)

        return ValidationResult(
            gate_name=self.GATE_NAME,
            passed=passed,
            issues=issues,
            checked_rules=[
                self.RULE_STEP_REFERENCES_EXISTING_CRITERIA,
                self.RULE_TESTS_REFERENCE_EXISTING_CRITERIA,
                self.RULE_ALL_CRITERIA_HAVE_IMPLEMENTATION_STEP,
                self.RULE_REFERENCES_ARE_UNIQUE,
            ],
        )

    def _validate_step_references(
        self,
        plan: TechnicalPlan,
        valid_criterion_ids: set[str],
    ) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []

        for step_index, step in enumerate(plan.implementation_steps):
            for criterion_id in step.related_acceptance_criteria:
                if criterion_id in valid_criterion_ids:
                    continue

                issues.append(
                    ValidationIssue(
                        code=(
                            ValidationIssueCode.UNKNOWN_ACCEPTANCE_CRITERION
                        ),
                        severity=ValidationSeverity.BLOCKER,
                        message=(
                            f"Implementation step {step.step_id} references "
                            f"unknown acceptance criterion {criterion_id}."
                        ),
                        source_artifact="TechnicalPlan",
                        source_field=(
                            f"implementation_steps[{step_index}]"
                            ".related_acceptance_criteria"
                        ),
                        reference_id=criterion_id,
                        related_artifact="RequirementSpec",
                        blocking=True,
                    )
                )

        return issues

    def _validate_test_plan_references(
        self,
        plan: TechnicalPlan,
        valid_criterion_ids: set[str],
    ) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []

        for test_index, test_item in enumerate(plan.test_plan):
            for criterion_id in test_item.related_acceptance_criteria:
                if criterion_id in valid_criterion_ids:
                    continue

                issues.append(
                    ValidationIssue(
                        code=(
                            ValidationIssueCode.UNKNOWN_ACCEPTANCE_CRITERION
                        ),
                        severity=ValidationSeverity.BLOCKER,
                        message=(
                            f"Test plan item {test_item.test_id} references "
                            f"unknown acceptance criterion {criterion_id}."
                        ),
                        source_artifact="TechnicalPlan",
                        source_field=(
                            f"test_plan[{test_index}]"
                            ".related_acceptance_criteria"
                        ),
                        reference_id=criterion_id,
                        related_artifact="RequirementSpec",
                        blocking=True,
                    )
                )

        return issues

    def _validate_acceptance_criterion_coverage(
        self,
        requirement: RequirementSpec,
        plan: TechnicalPlan,
    ) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []

        planned_criterion_ids = {
            criterion_id
            for step in plan.implementation_steps
            for criterion_id in step.related_acceptance_criteria
        }

        for criterion_index, criterion in enumerate(
            requirement.acceptance_criteria
        ):
            if criterion.criterion_id in planned_criterion_ids:
                continue

            issues.append(
                ValidationIssue(
                    code=ValidationIssueCode.UNPLANNED_ACCEPTANCE_CRITERION,
                    severity=ValidationSeverity.BLOCKER,
                    message=(
                        f"Acceptance criterion {criterion.criterion_id} "
                        "is not covered by any implementation step."
                    ),
                    source_artifact="RequirementSpec",
                    source_field=(
                        f"acceptance_criteria[{criterion_index}]"
                        ".criterion_id"
                    ),
                    reference_id=criterion.criterion_id,
                    related_artifact="TechnicalPlan",
                    blocking=True,
                )
            )

        return issues

    def _validate_duplicate_references(
        self,
        plan: TechnicalPlan,
    ) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []

        for step_index, step in enumerate(plan.implementation_steps):
            references = step.related_acceptance_criteria

            if len(references) == len(set(references)):
                continue

            duplicate_ids = sorted(
                {
                    criterion_id
                    for criterion_id in references
                    if references.count(criterion_id) > 1
                }
            )

            for criterion_id in duplicate_ids:
                issues.append(
                    ValidationIssue(
                        code=ValidationIssueCode.DUPLICATE_REFERENCE,
                        severity=ValidationSeverity.ERROR,
                        message=(
                            f"Implementation step {step.step_id} contains "
                            f"duplicate acceptance criterion reference "
                            f"{criterion_id}."
                        ),
                        source_artifact="TechnicalPlan",
                        source_field=(
                            f"implementation_steps[{step_index}]"
                            ".related_acceptance_criteria"
                        ),
                        reference_id=criterion_id,
                        blocking=True,
                    )
                )

        for test_index, test_item in enumerate(plan.test_plan):
            references = test_item.related_acceptance_criteria

            if len(references) == len(set(references)):
                continue

            duplicate_ids = sorted(
                {
                    criterion_id
                    for criterion_id in references
                    if references.count(criterion_id) > 1
                }
            )

            for criterion_id in duplicate_ids:
                issues.append(
                    ValidationIssue(
                        code=ValidationIssueCode.DUPLICATE_REFERENCE,
                        severity=ValidationSeverity.ERROR,
                        message=(
                            f"Test plan item {test_item.test_id} contains "
                            f"duplicate acceptance criterion reference "
                            f"{criterion_id}."
                        ),
                        source_artifact="TechnicalPlan",
                        source_field=(
                            f"test_plan[{test_index}]"
                            ".related_acceptance_criteria"
                        ),
                        reference_id=criterion_id,
                        blocking=True,
                    )
                )

        return issues