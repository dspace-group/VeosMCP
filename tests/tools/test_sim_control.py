"""Integration-style tests for VEOS sim control tools."""

from typing import cast

from mcp.types import CallToolResult
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
from tests.tool_test_helpers import (
    RecordingSimCliMock,
    assert_command_result_structured_content,
    assert_error_text_content,
)


@pytest.mark.parametrize(
    ("tool_func", "tool_name", "expected_call", "payload"),
    [
        (veos_status_info, "veos_status_info", ("info",), {}),
        (veos_load, "veos_load", ("load", "model.osa"), {"osa_path": "model.osa"}),
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
            {"osa_path": "model.osa"},
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
            stop_time="10",
            acceleration_factor="2",
            ip_address="127.0.0.2",
            bus_log=True,
            sim_log=False,
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
    assert_command_result_structured_content(
        "veos_apply_config", result.structuredContent
    )


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
    assert_command_result_structured_content(
        "veos_apply_config", result.structuredContent
    )


def test_tool_veos_apply_config_returns_error_response_on_cli_failure(
    monkeypatch,
) -> None:
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

    result = cast(CallToolResult, veos_apply_config(bus_log=False, sim_log=True))

    assert result.isError is True
    assert cli.sim_calls == [("config", "--disable-bus-log", "--enable-sim-log")]
    assert result.structuredContent is not None
    assert_command_result_structured_content(
        "veos_apply_config", result.structuredContent
    )
    assert_error_text_content(
        result, "Failed to apply the VEOS simulation configuration."
    )
