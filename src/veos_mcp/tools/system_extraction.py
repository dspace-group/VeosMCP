"""MCP tools and helpers for VEOS model signal inspection."""

from mcp.types import CallToolResult, ToolAnnotations

from veos_mcp.parsers import model_parser as model_inspection_service
from veos_mcp.runtime import (
    create_command_result_response_error,
    create_error_response,
    get_cli,
    mcp,
)


@mcp.tool(
    name="veos_get_all_signals_and_ports",
    title="Get a list of signals/ports from the VEOS osa simulation system",
    description=(
        "Gets the list of available signals/ports from the currently loaded VEOS model and existing connections "
        "between them. Signals and ports are often used interchangeably in the context of the VEOS simulation system. "
        "Signals are either output or input ports, and each port has a specific data type. An output port/signal "
        "represents a signal that is produced by a component in the simulation and can be connected to multiple input "
        "ports/signals of other components. Signal paths are structured hierarchically. Interpret the first path "
        "element as the VPU/model/ECU and the last path element as the signal name. When the tool call is successful, "
        "it returns the list of signals/ports and their connections in a structured format. If the tool call fails "
        "(e.g. due to invalid osa file), it returns an error message with details about the failure and the Stdout "
        "and Stderr of the underlying VEOS process in structured content."
    ),
    annotations=ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
def veos_get_all_signals_and_ports(osa_path: str) -> CallToolResult:
    """Return the available signals, ports, and connections for an OSA model."""
    command_result = get_cli().run_model("get", osa_path)
    if not command_result.success:
        return create_command_result_response_error(
            command_result,
            "Failed to get the list of signals from the VEOS model.",
        )

    try:
        signal_summary = model_inspection_service.extract_signal_summary(command_result.stdout)
    except (KeyError, TypeError, ValueError) as exception:
        return create_error_response(f"Failed to parse the signal summary from the VEOS model output: {exception}")

    return CallToolResult(
        isError=False,
        content=[],
        structuredContent=signal_summary.model_dump(by_alias=True, mode="json"),
    )
