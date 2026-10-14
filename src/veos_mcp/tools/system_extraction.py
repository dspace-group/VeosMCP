"""MCP tools and helpers for VEOS model signal inspection."""

import json
import os
import tempfile
from pathlib import Path

from mcp.types import CallToolResult, TextContent, ToolAnnotations

from veos_mcp.parsers import model_parser as model_inspection_service
from veos_mcp.runtime import (
    create_command_result_response_error,
    create_error_response,
    get_cli,
    mcp,
)


def _write_json_to_server_temp_file(osa_path: str, data: object) -> Path:
    """Write JSON to a new unique file in the server's temp directory and return its path."""
    temp_directory = Path(tempfile.gettempdir()) / "veos_mcp"
    temp_directory.mkdir(parents=True, exist_ok=True)
    file_descriptor, temp_name = tempfile.mkstemp(
        dir=temp_directory,
        prefix=f"{Path(osa_path).stem or 'model'}_data_model_",
        suffix=".json",
    )
    temp_path = Path(temp_name)
    try:
        with os.fdopen(file_descriptor, "w", encoding="utf-8") as temp_file:
            json.dump(data, temp_file, indent=2, ensure_ascii=False)
    except BaseException:
        temp_path.unlink(missing_ok=True)
        raise
    return temp_path.resolve()


@mcp.tool(
    name="veos_get_full_simulation_system_data_model",
    title="Export the full VEOS simulation system data model to a JSON file",
    description=(
        "Exports the complete data model of the given VEOS osa simulation system (VPUs, ports, signals, "
        "communication packages, connections, etc.) as a pretty-printed JSON file. The data model can be very large, "
        "so it is written to a new unique file in the VEOS MCP server's temp directory instead of being returned. "
        "Read or search the file in parts afterwards. On success, structured content contains the JsonFilePath of the "
        "written file, its SizeBytes, and TopLevelEntries (element counts of the top-level properties) as an overview. "
        "If the tool call fails, it returns an error message with details about the failure, and if the underlying "
        "VEOS process failed, its Stdout and Stderr in structured content."
    ),
    annotations=ToolAnnotations(
        read_only_hint=False,
        destructive_hint=False,
        idempotent_hint=True,
        open_world_hint=False,
    ),
)
def veos_get_full_simulation_system_data_model(osa_path: str) -> CallToolResult:
    """Write the full VEOS model data of an OSA file as JSON to a server temp file and return its path."""
    command_result = get_cli().run_model("get", osa_path)
    if not command_result.success:
        return create_command_result_response_error(command_result, "Failed to get the data model from the VEOS model.")

    try:
        data_model = json.loads(s=command_result.stdout)
    except json.JSONDecodeError as exception:
        return create_error_response(f"Failed to parse the data model from the VEOS model output as JSON: {exception}")

    try:
        json_file_path = _write_json_to_server_temp_file(osa_path, data_model)
    except OSError as exception:
        return create_error_response(f"Failed to write the data model to the server temp directory: {exception}")

    size_bytes = json_file_path.stat().st_size

    top_level_entries = (
        {key: len(value) if isinstance(value, list | dict) else 1 for key, value in data_model.items()}
        if isinstance(data_model, dict)
        else {}
    )
    return CallToolResult(
        is_error=False,
        content=[TextContent(type="text", text=f"Wrote the VEOS data model ({size_bytes} bytes) to '{json_file_path}'.")],
        structured_content={
            "Success": True,
            "JsonFilePath": str(json_file_path),
            "SizeBytes": size_bytes,
            "TopLevelEntries": top_level_entries,
        },
    )


@mcp.tool(
    name="veos_get_all_signals_and_ports",
    title="Get a list of signals/ports from the VEOS osa simulation system",
    description=(
        "Gets the list of available signals/ports from the given osa file and existing connections "
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
        read_only_hint=True,
        destructive_hint=False,
        idempotent_hint=True,
        open_world_hint=False,
    ),
)
def veos_get_all_signals_and_ports(osa_path: str) -> CallToolResult:
    """Return the available signals, ports, and connections for an OSA model."""
    command_result = get_cli().run_model("get", osa_path)
    if not command_result.success:
        return create_command_result_response_error(command_result, "Failed to get the list of signals from the VEOS model.")

    try:
        signal_summary = model_inspection_service.extract_signal_summary(command_result.stdout)
    except (KeyError, TypeError, ValueError) as exception:
        return create_error_response(f"Failed to parse the signal summary from the VEOS model output: {exception}")

    return CallToolResult(
        is_error=False,
        content=[],
        structured_content=signal_summary.model_dump(by_alias=True, mode="json"),
    )
