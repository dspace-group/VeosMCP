"""Tests for the VEOS file import tool."""

from typing import cast

import pytest
from mcp.types import CallToolResult

from tests.tool_test_helpers import RecordingBuildCliMock, RecordingModelCliMock, assert_error_text_content
from veos_mcp import runtime
from veos_mcp.models.cli_command_result import CliCommandResult, CommandResultCode
from veos_mcp.tools.file_import import veos_import_file


def create_command_result(*, success: bool = True) -> CliCommandResult:
    return CliCommandResult(
        success=success,
        exit_code=0 if success else 1,
        code=CommandResultCode.OK if success else CommandResultCode.PROCESS_FAILED,
        stdout="imported" if success else "",
        stderr="" if success else "failed",
    )


@pytest.mark.parametrize(
    ("import_file_path", "expected_build_type"),
    [
        ("model.fmu", "fmu"),
        ("model.sic", "sic"),
        ("model.bsc", "bsc"),
        ("model.smc", "smc"),
    ],
)
def test_import_file_infers_and_builds_container_type(monkeypatch, import_file_path: str, expected_build_type: str) -> None:
    cli = RecordingBuildCliMock(create_command_result())
    monkeypatch.setattr(runtime, "_veos_cli", cli)

    result = cast(CallToolResult, veos_import_file("target.osa", import_file_path))

    assert cli.build_calls == [(expected_build_type, import_file_path, "--output-file", "target.osa")]
    assert result.isError is False


@pytest.mark.parametrize("file_type", ["classic-vecu", "adaptive-vecu"])
def test_import_file_builds_explicit_vecu_type(monkeypatch, file_type: str) -> None:
    cli = RecordingBuildCliMock(create_command_result())
    monkeypatch.setattr(runtime, "_veos_cli", cli)

    result = cast(CallToolResult, veos_import_file("target.osa", "model.vecu", file_type))

    assert cli.build_calls == [(file_type, "model.vecu", "--output-file", "target.osa")]
    assert result.isError is False


@pytest.mark.parametrize("import_file_path", ["source.osa", "participant.json"])
def test_import_file_uses_model_console_for_osa_and_json(monkeypatch, import_file_path: str) -> None:
    cli = RecordingModelCliMock(create_command_result())
    monkeypatch.setattr(runtime, "_veos_cli", cli)

    result = cast(CallToolResult, veos_import_file("target.osa", import_file_path))

    assert cli.model_calls == [
        ("import", "target.osa", "--path", import_file_path, "--save-only-on-success")
    ]
    assert result.isError is False


def test_import_file_requires_explicit_type_for_vecu(monkeypatch) -> None:
    result = cast(CallToolResult, veos_import_file("target.osa", "model.vecu"))

    assert result.isError is True
    assert_error_text_content(
        result,
        "Could not determine the VEOS import type for model.vecu. "
        "Specify file_type; VECU files require classic-vecu or adaptive-vecu.",
    )


def test_import_file_returns_command_error(monkeypatch) -> None:
    cli = RecordingBuildCliMock(create_command_result(success=False))
    monkeypatch.setattr(runtime, "_veos_cli", cli)

    result = cast(CallToolResult, veos_import_file("target.osa", "model.fmu"))

    assert result.isError is True
    assert_error_text_content(result, "Failed to import file model.fmu into VEOS OSA target.osa.")
