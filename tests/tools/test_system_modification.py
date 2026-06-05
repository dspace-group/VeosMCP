"""Integration-style tests for VEOS system modification tools."""

from __future__ import annotations

import json
from typing import cast

from mcp.types import CallToolResult, TextContent
import pytest

from veos_mcp import runtime
from veos_mcp.schemas.cli_command_result import CliCommandResult, CommandResultCode
from veos_mcp.tools.system_modification import (
    veos_add_signal_connection,
    veos_remove_signal_connection,
)

class RecordingModelCliMock:
    def __init__(self, result: CliCommandResult) -> None:
        self._result = result
        self.model_calls: list[tuple[str, ...]] = []

    def run_model(self, *arguments: str) -> CliCommandResult:
        self.model_calls.append(arguments)
        return self._result


def assert_command_result_structured_content(
    tool_name: str,
    structured_content: dict[str, object],
) -> None:
    assert "Success" in structured_content, (
        f"{tool_name} should include Success in structured content."
    )
    assert "Code" in structured_content, (
        f"{tool_name} should include Code in structured content."
    )
    assert "Stdout" in structured_content, (
        f"{tool_name} should include Stdout in structured content."
    )
    assert "Stderr" in structured_content, (
        f"{tool_name} should include Stderr in structured content."
    )
    assert "ExitCode" in structured_content, (
        f"{tool_name} should include ExitCode in structured content."
    )


def assert_error_text_content(result: CallToolResult, expected_message: str) -> None:
    assert result.content is not None, "Expected text content in the tool result."
    text_content = cast(TextContent, result.content[0])
    payload = json.loads(text_content.text)
    assert payload["Type"] == "PermanentError"
    assert payload["Message"] == expected_message


@pytest.mark.parametrize(
    ("tool_func", "tool_name", "arguments"),
    [
        (
            veos_add_signal_connection,
            "veos_add_signal_connection",
            ("connect", "model.osa", "-c", "connections.json"),
        ),
        (
            veos_remove_signal_connection,
            "veos_remove_signal_connection",
            ("remove", "model.osa", "-c", "connections.json"),
        ),
    ],
)
def test_system_modification_tools_invoke_veos_model_and_return_structured_content(
    monkeypatch,
    tool_func,
    tool_name: str,
    arguments: tuple[str, ...],
) -> None:
    cli = RecordingModelCliMock(
        CliCommandResult(
            success=True,
            exit_code=0,
            code=CommandResultCode.OK,
            stdout="edited",
            stdout_bytes=b"edited",
            stderr="",
        )
    )
    monkeypatch.setattr(runtime, "_veos_cli", cli)

    result = cast(CallToolResult, tool_func("model.osa", "connections.json"))

    assert result.isError is False
    assert cli.model_calls == [arguments]
    assert result.structuredContent is not None
    assert_command_result_structured_content(tool_name, result.structuredContent)


@pytest.mark.parametrize(
    ("tool_func", "tool_name", "arguments", "expected_message"),
    [
        (
            veos_add_signal_connection,
            "veos_add_signal_connection",
            ("connect", "model.osa", "-c", "connections.json"),
            "Failed to add signal connection from JSON file connections.json on the VEOS model.",
        ),
        (
            veos_remove_signal_connection,
            "veos_remove_signal_connection",
            ("remove", "model.osa", "-c", "connections.json"),
            "Failed to remove signal connection from JSON file connections.json on the VEOS model.",
        ),
    ],
)
def test_system_modification_tools_return_error_response_on_cli_failure(
    monkeypatch,
    tool_func,
    tool_name: str,
    arguments: tuple[str, ...],
    expected_message: str,
) -> None:
    cli = RecordingModelCliMock(
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

    result = cast(CallToolResult, tool_func("model.osa", "connections.json"))

    assert result.isError is True
    assert cli.model_calls == [arguments]
    assert result.structuredContent is not None
    assert_command_result_structured_content(tool_name, result.structuredContent)
    assert_error_text_content(result, expected_message)
