"""Tests for the VEOS OSA creation tool."""

from typing import cast

from mcp.types import CallToolResult

from tests.tool_test_helpers import (
    RecordingModelCliMock,
    assert_command_result_structured_content,
    assert_error_text_content,
)
from veos_mcp import runtime
from veos_mcp.models.cli_command_result import CliCommandResult, CommandResultCode
from veos_mcp.tools.osa_creation import veos_create_osa


def create_command_result(*, success: bool) -> CliCommandResult:
    return CliCommandResult(
        success=success,
        exit_code=0 if success else 1,
        code=CommandResultCode.OK if success else CommandResultCode.PROCESS_FAILED,
        stdout="created" if success else "",
        stderr="" if success else "failed",
    )


def test_create_osa_invokes_headless_model_console(monkeypatch) -> None:
    cli = RecordingModelCliMock(create_command_result(success=True))
    monkeypatch.setattr(runtime, "_veos_cli", cli)

    result = cast(CallToolResult, veos_create_osa("new-system.osa"))

    assert cli.model_calls == [
        (
            "modify",
            "new-system.osa",
            "--modifications",
            "[]",
            "--create-new",
            "--save-only-on-success",
            "--verbosity",
            "Error",
        )
    ]
    assert result.isError is False
    assert result.structuredContent is not None
    assert_command_result_structured_content("veos_create_osa", result.structuredContent)


def test_create_osa_returns_error_when_model_console_fails(monkeypatch) -> None:
    cli = RecordingModelCliMock(create_command_result(success=False))
    monkeypatch.setattr(runtime, "_veos_cli", cli)

    result = cast(CallToolResult, veos_create_osa("existing.osa"))

    assert result.isError is True
    assert_error_text_content(result, "Failed to create VEOS OSA file existing.osa.")
