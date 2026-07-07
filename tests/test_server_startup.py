"""Startup tests for the MCP server."""

import sys
from pathlib import Path
from unittest.mock import ANY, patch

import pytest

import veos_mcp.veos_path_resolver as path_resolver
from veos_mcp import server


def create_installation(tmp_path: Path) -> path_resolver._VeosInstallation:
    return path_resolver._VeosInstallation(
        year=2026,
        release="A",
        bin_path=tmp_path / "bin",
        source_name="dSPACE VEOS 2026-A",
    )


def patch_veos_installation_discovery(installations: list[path_resolver._VeosInstallation]):
    discovery_target = (
        "veos_mcp.runtime.get_windows_installations" if sys.platform.startswith("win32") else "veos_mcp.runtime.get_linux_installations"
    )
    return patch(discovery_target, return_value=installations)


def test_argument_no_veos_version_calls_select_installation(tmp_path: Path) -> None:
    installation = create_installation(tmp_path)

    with patch_veos_installation_discovery([installation]):
        with patch("veos_mcp.veos_path_resolver._select_installation", return_value=installation) as mock_select:
            with patch.object(server.mcp, "run") as mock_run:
                server.main([])

    mock_select.assert_called_once_with(ANY, None)
    mock_run.assert_called_once_with()


def test_argument_veos_version_calls_select_installation(tmp_path: Path) -> None:
    installation = create_installation(tmp_path)

    with patch_veos_installation_discovery([installation]):
        with patch("veos_mcp.veos_path_resolver._select_installation", return_value=installation) as mock_select:
            with patch.object(server.mcp, "run") as mock_run:
                server.main(["--veos-version", "26.1"])

    mock_select.assert_called_once_with(ANY, "26.1")
    mock_run.assert_called_once_with()


def test_skip_configure_environment_variable_skips_configure(monkeypatch) -> None:
    monkeypatch.setenv("VEOS_MCP_SKIP_CONFIGURE", "1")

    with patch("veos_mcp.server.configure_cli") as mock_configure:
        with patch.object(server.mcp, "run") as mock_run:
            server.main([])

    mock_configure.assert_not_called()
    mock_run.assert_called_once_with()


def test_argument_veos_bin_path_invalid(tmp_path: Path) -> None:
    """Test the direct server entrypoint error when the --veos-bin-path argument is invalid."""
    with patch_veos_installation_discovery([create_installation(tmp_path)]):
        with pytest.raises(ValueError) as exc_info:
            server.main(["--veos-bin-path", "invalid_path"])

    assert "path is invalid" in str(exc_info.value)
    assert "invalid_path" in str(exc_info.value)


def test_argument_veos_version_invalid(tmp_path: Path) -> None:
    """Test the direct server entrypoint error when the --veos-version argument is invalid."""

    with patch_veos_installation_discovery([create_installation(tmp_path)]):
        with pytest.raises(ValueError) as exc_info:
            server.main(["--veos-version", "invalid_version"])

    assert "Invalid VEOS version format" in str(exc_info.value)


def test_argument_unknown() -> None:
    """Test the direct server entrypoint error when an unknown argument is provided."""

    with pytest.raises(SystemExit) as exc_info:
        server.main(["--veos-version", "26-A", "--unknown-argument", "value"])

    assert exc_info.value.code == 2
