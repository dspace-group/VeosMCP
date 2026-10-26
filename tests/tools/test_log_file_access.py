"""Integration-style tests for VEOS log file access tools"""

from typing import cast

from mcp.types import CallToolResult

from tests.tool_test_helpers import (
    RecordingSimCliMock,
    assert_command_result_structured_content,
    assert_error_text_content,
)
from veos_mcp import runtime
from veos_mcp.models.cli_command_result import CliCommandResult, CommandResultCode
from veos_mcp.tools.log_file_access import (
    veos_list_all_available_log_files,
)


def test_tool_veos_list_all_available_log_files_invokes_veos_sim(monkeypatch) -> None:
    cli = RecordingSimCliMock(
        CliCommandResult(
            success=True,
            exit_code=0,
            code=CommandResultCode.OK,
            stdout="veos.log\ntrace.pcapng",
            stdout_bytes=b"veos.log\ntrace.pcapng",
            stderr="",
        )
    )
    monkeypatch.setattr(runtime, "_veos_cli", cli)

    result = cast(CallToolResult, veos_list_all_available_log_files())

    assert result.is_error is False
    assert cli.sim_calls == [("show-log",)]
    assert result.structured_content is not None
    assert_command_result_structured_content("veos_list_all_available_log_files", result.structured_content)


def test_tool_veos_list_all_available_log_files_returns_error_response_on_cli_failure(
    monkeypatch,
) -> None:
    cli = RecordingSimCliMock(
        CliCommandResult(
            success=False,
            exit_code=1,
            code=CommandResultCode.PROCESS_FAILED,
            stdout="",
            stdout_bytes=b"",
            stderr="failed",
        )
    )
    monkeypatch.setattr(runtime, "_veos_cli", cli)

    result = cast(CallToolResult, veos_list_all_available_log_files())

    assert result.is_error is True
    assert cli.sim_calls == [("show-log",)]
    assert result.structured_content is not None
    assert_command_result_structured_content("veos_list_all_available_log_files", result.structured_content)
    assert_error_text_content(result, "Failed to retrieve the list of available log files.")
