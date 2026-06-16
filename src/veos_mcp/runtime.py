"""Shared FastMCP runtime state and response helpers for the VEOS MCP server."""

import sys

from mcp.server import FastMCP

from mcp.types import CallToolResult, TextContent

from veos_mcp.models.cli_command_result import CliCommandResult
from veos_mcp.models.errors import VeosError, ErrorType
from veos_mcp.veos_cli import VeosCli
from veos_mcp.veos_path_resolver import (
    check_veos_installation_exists,
    get_linux_installations,
    get_windows_installations,
    resolve_veos_path_for_version,
)

mcp = FastMCP(
    name="VEOS MCP Server",
    instructions="Tools for controlling the dSPACE VEOS simulator.",
    json_response=True,
)

_veos_cli: VeosCli | None = None


def configure(*, veos_version: str | None, veos_bin_path: str | None) -> None:
    """Configure the server with the VEOS CLI installation directory."""

    veos_installations = (
        get_windows_installations()
        if sys.platform.startswith("win32")
        else get_linux_installations()
    )

    if veos_bin_path is not None:
        veos_path = check_veos_installation_exists(veos_installations, veos_bin_path)
    else:
        veos_path = resolve_veos_path_for_version(veos_installations, veos_version)

    global _veos_cli
    _veos_cli = VeosCli(veos_path=veos_path)


def get_cli() -> VeosCli:
    """Return the configured VEOS CLI facade."""
    if _veos_cli is None:
        raise RuntimeError("VEOS CLI is not configured.")
    return _veos_cli


def _create_error(
    message: str,
    error_type: ErrorType = ErrorType.PERMANENT_ERROR,
) -> VeosError:
    """Create a typed MCP-facing error payload."""
    return VeosError(Type=error_type, Message=message)


def create_error_response(message: str) -> CallToolResult:
    """Create a typed MCP-facing error result."""
    error = _create_error(message)
    return CallToolResult(
        isError=True,
        content=[TextContent(type="text", text=error.model_dump_json(by_alias=True))],
        structuredContent=error.model_dump(by_alias=True, mode="json"),
    )


def create_command_result_response_error(
    command_result: CliCommandResult,
    error_message: str,
) -> CallToolResult:
    """Convert a VEOS CLI command result into an MCP tool result."""
    error = _create_error(error_message)
    return CallToolResult(
        isError=not command_result.success,
        content=[TextContent(type="text", text=error.model_dump_json(by_alias=True))],
        structuredContent=command_result.to_structured_content(),
    )


def create_command_result_response_success(
    command_result: CliCommandResult,
) -> CallToolResult:
    """Convert a VEOS CLI command result into an MCP tool result."""
    return CallToolResult(
        isError=not command_result.success,
        content=[TextContent(type="text", text="Tool Call succeeded.")],
        structuredContent=command_result.to_structured_content(),
    )
