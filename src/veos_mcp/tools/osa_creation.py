"""MCP tool for creating VEOS simulation systems with the Model Console."""

from mcp.types import CallToolResult, ToolAnnotations

from veos_mcp.runtime import (
    create_command_result_response_error,
    create_command_result_response_success,
    get_cli,
    mcp,
)


@mcp.tool(
    name="veos_create_osa",
    title="Create a new VEOS OSA file",
    description=(
        "Creates and saves a new, empty VEOS offline simulation application (OSA) at the specified path using the "
        "headless VEOS Model Console. The parent directory must already exist."
    ),
    annotations=ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=False,
    ),
)
def veos_create_osa(osa_path: str) -> CallToolResult:
    """Create a new OSA simulation system."""
    command_result = get_cli().run_model(
        "modify",
        osa_path,
        "--modifications",
        "[]",
        "--create-new",
        "--save-only-on-success",
        "--verbosity",
        "Error",
    )
    if not command_result.success:
        return create_command_result_response_error(command_result, f"Failed to create VEOS OSA file {osa_path}.")

    return create_command_result_response_success(command_result)
