"""Shared FastMCP runtime state and response helpers for the VEOS MCP server."""

from mcp.server import FastMCP

from mcp.types import CallToolResult, TextContent

from veos_mcp.schemas.cli_command_result import CliCommandResult
from veos_mcp.schemas.errors import VeosError, ErrorType
from veos_mcp.veos_cli import VeosCli
    
mcp = FastMCP(
    name="VEOS MCP Server",
    instructions="Tools for controlling the dSPACE VEOS simulator.",
    json_response=True,
)

_veos_cli: VeosCli | None = None

def configure(veos_path: str) -> None:
    """Configure the server with the VEOS CLI installation directory."""
    global _veos_cli
    _veos_cli = VeosCli(veos_path)

def get_cli() -> VeosCli:
    """Return the configured VEOS CLI facade."""
    if _veos_cli is None:
        raise RuntimeError(
            "Missing required command line argument '--veos-path'. "
            "Configure it in the MCP server startup arguments."
        )
    return _veos_cli

def create_error(
    message: str,
    error_type: ErrorType = ErrorType.PERMANENT_ERROR,
) -> VeosError:
    """Create a typed MCP-facing error payload."""
    return VeosError(Type=error_type, Message=message)

def create_command_result_response(
    command_result: CliCommandResult,
    error: VeosError | None = None,
) -> CallToolResult:
    """Convert a VEOS CLI command result into an MCP tool result."""
    message = (
        error.model_dump_json(by_alias=True)
        if error is not None
        else "Tool Call succeeded."
        if command_result.success
        else "Tool Call failed."
    )
    return CallToolResult(
        isError=not command_result.success,
        content=[TextContent(type="text", text=message)],
        structuredContent=command_result.to_structured_content(),
    )
