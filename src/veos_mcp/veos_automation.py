"""VEOS Player COM automation helpers."""

import sys
from collections.abc import Callable, Iterator
from contextlib import AbstractContextManager, contextmanager
from pathlib import Path
from threading import Lock
from typing import Any

from veos_mcp.models.import_result import ImportResult

_AUTOMATION_GATE = Lock()
_VALID_BUILD_STATUS = 0


@contextmanager
def _initialized_com() -> Iterator[None]:
    if not sys.platform.startswith("win32"):
        raise RuntimeError("VEOS Player COM automation is available only on Windows.")

    import pythoncom

    pythoncom.CoInitialize()
    try:
        yield
    finally:
        pythoncom.CoUninitialize()


def _dispatch_player(programmatic_identifier: str) -> Any:
    from win32com.client import Dispatch

    return Dispatch(programmatic_identifier)


class VeosAutomation:
    """Facade for serialized access to the VEOS Player automation API."""

    def __init__(
        self,
        *,
        programmatic_identifier: str,
        dispatch_player: Callable[[str], Any] = _dispatch_player,
        com_context: Callable[[], AbstractContextManager[None]] = _initialized_com,
    ) -> None:
        self.programmatic_identifier = programmatic_identifier
        self._dispatch_player = dispatch_player
        self._com_context = com_context

    def import_file(self, osa_path: str, import_file_path: str) -> ImportResult:
        """Import a VEOS-supported file into an OSA and save valid changes."""
        resolved_osa_path = str(Path(osa_path).resolve())
        resolved_import_file_path = str(Path(import_file_path).resolve())

        with _AUTOMATION_GATE, self._com_context():
            player = self._dispatch_player(self.programmatic_identifier)
            project = player.Projects.Open(resolved_osa_path)
            if project is None:
                raise RuntimeError(f"VEOS Player could not open the OSA file {resolved_osa_path}.")

            import_settings = project.CreateNewImportSettings()
            import_settings.ImportFilePath = resolved_import_file_path
            build_result = project.Import(import_settings)
            build_status = int(build_result.BuildStatus)
            success = build_status == _VALID_BUILD_STATUS

            if success:
                project.Save(resolved_osa_path)

            return ImportResult(
                success=success,
                osa_path=resolved_osa_path,
                imported_file_path=resolved_import_file_path,
                build_status="valid" if success else "invalid",
                build_output=str(build_result.BuildOutput),
                imported_application_processes=[str(name) for name in build_result.ImportedApplicationProcesses],
            )
