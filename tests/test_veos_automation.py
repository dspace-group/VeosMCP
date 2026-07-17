"""Tests for VEOS Player COM automation helpers."""

from contextlib import nullcontext
from pathlib import Path
from types import SimpleNamespace

import pytest

from veos_mcp.veos_automation import VeosAutomation


class RecordingProject:
    def __init__(self, build_status: int) -> None:
        self.import_settings = SimpleNamespace(ImportFilePath=None)
        self.build_result = SimpleNamespace(
            BuildStatus=build_status,
            BuildOutput="build output",
            ImportedApplicationProcesses=["ImportedModel"],
        )
        self.import_calls: list[object] = []
        self.save_calls: list[str] = []

    def CreateNewImportSettings(self):
        return self.import_settings

    def Import(self, import_settings):
        self.import_calls.append(import_settings)
        return self.build_result

    def Save(self, osa_path: str) -> None:
        self.save_calls.append(osa_path)


@pytest.mark.parametrize(("build_status", "expected_success"), [(0, True), (1, False)])
def test_import_file_uses_veos_player_automation_and_saves_only_valid_builds(
    tmp_path: Path,
    build_status: int,
    expected_success: bool,
) -> None:
    osa_path = tmp_path / "target.osa"
    import_file_path = tmp_path / "model.fmu"
    project = RecordingProject(build_status)
    projects = SimpleNamespace(Open=lambda path: project)
    player = SimpleNamespace(Projects=projects)
    dispatched_identifiers: list[str] = []

    automation = VeosAutomation(
        programmatic_identifier="VeosPlayer.Application.2026-A",
        dispatch_player=lambda identifier: (dispatched_identifiers.append(identifier), player)[1],
        com_context=nullcontext,
    )

    result = automation.import_file(str(osa_path), str(import_file_path))

    resolved_osa_path = str(osa_path.resolve())
    assert dispatched_identifiers == ["VeosPlayer.Application.2026-A"]
    assert project.import_settings.ImportFilePath == str(import_file_path.resolve())
    assert project.import_calls == [project.import_settings]
    assert project.save_calls == ([resolved_osa_path] if expected_success else [])
    assert result.success is expected_success
    assert result.build_status == ("valid" if expected_success else "invalid")
    assert result.imported_application_processes == ["ImportedModel"]
