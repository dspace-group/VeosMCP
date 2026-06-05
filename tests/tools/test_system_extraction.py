"""Integration-style tests for VEOS system extraction tools."""

from __future__ import annotations

import json
from typing import cast

from mcp.types import CallToolResult

from veos_mcp import runtime
from veos_mcp.schemas.cli_command_result import CliCommandResult, CommandResultCode
from veos_mcp.tools.system_extraction import veos_get_all_signals_and_ports

class RecordingModelCliMock:
    def __init__(self, result: CliCommandResult) -> None:
        self._result = result
        self.model_calls: list[tuple[str, ...]] = []

    def run_model(self, *arguments: str) -> CliCommandResult:
        self.model_calls.append(arguments)
        return self._result

def test_tool_veos_get_all_signals_and_ports_returns_signal_summary(monkeypatch) -> None:
    cli = RecordingModelCliMock(
        CliCommandResult(
            success=True,
            exit_code=0,
            code=CommandResultCode.OK,
            stdout=json.dumps(
                {
                    "Vpus": [
                        {
                            "Ports": [
                                {
                                    "InSignals": [
                                        {
                                            "ShortElementPath": "/Consumer/In1",
                                            "DataType": "Float64",
                                        }
                                    ],
                                    "OutSignals": [
                                        {
                                            "ShortElementPath": "/Producer/Out1",
                                            "DataType": "Float64",
                                        }
                                    ],
                                    "SignalGroups": [
                                        {
                                            "InSignals": [
                                                {
                                                    "ShortElementPath": "/Consumer/In2",
                                                    "DataType": "UInt8",
                                                }
                                            ],
                                            "OutSignals": [],
                                        }
                                    ],
                                }
                            ]
                        }
                    ],
                    "CommunicationPackages": [
                        {
                            "SignalConnections": [
                                {
                                    "InSignalReference": {"ShortPath": "/Consumer/In1"},
                                    "OutSignalReference": {"ShortPath": "/Producer/Out1"},
                                }
                            ]
                        }
                    ],
                }
            ),
            stdout_bytes=b"",
            stderr="",
        )
    )
    monkeypatch.setattr(runtime, "_veos_cli", cli)

    result = cast(CallToolResult, veos_get_all_signals_and_ports("model.osa"))

    assert result.isError is False
    assert cli.model_calls == [("get", "model.osa")]
    assert result.structuredContent == {
        "InSignals": [
            {"path": "/Consumer/In1", "data_type": "Float64"},
            {"path": "/Consumer/In2", "data_type": "UInt8"},
        ],
        "OutSignals": [
            {"path": "/Producer/Out1", "data_type": "Float64"},
        ],
        "SignalConnections": [
            {
                "InSignalReference": "/Consumer/In1",
                "OutSignalReference": "/Producer/Out1",
            }
        ],
    }


def test_tool_veos_get_all_signals_and_ports_returns_error_on_cli_failure(monkeypatch) -> None:
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

    result = cast(CallToolResult, veos_get_all_signals_and_ports("model.osa"))

    assert result.isError is True
    assert cli.model_calls == [("get", "model.osa")]
    assert result.structuredContent == {
        "Type": "PermanentError",
        "Message": "Failed to get the list of signals from the VEOS model.",
    }