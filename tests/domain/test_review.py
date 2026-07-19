import pytest
from pydantic import ValidationError

from software_team.domain import (
    FindingStatus,
    ReviewCategory,
    ReviewDecision,
    ReviewFinding as Finding,
    ReviewResult as Result,
    ReviewSeverity,
)


def test_create_approved_review_result() -> None:
    result = Result(
        decision=ReviewDecision.APPROVED,
        summary="Implementation đáp ứng yêu cầu.",
        positive_observations=[
            "Code rõ ràng và test đầy đủ.",
        ],
        reviewed_acceptance_criteria=[
            "AC-001",
            "AC-002",
        ],
        reviewed_steps=[
            "STEP-001",
            "STEP-002",
        ],
    )

    assert result.version == 1
    assert result.decision == ReviewDecision.APPROVED
    assert result.findings == []
    assert result.required_changes == []


def test_create_approved_with_notes_result() -> None:
    result = Result(
        decision=ReviewDecision.APPROVED_WITH_NOTES,
        summary="Có thể approve nhưng nên cải thiện documentation.",
        findings=[
            Finding(
                finding_id="REVIEW-001",
                title="Thiếu docstring",
                description="Public service chưa có docstring.",
                category=ReviewCategory.DOCUMENTATION,
                severity=ReviewSeverity.LOW,
                recommendation="Bổ sung docstring trong lần refactor sau.",
            )
        ],
        suggestions=[
            "Bổ sung docstring cho public service.",
        ],
    )

    assert result.decision == ReviewDecision.APPROVED_WITH_NOTES
    assert len(result.findings) == 1


def test_create_changes_requested_result() -> None:
    result = Result(
        decision=ReviewDecision.CHANGES_REQUESTED,
        summary="Cần sửa validation trước khi approve.",
        findings=[
            Finding(
                finding_id="REVIEW-001",
                title="Thiếu token validation",
                description="Token hết hạn vẫn được chấp nhận.",
                category=ReviewCategory.SECURITY,
                severity=ReviewSeverity.HIGH,
                file_path="src/software_team/api/auth.py",
                line_number=84,
                recommendation="Kiểm tra exp claim.",
                blocking=True,
            )
        ],
        required_changes=[
            "Bổ sung kiểm tra exp claim.",
        ],
    )

    assert result.decision == ReviewDecision.CHANGES_REQUESTED
    assert result.findings[0].blocking is True


def test_create_rejected_review_result() -> None:
    result = Result(
        decision=ReviewDecision.REJECTED,
        summary="Giải pháp hiện tại có lỗ hổng bảo mật nghiêm trọng.",
        findings=[
            Finding(
                finding_id="REVIEW-001",
                title="Authentication bypass",
                description="Endpoint cho phép bỏ qua xác thực.",
                category=ReviewCategory.SECURITY,
                severity=ReviewSeverity.BLOCKER,
                recommendation="Thiết kế lại authentication flow.",
                blocking=True,
            )
        ],
        required_changes=[
            "Thiết kế lại authentication flow.",
        ],
    )

    assert result.decision == ReviewDecision.REJECTED


def test_reject_finding_with_line_number_but_without_file_path() -> None:
    with pytest.raises(
        ValidationError,
        match="finding with line_number must also contain file_path",
    ):
        Finding(
            finding_id="REVIEW-001",
            title="Invalid validation",
            description="Validation không chính xác.",
            category=ReviewCategory.IMPLEMENTATION,
            severity=ReviewSeverity.MEDIUM,
            line_number=20,
        )


def test_reject_blocker_finding_that_is_not_blocking() -> None:
    with pytest.raises(
        ValidationError,
        match="blocker finding must have blocking set to true",
    ):
        Finding(
            finding_id="REVIEW-001",
            title="Authentication bypass",
            description="Endpoint bỏ qua xác thực.",
            category=ReviewCategory.SECURITY,
            severity=ReviewSeverity.BLOCKER,
            blocking=False,
        )


def test_reject_resolved_finding_that_remains_blocking() -> None:
    with pytest.raises(
        ValidationError,
        match="resolved finding cannot remain blocking",
    ):
        Finding(
            finding_id="REVIEW-001",
            title="Validation issue",
            description="Validation chưa chính xác.",
            category=ReviewCategory.IMPLEMENTATION,
            severity=ReviewSeverity.HIGH,
            status=FindingStatus.RESOLVED,
            blocking=True,
        )


def test_reject_approved_result_with_open_blocking_finding() -> None:
    with pytest.raises(
        ValidationError,
        match="approved review cannot contain open blocking findings",
    ):
        Result(
            decision=ReviewDecision.APPROVED,
            summary="Implementation đã được approve.",
            findings=[
                Finding(
                    finding_id="REVIEW-001",
                    title="Security issue",
                    description="Có lỗi bảo mật.",
                    category=ReviewCategory.SECURITY,
                    severity=ReviewSeverity.HIGH,
                    blocking=True,
                )
            ],
        )


def test_reject_approved_result_with_required_changes() -> None:
    with pytest.raises(
        ValidationError,
        match="approved review cannot contain required changes",
    ):
        Result(
            decision=ReviewDecision.APPROVED,
            summary="Implementation đã được approve.",
            required_changes=[
                "Sửa authentication.",
            ],
        )


def test_reject_approved_with_notes_with_required_changes() -> None:
    with pytest.raises(
        ValidationError,
        match=(
            "approved-with-notes review cannot contain required changes"
        ),
    ):
        Result(
            decision=ReviewDecision.APPROVED_WITH_NOTES,
            summary="Có thể approve.",
            required_changes=[
                "Bổ sung validation.",
            ],
        )


def test_reject_changes_requested_without_required_action() -> None:
    with pytest.raises(
        ValidationError,
        match=(
            "changes-requested review must contain required changes "
            "or open blocking findings"
        ),
    ):
        Result(
            decision=ReviewDecision.CHANGES_REQUESTED,
            summary="Cần chỉnh sửa.",
        )


def test_reject_rejected_result_without_high_severity_finding() -> None:
    with pytest.raises(
        ValidationError,
        match=(
            "rejected review must contain an open high-severity "
            "or blocker finding"
        ),
    ):
        Result(
            decision=ReviewDecision.REJECTED,
            summary="Implementation bị từ chối.",
            findings=[
                Finding(
                    finding_id="REVIEW-001",
                    title="Missing documentation",
                    description="Thiếu docstring.",
                    category=ReviewCategory.DOCUMENTATION,
                    severity=ReviewSeverity.LOW,
                )
            ],
        )


def test_reject_duplicate_finding_ids() -> None:
    with pytest.raises(
        ValidationError,
        match="findings must not contain duplicate finding IDs",
    ):
        Result(
            decision=ReviewDecision.APPROVED_WITH_NOTES,
            summary="Có một số ghi chú.",
            findings=[
                Finding(
                    finding_id="REVIEW-001",
                    title="First finding",
                    description="Finding thứ nhất.",
                    category=ReviewCategory.DOCUMENTATION,
                    severity=ReviewSeverity.LOW,
                ),
                Finding(
                    finding_id="REVIEW-001",
                    title="Second finding",
                    description="Finding thứ hai.",
                    category=ReviewCategory.MAINTAINABILITY,
                    severity=ReviewSeverity.LOW,
                ),
            ],
        )


def test_strip_whitespace_from_review_fields() -> None:
    result = Result(
        decision=ReviewDecision.APPROVED,
        summary="   Implementation đáp ứng yêu cầu.   ",
    )

    assert result.summary == "Implementation đáp ứng yêu cầu."