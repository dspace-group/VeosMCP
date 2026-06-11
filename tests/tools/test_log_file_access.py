"""Integration-style tests for VEOS log file access tools"""

import json
from typing import cast

from mcp.types import CallToolResult, ResourceLink, TextContent

from veos_mcp import runtime

from veos_mcp.models.cli_command_result import CliCommandResult, CommandResultCode
from veos_mcp.tools.log_file_access import (
    veos_get_log_file,
    veos_list_all_available_log_files,
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


def test_tool_veos_get_log_file_returns_bus_resource_link_for_pcapng() -> None:
    result = cast(
        CallToolResult,
        veos_get_log_file("SimpleEthernetReceiverFmu.BusTransfer.pcapng"),
    )

    assert result.isError is False
    assert result.content is not None
    resource_link = cast(ResourceLink, result.content[0])
    assert (
        str(resource_link.uri)
        == "logs://bus/SimpleEthernetReceiverFmu.BusTransfer.pcapng"
    )
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
    assert_command_result_structured_content(
        "veos_list_all_available_log_files",
        result.structuredContent,
    )


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
    assert_command_result_structured_content(
        "veos_list_all_available_log_files",
        result.structuredContent,
    )
    assert_error_text_content(
        result, "Failed to retrieve the list of available log files."
    )
