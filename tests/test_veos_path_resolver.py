"""Tests for VEOS installation resolution and CLI initialization."""

from pathlib import Path

import pytest

import veos_mcp.veos_path_resolver as path_resolver


def _installation(year: int, release: str, path: str) -> path_resolver._VeosInstallation:
    return path_resolver._VeosInstallation(
        year=year,
        release=release,
        bin_path=Path(path),
        source_name=f"dSPACE VEOS {year}-{release}",
    )


def test_select_installation_maps_numeric_release_aliases() -> None:
    installations = [
        _installation(2026, "B", "C:/VEOS/2026B/bin"),
        _installation(2026, "A", "C:/VEOS/2026A/bin"),
    ]

    assert path_resolver._select_installation(installations, "26.1").release == "A"
    assert path_resolver._select_installation(installations, "2026-B").release == "B"


def test_select_installation_uses_newest_version_when_unspecified() -> None:
    installations = [
        _installation(2026, "B", "C:/VEOS/2026B/bin"),
        _installation(2027, "A", "C:/VEOS/2027A/bin"),
        _installation(2027, "A", "C:/VEOS/2025A/bin"),
    ]

    selected = path_resolver._select_installation(installations, None)

    assert selected.year == 2027
    assert selected.release == "A"


def test_installation_exposes_version_specific_automation_identifier() -> None:
    installation = _installation(2026, "B", "C:/VEOS/2026B/bin")

    assert installation.automation_programmatic_identifier == "VeosPlayer.Application.2026-B"


def test_select_installation_reports_available_versions() -> None:
    installations = [_installation(2026, "A", "C:/VEOS/2026A/bin")]

    with pytest.raises(RuntimeError) as exc_info:
        path_resolver._select_installation(installations, "26.2")

    assert "2026-A" in str(exc_info.value)


def test_select_installation_reports_error_when_no_installations_available() -> None:
    installations = []

    with pytest.raises(RuntimeError) as exc_info:
        path_resolver._select_installation(installations, "26.2")

    assert "Could not find any installed dSPACE VEOS instances on the machine." in str(exc_info.value)
