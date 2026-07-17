"""Structured result from a VEOS Player file import."""

from typing import Any

from pydantic import BaseModel, Field


class ImportResult(BaseModel):
    """Result returned by the VEOS Player automation import API."""

    success: bool = Field(serialization_alias="Success")
    osa_path: str = Field(serialization_alias="OsaPath")
    imported_file_path: str = Field(serialization_alias="ImportedFilePath")
    build_status: str = Field(serialization_alias="BuildStatus")
    build_output: str = Field(serialization_alias="BuildOutput")
    imported_application_processes: list[str] = Field(serialization_alias="ImportedApplicationProcesses")

    def to_structured_content(self) -> dict[str, Any]:
        return self.model_dump(by_alias=True, mode="json")
