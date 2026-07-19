import pytest
from pydantic import ValidationError

from software_team.domain import (
    ChangeType,
    CodeChangeResult,
    CodeChangeStatus,
    CommandExecution,
    CommandStatus,
    FileChange,
    ImplementationIssue,
    IssueSeverity,
)


def test_create_completed_code_change_result() -> None:
    result = CodeChangeResult(
        status=CodeChangeStatus.COMPLETED,
        summary="Đã triển khai login endpoint.",
        file_changes=[
            FileChange(
                path="src/software_team/api/auth.py",
                change_type=ChangeType.CREATE,
                summary="Thêm endpoint POST /auth/login.",
                related_steps=["STEP-002"],
                related_acceptance_criteria=["AC-001"],
            )
        ],
        commands=[
            CommandExecution(
                command="pytest -v",
                status=CommandStatus.SUCCESS,
                exit_code=0,
                stdout="24 passed",
                purpose="Chạy toàn bộ unit test.",
            )
        ],
        completed_steps=["STEP-001", "STEP-002"],
    )

    assert result.version == 1
    assert result.status == CodeChangeStatus.COMPLETED
    assert result.incomplete_steps == []
    assert len(result.file_changes) == 1
    assert result.file_changes[0].change_type == ChangeType.CREATE
    assert result.commands[0].exit_code == 0


def test_create_partially_completed_result() -> None:
    result = CodeChangeResult(
        status=CodeChangeStatus.PARTIALLY_COMPLETED,
        summary="Đã tạo schema nhưng chưa hoàn thành endpoint.",
        completed_steps=["STEP-001"],
        incomplete_steps=["STEP-002"],
        issues=[
            ImplementationIssue(
                issue_id="ISSUE-001",
                severity=IssueSeverity.BLOCKER,
                description="Thiếu cấu hình database.",
                impact="Không thể chạy integration test.",
                blocking=True,
            )
        ],
    )

    assert result.status == CodeChangeStatus.PARTIALLY_COMPLETED
    assert result.completed_steps == ["STEP-001"]
    assert result.incomplete_steps == ["STEP-002"]
    assert result.issues[0].blocking is True
    assert result.issues[0].resolution is None


def test_create_failed_command_execution() -> None:
    command = CommandExecution(
        command="pytest -v",
        status=CommandStatus.FAILED,
        exit_code=1,
        stderr="2 tests failed",
        purpose="Chạy unit test.",
    )

    assert command.status == CommandStatus.FAILED
    assert command.exit_code == 1
    assert command.stderr == "2 tests failed"


def test_create_skipped_command_without_exit_code() -> None:
    command = CommandExecution(
        command="docker compose up -d",
        status=CommandStatus.SKIPPED,
        purpose="Khởi động database test.",
        stderr="Docker không khả dụng.",
    )

    assert command.status == CommandStatus.SKIPPED
    assert command.exit_code is None


def test_reject_invalid_code_change_status() -> None:
    invalid_data = {
        "status": "done",
        "summary": "Đã hoàn thành.",
    }

    with pytest.raises(ValidationError):
        CodeChangeResult.model_validate(invalid_data)


def test_reject_invalid_command_status() -> None:
    invalid_data = {
        "command": "pytest",
        "status": "passed",
        "purpose": "Chạy test.",
    }

    with pytest.raises(ValidationError):
        CommandExecution.model_validate(invalid_data)


def test_reject_empty_file_path() -> None:
    with pytest.raises(ValidationError):
        FileChange(
            path="",
            change_type=ChangeType.CREATE,
            summary="Tạo file mới.",
        )


def test_strip_whitespace_from_code_change_fields() -> None:
    result = CodeChangeResult(
        status=CodeChangeStatus.COMPLETED,
        summary="   Đã hoàn thành triển khai.   ",
    )

    assert result.summary == "Đã hoàn thành triển khai."


def test_code_change_instances_have_independent_lists() -> None:
    first_result = CodeChangeResult(
        status=CodeChangeStatus.COMPLETED,
        summary="First result",
    )

    second_result = CodeChangeResult(
        status=CodeChangeStatus.COMPLETED,
        summary="Second result",
    )

    first_result.completed_steps.append("STEP-001")

    assert first_result.completed_steps == ["STEP-001"]
    assert second_result.completed_steps == []

def test_reject_success_command_with_non_zero_exit_code() -> None:
    with pytest.raises(
        ValidationError,
        match="successful command must have exit_code equal to 0",
    ):
        CommandExecution(
            command="pytest",
            status=CommandStatus.SUCCESS,
            exit_code=1,
            purpose="Chạy unit test.",
        )

def test_reject_success_command_without_exit_code() -> None:
    with pytest.raises(
        ValidationError,
        match="successful command must have exit_code equal to 0",
    ):
        CommandExecution(
            command="pytest",
            status=CommandStatus.SUCCESS,
            purpose="Chạy unit test.",
        )

def test_reject_failed_command_with_zero_exit_code() -> None:
    with pytest.raises(
        ValidationError,
        match="failed command must have a non-zero exit_code",
    ):
        CommandExecution(
            command="pytest",
            status=CommandStatus.FAILED,
            exit_code=0,
            purpose="Chạy unit test.",
        )

def test_reject_failed_command_without_exit_code() -> None:
    with pytest.raises(
        ValidationError,
        match="failed command must have a non-zero exit_code",
    ):
        CommandExecution(
            command="pytest",
            status=CommandStatus.FAILED,
            purpose="Chạy unit test.",
        )

def test_reject_skipped_command_with_exit_code() -> None:
    with pytest.raises(
        ValidationError,
        match="skipped command must not have an exit_code",
    ):
        CommandExecution(
            command="docker compose up -d",
            status=CommandStatus.SKIPPED,
            exit_code=0,
            purpose="Khởi động database.",
        )

def test_reject_completed_result_with_incomplete_steps() -> None:
    with pytest.raises(
        ValidationError,
        match="completed result cannot contain incomplete steps",
    ):
        CodeChangeResult(
            status=CodeChangeStatus.COMPLETED,
            summary="Đã hoàn thành.",
            incomplete_steps=["STEP-002"],
        )

def test_reject_partially_completed_result_without_incomplete_steps() -> None:
    with pytest.raises(
        ValidationError,
        match=(
            "partially completed result must contain incomplete steps"
        ),
    ):
        CodeChangeResult(
            status=CodeChangeStatus.PARTIALLY_COMPLETED,
            summary="Hoàn thành một phần.",
        )

def test_reject_step_in_both_completed_and_incomplete_lists() -> None:
    with pytest.raises(
        ValidationError,
        match="Steps cannot be both completed and incomplete: STEP-002",
    ):
        CodeChangeResult(
            status=CodeChangeStatus.PARTIALLY_COMPLETED,
            summary="Hoàn thành một phần.",
            completed_steps=["STEP-001", "STEP-002"],
            incomplete_steps=["STEP-002", "STEP-003"],
        )