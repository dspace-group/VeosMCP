"""Pydantic schema for VEOS CLI command execution results."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class CommandResultCode(str, Enum):
    """Normalized result codes for underlying VEOS process execution."""

    OK = "ok"
    PROCESS_FAILED = "process_failed"
    PROCESS_START_FAILED = "process_start_failed"
    PROCESS_TIMED_OUT = "process_timed_out"


class CliCommandResult(BaseModel):
    """Structured command result returned to MCP clients."""

    success: bool = Field(serialization_alias="Success")
    exit_code: int | None = Field(serialization_alias="ExitCode")
    code: CommandResultCode = Field(serialization_alias="Code")
    stdout: str = Field(serialization_alias="Stdout")
    stdout_bytes: bytes = Field(default=b"", exclude=True, repr=False)
    stderr: str = Field(serialization_alias="Stderr")

    def to_structured_content(self) -> dict[str, Any]:
        return self.model_dump(by_alias=True, exclude={"stdout_bytes"}, mode="json")
