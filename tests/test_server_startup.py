"""Startup tests for the MCP server."""

import sys
from pathlib import Path
from unittest.mock import patch, ANY

import pytest

from veos_mcp import server
from veos_mcp import veos_path_resolver


def create_fake_veos_executable(tmp_path: Path) -> Path:
    """Create a minimal VEOS stub executable for subprocess-based MCP tests."""
    if sys.platform.startswith("win"):
        veos_path = tmp_path / "veos.cmd"
        veos_path.write_text("@echo off\r\nexit /b 0\r\n", encoding="utf-8")
        return veos_path

    veos_path = tmp_path / "veos"
    veos_path.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    veos_path.chmod(0o755)
    return veos_path


def create_installation(bin_path: Path) -> veos_path_resolver._VeosInstallation:
    return veos_path_resolver._VeosInstallation(
        year=2026,
        release="A",
        bin_path=bin_path / "veos.exe"
        if sys.platform.startswith("win")
        else bin_path / "veos",
        source_name="test-installation",
    )


def test_argument_no_veos_version_calls_select_installation(tmp_path: Path) -> None:
    with patch("veos_mcp.veos_path_resolver._select_installation") as mock_select:
        with patch.object(server.mcp, "run") as mock_run:
            mock_select.return_value = create_installation(
                create_fake_veos_executable(tmp_path)
            )

            server.main([])

    mock_select.assert_called_once_with(ANY, None)
    mock_run.assert_called_once_with()


def test_argument_veos_version_calls_select_installation(tmp_path: Path) -> None:
    with patch("veos_mcp.veos_path_resolver._select_installation") as mock_select:
        with patch.object(server.mcp, "run") as mock_run:
            mock_select.return_value = create_installation(
                create_fake_veos_executable(tmp_path)
            )

            server.main(["--veos-version", "26.1"])

    mock_select.assert_called_once_with(ANY, "26.1")
    mock_run.assert_called_once_with()


def test_skip_configure_environment_variable_skips_configure(monkeypatch) -> None:
    monkeypatch.setenv("VEOS_MCP_SKIP_CONFIGURE", "1")

    with patch("veos_mcp.server.configure") as mock_configure:
        with patch.object(server.mcp, "run") as mock_run:
            server.main([])

    mock_configure.assert_not_called()
    mock_run.assert_called_once_with()


def test_argument_veos_bin_path_invalid() -> None:
    """Test the direct server entrypoint error when the --veos-bin-path argument is invalid."""
    with pytest.raises(ValueError) as exc_info:
        server.main(["--veos-bin-path", "invalid_path"])

    assert "path is invalid" in str(exc_info.value)
    assert "invalid_path" in str(exc_info.value)


def test_argument_veos_version_invalid() -> None:
    """Test the direct server entrypoint error when the --veos-version argument is invalid."""

    with pytest.raises(ValueError) as exc_info:
        server.main(["--veos-version", "invalid_version"])

    assert "Invalid VEOS version format" in str(exc_info.value)


def test_argument_unknown() -> None:
    """Test the direct server entrypoint error when an unknown argument is provided."""

    with pytest.raises(SystemExit) as exc_info:
        server.main(["--veos-version", "26-A", "--unknown-argument", "value"])

    assert exc_info.value.code == 2
