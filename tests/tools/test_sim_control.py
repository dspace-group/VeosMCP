"""Integration-style tests for VEOS sim control tools."""


import json
from typing import cast

from mcp.types import CallToolResult, TextContent
import pytest

from veos_mcp import runtime
from veos_mcp.models.cli_command_result import CliCommandResult, CommandResultCode
from veos_mcp.tools.sim_control import (
    veos_apply_config,
    veos_load,
    veos_start,
    veos_status_info,
    veos_stop,
)

class RecordingSimCliMock:
    def __init__(self, sim_result: CliCommandResult) -> None:
        self._sim_result = sim_result
        self.sim_calls: list[tuple[str, ...]] = []

    def run_sim(self, *arguments: str) -> CliCommandResult:
        self.sim_calls.append(arguments)
        return self._sim_result


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
    ("tool_func", "tool_name", "expected_call", "payload"),
    [
        (veos_status_info, "veos_status_info", ("info",), {}),
        (veos_load, "veos_load", ("load", "model.osa"), {"osaPath": "model.osa"}),
        (veos_start, "veos_start", ("start",), {}),
        (veos_stop, "veos_stop", ("stop",), {}),
    ],
)
def test_sim_control_tools_invoke_veos_sim_and_return_structured_content(
    monkeypatch,
    tool_func,
    tool_name: str,
    expected_call: tuple[str, ...],
    payload: dict[str, object],
) -> None:
    cli = RecordingSimCliMock(
        CliCommandResult(
            success=True,
            exit_code=0,
            code=CommandResultCode.OK,
            stdout="ok",
            stdout_bytes=b"ok",
            stderr="",
        )
    )
    monkeypatch.setattr(runtime, "_veos_cli", cli)

    result = cast(CallToolResult, tool_func(**payload))

    assert result.isError is False
    assert cli.sim_calls == [expected_call]
    assert result.structuredContent is not None
    assert_command_result_structured_content(tool_name, result.structuredContent)


@pytest.mark.parametrize(
    ("tool_func", "tool_name", "expected_call", "payload", "expected_message"),
    [
        (
            veos_status_info,
            "veos_status_info",
            ("info",),
            {},
            "Failed to get VEOS status info.",
        ),
        (
            veos_load,
            "veos_load",
            ("load", "model.osa"),
            {"osaPath": "model.osa"},
            "Failed to load osa file onto the VEOS.",
        ),
        (
            veos_start,
            "veos_start",
            ("start",),
            {},
            "Failed to start the VEOS simulation.",
        ),
        (
            veos_stop,
            "veos_stop",
            ("stop",),
            {},
            "Failed to stop the VEOS simulation.",
        ),
    ],
)
def test_sim_control_tools_return_error_response_on_cli_failure(
    monkeypatch,
    tool_func,
    tool_name: str,
    expected_call: tuple[str, ...],
    payload: dict[str, object],
    expected_message: str,
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

    result = cast(CallToolResult, tool_func(**payload))

    assert result.isError is True
    assert cli.sim_calls == [expected_call]
    assert result.structuredContent is not None
    assert_command_result_structured_content(tool_name, result.structuredContent)
    assert_error_text_content(result, expected_message)


def test_tool_veos_apply_config_invokes_veos_sim_with_all_supported_arguments(
    monkeypatch,
) -> None:
    cli = RecordingSimCliMock(
        CliCommandResult(
            success=True,
            exit_code=0,
            code=CommandResultCode.OK,
            stdout="configured",
            stdout_bytes=b"configured",
            stderr="",
        )
    )
    monkeypatch.setattr(runtime, "_veos_cli", cli)

    result = cast(
        CallToolResult,
        veos_apply_config(
            stopTime="10",
            accelerationFactor="2",
            ipAddress="127.0.0.2",
            busLog=True,
            simLog=False,
        ),
    )

    assert result.isError is False
    assert cli.sim_calls == [
        (
            "config",
            "-o",
            "10",
            "-h",
            "127.0.0.2",
            "-a",
            "2",
            "--enable-bus-log",
            "--disable-sim-log",
        )
    ]
    assert result.structuredContent is not None
    assert_command_result_structured_content("veos_apply_config", result.structuredContent)


def test_tool_veos_apply_config_uses_default_command_without_optional_arguments(
    monkeypatch,
) -> None:
    cli = RecordingSimCliMock(
        CliCommandResult(
            success=True,
            exit_code=0,
            code=CommandResultCode.OK,
            stdout="configured",
            stdout_bytes=b"configured",
            stderr="",
        )
    )
    monkeypatch.setattr(runtime, "_veos_cli", cli)

    result = cast(CallToolResult, veos_apply_config())

    assert result.isError is False
    assert cli.sim_calls == [("config",)]
    assert result.structuredContent is not None
    assert_command_result_structured_content("veos_apply_config", result.structuredContent)


def test_tool_veos_apply_config_returns_error_response_on_cli_failure(monkeypatch) -> None:
    cli = RecordingSimCliMock(
        CliCommandResult(
            success=False,
            exit_code=1,
            code=CommandResultCode.PROCESS_FAILED,
            stdout="",
            stdout_bytes=b"",
            stderr="invalid config",
        )
    )
    monkeypatch.setattr(runtime, "_veos_cli", cli)

    result = cast(CallToolResult, veos_apply_config(busLog=False, simLog=True))

    assert result.isError is True
    assert cli.sim_calls == [("config", "--disable-bus-log", "--enable-sim-log")]
    assert result.structuredContent is not None
    assert_command_result_structured_content("veos_apply_config", result.structuredContent)
    assert_error_text_content(result, "Failed to apply the VEOS simulation configuration.")