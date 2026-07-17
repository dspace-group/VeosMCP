"""Tests for VEOS CLI subprocess routing."""

from pathlib import Path
from unittest.mock import patch

from veos_mcp.models.cli_command_result import CliCommandResult, CommandResultCode
from veos_mcp.veos_cli import VeosCli


def test_run_build_uses_build_command_and_build_timeout() -> None:
    expected_result = CliCommandResult(
        success=True,
        exit_code=0,
        code=CommandResultCode.OK,
        stdout="built",
        stderr="",
    )
    cli = VeosCli(
        veos_path=Path("C:/VEOS/veos.exe"),
        command_timeout_seconds=40,
        build_command_timeout_seconds=600,
    )

    with patch("veos_mcp.veos_cli.run_process_command", return_value=expected_result) as run_command:
        result = cli.run_build("fmu", "model.fmu", "--output-file", "target.osa")

    assert result is expected_result
    run_command.assert_called_once_with(
        Path("C:/VEOS/veos.exe"),
        ("build", "fmu", "model.fmu", "--output-file", "target.osa"),
        command_timeout_seconds=600,
    )