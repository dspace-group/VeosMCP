"""Integration-style tests for MCP server resources."""

from veos_mcp import runtime
from veos_mcp.models.cli_command_result import CliCommandResult, CommandResultCode
from veos_mcp.resources.log_files import (
    veos_get_bus_log_file_resource,
    veos_get_sim_log_file_resource,
)


class RecordingVeosCliMock:
    def __init__(self, sim_result: CliCommandResult) -> None:
        self._sim_result = sim_result
        self.sim_calls: list[tuple[str, ...]] = []

    def run_sim(self, *arguments: str) -> CliCommandResult:
        self.sim_calls.append(arguments)
        return self._sim_result


def test_resource_function_veos_bus_log_file_returns_binary_contents(
    monkeypatch,
) -> None:
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

    result = veos_get_bus_log_file_resource("SimpleEthernetReceiverFmu.BusTransfer.pcapng")

    assert result == b"pcap-bytes"
    assert cli.sim_calls == [("show-log", "SimpleEthernetReceiverFmu.BusTransfer.pcapng")]


def test_resource_function_veos_sim_log_file_returns_text_contents(monkeypatch) -> None:
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

    result = veos_get_sim_log_file_resource("veos.log")

    assert result == "simulation log text"
    assert cli.sim_calls == [("show-log", "veos.log")]
