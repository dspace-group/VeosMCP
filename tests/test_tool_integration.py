"""Integration-style tests for VEOS MCP tools and log file resources."""

from __future__ import annotations

import asyncio
from typing import cast

from mcp.server.lowlevel.helper_types import ReadResourceContents
from mcp.types import CallToolResult, ResourceLink

from veos_mcp import runtime
from veos_mcp.schemas.cli_command_result import CliCommandResult, CommandResultCode

import veos_mcp.resources.log_files
import veos_mcp.tools.log_file_access
import veos_mcp.tools.sim_control


class RecordingVeosCliMock:
    def __init__(self, result: CliCommandResult) -> None:
        self._result = result
        self.calls: list[tuple[str, ...]] = []

    def run_sim(self, *arguments: str) -> CliCommandResult:
        self.calls.append(arguments)
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


def test_tool_veos_status_info_invokes_veos_sim_and_returns_structured_content(
    monkeypatch,
) -> None:
    cli = RecordingVeosCliMock(
        CliCommandResult(
            success=True,
            exit_code=0,
            code=CommandResultCode.OK,
            stdout="mock status info",
            stdout_bytes=b"mock status info",
            stderr="",
        )
    )
    monkeypatch.setattr(runtime, "_veos_cli", cli)

    result = cast(CallToolResult, asyncio.run(runtime.mcp.call_tool("veos_status_info", {})))

    assert result.isError is False, "Expected tool call to succeed."
    assert cli.calls == [("info",)]
    assert result.structuredContent is not None, (
        "Expected structured content in the tool result."
    )
    assert_command_result_structured_content(
        "veos_status_info",
        result.structuredContent,
    )


def test_tool_veos_get_log_file_returns_bus_resource_link_for_pcapng(
    monkeypatch,
) -> None:
    cli = RecordingVeosCliMock(
        CliCommandResult(
            success=True,
            exit_code=0,
            code=CommandResultCode.OK,
            stdout="",
            stdout_bytes=b"pcap-bytes",
            stderr="",
        )
    )
    monkeypatch.setattr(runtime, "_veos_cli", cli)

    result = cast(
        CallToolResult,
        asyncio.run(
            runtime.mcp.call_tool(
            "veos_get_log_file",
            {"logFileName": "SimpleEthernetReceiverFmu.BusTransfer.pcapng"},
            )
        ),
    )

    assert result.isError is False
    assert result.content is not None
    resource_link = cast(ResourceLink, result.content[0])
    assert str(resource_link.uri) == "logs://bus/SimpleEthernetReceiverFmu.BusTransfer.pcapng"
    assert resource_link.mimeType == "application/vnd.tcpdump.pcap"


def test_resource_veos_bus_log_file_returns_binary_contents(monkeypatch) -> None:
    cli = RecordingVeosCliMock(
        CliCommandResult(
            success=True,
            exit_code=0,
            code=CommandResultCode.OK,
            stdout="ignored text",
            stdout_bytes=b"pcap-bytes",
            stderr="",
        )
    )
    monkeypatch.setattr(runtime, "_veos_cli", cli)

    result = asyncio.run(
        runtime.mcp.read_resource(
            "logs://bus/SimpleEthernetReceiverFmu.BusTransfer.pcapng"
        )
    )

    contents = cast(list[ReadResourceContents], list(result))
    assert len(contents) == 1
    assert contents[0].content == b"pcap-bytes"
    assert contents[0].mime_type == "application/vnd.tcpdump.pcap"
    assert cli.calls == [("show-log", "SimpleEthernetReceiverFmu.BusTransfer.pcapng")]


def test_resource_veos_sim_log_file_returns_text_contents(monkeypatch) -> None:
    cli = RecordingVeosCliMock(
        CliCommandResult(
            success=True,
            exit_code=0,
            code=CommandResultCode.OK,
            stdout="simulation log text",
            stdout_bytes=b"simulation log text",
            stderr="",
        )
    )
    monkeypatch.setattr(runtime, "_veos_cli", cli)

    result = asyncio.run(runtime.mcp.read_resource("logs://sim/veos.log"))

    contents = cast(list[ReadResourceContents], list(result))
    assert len(contents) == 1
    assert contents[0].content == "simulation log text"
    assert contents[0].mime_type == "text/plain"
    assert cli.calls == [("show-log", "veos.log")]