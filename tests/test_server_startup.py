"""Startup tests for the MCP server."""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from veos_mcp import server
from veos_mcp.veos_cli import VeosInstallation


def create_installation(tmp_path: Path) -> VeosInstallation:
    return VeosInstallation(
        year=2026,
        release="A",
        bin_path=tmp_path / "bin",
        source_name="dSPACE VEOS 2026-A",
    )


def patch_veos_installation_discovery(installations: list[VeosInstallation]):
    discovery_target = (
        "veos_mcp.runtime.get_windows_installations" if sys.platform.startswith("win32") else "veos_mcp.runtime.get_linux_installations"
    )
    return patch(discovery_target, return_value=installations)


def test_skip_configure_environment_variable_skips_configure(monkeypatch) -> None:
    monkeypatch.setenv("VEOS_MCP_SKIP_CONFIGURE", "1")

    with patch("veos_mcp.server.configure_cli") as mock_configure, patch.object(server.mcp, "run") as mock_run:
        server.main([])

    mock_configure.assert_not_called()
    mock_run.assert_called_once()


def test_argument_veos_bin_path_invalid(tmp_path: Path) -> None:
    """Test the direct server entrypoint error when the --veos-bin-path argument is invalid."""
    with patch_veos_installation_discovery([create_installation(tmp_path)]), pytest.raises(ValueError) as exc_info:
        server.main(["--veos-bin-path", "invalid_path"])

    assert "path is invalid" in str(exc_info.value)
    assert "invalid_path" in str(exc_info.value)


def test_argument_veos_version_invalid(tmp_path: Path) -> None:
    """Test the direct server entrypoint error when the --veos-version argument is invalid."""

    with patch_veos_installation_discovery([create_installation(tmp_path)]), pytest.raises(ValueError) as exc_info:
        server.main(["--veos-version", "invalid_version"])

    assert "Invalid VEOS version format" in str(exc_info.value)


def test_argument_unknown() -> None:
    """Test the direct server entrypoint error when an unknown argument is provided."""

    with pytest.raises(SystemExit) as exc_info:
        server.main(["--veos-version", "26-A", "--unknown-argument", "value"])

    assert exc_info.value.code == 2
