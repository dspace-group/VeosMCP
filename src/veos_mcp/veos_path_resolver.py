from dataclasses import dataclass
from collections.abc import Iterable
import importlib
from pathlib import Path
import re
import sys

_WINDOWS_INSTALLATION_REFERENCE = (
    "dSPACE.InstallationManager.API, Version=2.0.0.0, Culture=neutral, "
    "PublicKeyToken=f9604847d8afbfbb"
)
_REQUESTED_VERSION_PATTERN = re.compile(
    r"^\s*(?P<year>\d{2}|\d{4})[.\-_ ]?(?P<release>[12abAB])\s*$"
)
_DISPLAY_NAME_PATTERN = re.compile(
    r"^dSPACE\s+VEOS\s+(?P<year>\d{4})-(?P<release>[AB])$",
    re.IGNORECASE,
)
_LINUX_INSTALLATION_PATTERN = re.compile(
    r"^veos(?P<year>\d{4})(?P<release>[ab])$",
    re.IGNORECASE,
)
_RELEASE_ORDER = {"A": 1, "B": 2}


@dataclass(frozen=True)
class _VeosInstallation:
    year: int
    release: str
    bin_path: Path
    source_name: str


def _normalize_release(release: str | None) -> str | None:
    if release is None:
        return None
    normalized = release.upper()
    if normalized == "1":
        return "A"
    if normalized == "2":
        return "B"
    if normalized in _RELEASE_ORDER:
        return normalized
    raise ValueError(f"Unsupported VEOS release suffix: {release}")


def _normalize_year(year: str) -> int:
    year_number = int(year)
    return 2000 + year_number if year_number < 100 else year_number


def _parse_requested_version(veos_version: str | None) -> tuple[int, str | None] | None:
    if veos_version is None or not veos_version.strip():
        return None

    match = _REQUESTED_VERSION_PATTERN.fullmatch(veos_version)
    if match is None:
        raise ValueError(
            "Invalid VEOS version format. Use values like '26.1', '26.2', "
            "'2026-A', or '2026-B'."
        )

    return (
        _normalize_year(match.group("year")),
        _normalize_release(match.group("release")),
    )


def _parse_windows_installation(display_name: str, root_path: str | Path) -> _VeosInstallation | None:
    match = _DISPLAY_NAME_PATTERN.fullmatch(display_name.strip())
    if match is None:
        return None

    return _VeosInstallation(
        year=int(match.group("year")),
        release=match.group("release").upper(),
        bin_path=Path(root_path) / "bin",
        source_name=display_name,
    )


def _parse_linux_installation(bin_path: Path) -> _VeosInstallation | None:
    match = _LINUX_INSTALLATION_PATTERN.fullmatch(bin_path.parent.name)
    if match is None:
        return None

    return _VeosInstallation(
        year=int(match.group("year")),
        release=match.group("release").upper(),
        bin_path=bin_path,
        source_name=bin_path.parent.name,
    )


def _installation_sort_key(installation: _VeosInstallation) -> tuple[int, int]:
    return installation.year, _RELEASE_ORDER[installation.release]


def _format_installation_version(year: int, release: str) -> str:
    return f"{year}-{release}"


def _format_requested_version(year: int, release: str | None) -> str:
    return str(year) if release is None else _format_installation_version(year, release)


def _select_installation(
    installations: Iterable[_VeosInstallation],
    veos_version: str | None,
) -> _VeosInstallation:
    available_installations = sorted(installations, key=_installation_sort_key)
    if not available_installations:
        raise RuntimeError("Could not find any installed dSPACE VEOS instances on the machine.")

    requested_version = _parse_requested_version(veos_version)
    if requested_version is None:
        return available_installations[-1]  # No specific version requested, return the newest available installation.

    requested_year, requested_release = requested_version
    matches = [
        installation
        for installation in available_installations
        if installation.year == requested_year
        and (requested_release is None or installation.release == requested_release)
    ]
    if matches:
        return matches[-1]

    available_versions = ", ".join(
        _format_installation_version(installation.year, installation.release)
        for installation in available_installations
    )
    raise RuntimeError(
        "Could not find the installation of dSPACE VEOS "
        f"{_format_requested_version(requested_year, requested_release)}. "
        f"Available installations: {available_versions}."
    )


def _get_windows_installations() -> list[_VeosInstallation]:
    clr = importlib.import_module("clr")
    clr.AddReference(_WINDOWS_INSTALLATION_REFERENCE)
    installation_api = importlib.import_module("dSPACE.InstallationManager.API")

    configuration_info = installation_api.ConfigurationInfo()
    installations: list[_VeosInstallation] = []
    for installation in configuration_info.Installations:
        parsed_installation = _parse_windows_installation(
            str(installation.DisplayName),
            str(installation.RootPath),
        )
        if parsed_installation is not None:
            installations.append(parsed_installation)
    return installations


def _get_linux_installations(base_path: Path = Path("/opt/dspace")) -> list[_VeosInstallation]:
    installations: list[_VeosInstallation] = []
    for bin_path in base_path.glob("veos????[aAbB]/bin"):
        parsed_installation = _parse_linux_installation(bin_path)
        if parsed_installation is not None:
            installations.append(parsed_installation)
    return installations

def resolve_veos_path(veos_version: str | None) -> Path:
    """Resolve the VEOS bin directory for a requested version or the newest install."""
    installations = (
        _get_windows_installations()
        if sys.platform.startswith("win32")
        else _get_linux_installations()
    )

    candidate_installation = _select_installation(installations, veos_version)
    return candidate_installation.bin_path / "veos.exe" if sys.platform.startswith("win32") else candidate_installation.bin_path / "veos"
