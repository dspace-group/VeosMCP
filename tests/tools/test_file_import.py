"""Tests for the VEOS file import tool."""

import json
from pathlib import Path
from typing import cast

from mcp.types import CallToolResult, TextContent

from veos_mcp import runtime
from veos_mcp.models.import_result import ImportResult
from veos_mcp.tools.file_import import veos_import_file


class AutomationMock:
    def __init__(self, result: ImportResult | Exception) -> None:
        self.result = result
        self.import_calls: list[tuple[str, str]] = []

    def import_file(self, osa_path: str, import_file_path: str) -> ImportResult:
        self.import_calls.append((osa_path, import_file_path))
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


def create_import_result(*, success: bool) -> ImportResult:
    return ImportResult(
        success=success,
        osa_path=str(Path("target.osa").resolve()),
        imported_file_path=str(Path("model.fmu").resolve()),
        build_status="valid" if success else "invalid",
        build_output="build output",
        imported_application_processes=["ImportedModel"] if success else [],
    )


def test_import_file_returns_structured_build_result(monkeypatch) -> None:
    automation = AutomationMock(create_import_result(success=True))
    monkeypatch.setattr(runtime, "_veos_automation", automation)

    result = cast(CallToolResult, veos_import_file("target.osa", "model.fmu"))

    assert automation.import_calls == [("target.osa", "model.fmu")]
    assert result.isError is False
    assert result.structuredContent is not None
    assert result.structuredContent["Success"] is True
    assert result.structuredContent["BuildStatus"] == "valid"
    assert result.structuredContent["BuildOutput"] == "build output"


def test_import_file_returns_build_details_on_invalid_build(monkeypatch) -> None:
    automation = AutomationMock(create_import_result(success=False))
    monkeypatch.setattr(runtime, "_veos_automation", automation)

    result = cast(CallToolResult, veos_import_file("target.osa", "model.fmu"))

    assert result.isError is True
    assert result.structuredContent is not None
    assert result.structuredContent["Success"] is False
    assert result.structuredContent["BuildOutput"] == "build output"
    text_content = cast(TextContent, result.content[0])
    assert (
        json.loads(text_content.text)["Message"]
        == "VEOS could not build and import file model.fmu. See BuildOutput for details."
    )


def test_import_file_returns_error_when_automation_fails(monkeypatch) -> None:
    automation = AutomationMock(RuntimeError("COM unavailable"))
    monkeypatch.setattr(runtime, "_veos_automation", automation)

    result = cast(CallToolResult, veos_import_file("target.osa", "model.fmu"))

    assert result.isError is True
    text_content = cast(TextContent, result.content[0])
    assert json.loads(text_content.text)["Message"] == "Failed to import file model.fmu into VEOS: COM unavailable"
