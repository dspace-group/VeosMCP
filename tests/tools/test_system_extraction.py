"""Integration-style tests for VEOS system extraction tools."""

import json
import tempfile
from pathlib import Path
from typing import cast

from mcp.types import CallToolResult

from tests.tool_test_helpers import RecordingModelCliMock
from veos_mcp import runtime
from veos_mcp.models.cli_command_result import CliCommandResult, CommandResultCode
from veos_mcp.tools.system_extraction import (
    veos_get_all_signals_and_ports,
    veos_get_full_simulation_system_data_model,
)


def _create_successful_result(stdout: str) -> CliCommandResult:
    return CliCommandResult(
        success=True,
        exit_code=0,
        code=CommandResultCode.OK,
        stdout=stdout,
        stdout_bytes=b"",
        stderr="",
    )


def test_tool_veos_get_full_simulation_system_data_model_writes_server_temp_file(monkeypatch, tmp_path) -> None:
    data_model = {"Vpus": [{"Name": "Vpu1"}], "Version": "1.0"}
    cli = RecordingModelCliMock(_create_successful_result(json.dumps(data_model)))
    monkeypatch.setattr(runtime, "_veos_cli", cli)
    monkeypatch.setattr(tempfile, "gettempdir", lambda: str(tmp_path))

    result = cast(CallToolResult, veos_get_full_simulation_system_data_model("C:/models/my_system.osa"))

    assert result.is_error is False
    assert cli.model_calls == [("get", "C:/models/my_system.osa")]
    assert result.structured_content is not None
    written_path = Path(cast(str, result.structured_content["JsonFilePath"]))
    assert written_path.parent == (tmp_path / "veos_mcp").resolve()
    assert written_path.name.startswith("my_system_data_model_")
    assert written_path.suffix == ".json"
    assert json.loads(written_path.read_text(encoding="utf-8")) == data_model
    assert result.structured_content == {
        "Success": True,
        "JsonFilePath": str(written_path),
        "SizeBytes": written_path.stat().st_size,
        "TopLevelEntries": {"Vpus": 1, "Version": 1},
    }
    assert [path.name for path in written_path.parent.iterdir()] == [written_path.name]


def test_tool_veos_get_full_simulation_system_data_model_creates_unique_temp_files(monkeypatch, tmp_path) -> None:
    cli = RecordingModelCliMock(_create_successful_result("{}"))
    monkeypatch.setattr(runtime, "_veos_cli", cli)
    monkeypatch.setattr(tempfile, "gettempdir", lambda: str(tmp_path))

    first_result = cast(CallToolResult, veos_get_full_simulation_system_data_model("model.osa"))
    second_result = cast(CallToolResult, veos_get_full_simulation_system_data_model("model.osa"))

    assert first_result.structured_content is not None
    assert second_result.structured_content is not None
    assert first_result.structured_content["JsonFilePath"] != second_result.structured_content["JsonFilePath"]


def test_tool_veos_get_full_simulation_system_data_model_returns_error_on_invalid_json(monkeypatch, tmp_path) -> None:
    cli = RecordingModelCliMock(_create_successful_result("not json"))
    monkeypatch.setattr(runtime, "_veos_cli", cli)

    result = cast(CallToolResult, veos_get_full_simulation_system_data_model("model.osa"))

    assert result.is_error is True
    assert result.structured_content is not None
    assert result.structured_content["Type"] == "PermanentError"


def test_tool_veos_get_full_simulation_system_data_model_returns_error_on_cli_failure(monkeypatch, tmp_path) -> None:
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

    result = cast(CallToolResult, veos_get_full_simulation_system_data_model("model.osa"))

    assert result.is_error is True
    assert cli.model_calls == [("get", "model.osa")]
    assert result.structured_content is not None
    assert result.structured_content["Success"] is False
    assert result.structured_content["Stderr"] == "failed"


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

    assert result.is_error is False
    assert cli.model_calls == [("get", "model.osa")]
    assert result.structured_content == {
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

    assert result.is_error is True
    assert cli.model_calls == [("get", "model.osa")]
    assert result.structured_content is not None
