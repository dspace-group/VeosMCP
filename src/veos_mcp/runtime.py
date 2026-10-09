"""Shared FastMCP runtime state and response helpers for the VEOS MCP server."""

import sys

from mcp.server import MCPServer
from mcp.types import CallToolResult, TextContent

from veos_mcp.models.cli_command_result import CliCommandResult
from veos_mcp.models.errors import ErrorType, VeosError
from veos_mcp.veos_cli import VeosCli
from veos_mcp.veos_path_resolver import (
    get_installation_for_bin_path,
    get_installation_for_version,
    get_linux_installations,
    get_windows_installations,
)

mcp = MCPServer(
    name="VEOS MCP Server",
    instructions="Tools for controlling the dSPACE VEOS simulator.",
)

_veos_cli: VeosCli | None = None


def configure_cli(*, veos_version: str | None, veos_bin_path: str | None) -> None:
    """Configure the server with the VEOS CLI installation directory."""

    veos_installations = get_windows_installations() if sys.platform.startswith("win32") else get_linux_installations()

    if veos_bin_path is not None:
        installation = get_installation_for_bin_path(veos_installations, veos_bin_path)
    else:
        # veos_version can be None as well, will pick newest VEOS installation
        installation = get_installation_for_version(veos_installations, veos_version)

    global _veos_cli
    _veos_cli = VeosCli(installation=installation)


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
        is_error=True,
        content=[TextContent(type="text", text=error.model_dump_json(by_alias=True))],
        structured_content=error.model_dump(by_alias=True, mode="json"),
    )


def create_command_result_response_error(
    command_result: CliCommandResult,
    error_message: str,
) -> CallToolResult:
    """Convert a VEOS CLI command result into an MCP tool result."""
    error = _create_error(error_message)
    return CallToolResult(
        is_error=not command_result.success,
        content=[TextContent(type="text", text=error.model_dump_json(by_alias=True))],
        structured_content=command_result.to_structured_content(),
    )


def create_command_result_response_success(
    command_result: CliCommandResult,
) -> CallToolResult:
    """Convert a VEOS CLI command result into an MCP tool result."""
    return CallToolResult(
        is_error=not command_result.success,
        content=[TextContent(type="text", text="Tool Call succeeded.")],
        structured_content=command_result.to_structured_content(),
    )
