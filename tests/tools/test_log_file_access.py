"""Integration-style tests for VEOS log file access tools"""

from typing import cast

from mcp.types import CallToolResult, ResourceLink

from tests.tool_test_helpers import (
    RecordingSimCliMock,
    assert_command_result_structured_content,
    assert_error_text_content,
)
from veos_mcp import runtime
from veos_mcp.models.cli_command_result import CliCommandResult, CommandResultCode
from veos_mcp.tools.log_file_access import (
    veos_get_log_file,
    veos_list_all_available_log_files,
)


def test_tool_veos_get_log_file_returns_bus_resource_link_for_pcapng() -> None:
    result = cast(CallToolResult, veos_get_log_file("SimpleEthernetReceiverFmu.BusTransfer.pcapng"))

    assert result.isError is False
    assert result.content is not None
    resource_link = cast(ResourceLink, result.content[0])
    assert str(resource_link.uri) == "logs://bus/SimpleEthernetReceiverFmu.BusTransfer.pcapng"
    assert resource_link.mimeType == "application/vnd.tcpdump.pcap"


def test_tool_veos_get_log_file_returns_sim_resource_link_for_text_log() -> None:
    result = cast(CallToolResult, veos_get_log_file("veos.log"))

    assert result.isError is False
    assert result.content is not None
    resource_link = cast(ResourceLink, result.content[0])
    assert str(resource_link.uri) == "logs://sim/veos.log"
    assert resource_link.mimeType == "text/plain"
    assert result.structuredContent == {
        "Success": True,
        "Code": CommandResultCode.OK.value,
        "LogFileName": "veos.log",
        "Uri": "logs://sim/veos.log",
        "MimeType": "text/plain",
        "Description": "VEOS simulation log file in plain text format.",
    }


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

    assert result.isError is False
    assert cli.sim_calls == [("show-log",)]
    assert result.structuredContent is not None
    assert_command_result_structured_content("veos_list_all_available_log_files", result.structuredContent)


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

    assert result.isError is True
    assert cli.sim_calls == [("show-log",)]
    assert result.structuredContent is not None
    assert_command_result_structured_content("veos_list_all_available_log_files", result.structuredContent)
    assert_error_text_content(result, "Failed to retrieve the list of available log files.")
