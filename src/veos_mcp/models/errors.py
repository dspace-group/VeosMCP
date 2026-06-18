"""Pydantic schema for MCP-facing VEOS errors."""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class ErrorType(StrEnum):
    """Classify whether a tool failure is transient or permanent."""

    TRANSIENT_ERROR = "TransientError"
    PERMANENT_ERROR = "PermanentError"


class VeosError(BaseModel):
    """Error payload serialized into tool text content on failures."""

    model_config = ConfigDict(populate_by_name=True)

    error_type: ErrorType = Field(alias="Type")
    message: str = Field(alias="Message")
