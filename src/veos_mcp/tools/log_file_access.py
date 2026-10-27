"""MCP tools for enumerating and downloading VEOS log files."""

import os
import tempfile
from pathlib import Path

from mcp.types import CallToolResult, TextContent, ToolAnnotations

from veos_mcp.models.cli_command_result import CommandResultCode
from veos_mcp.runtime import (
    create_command_result_response_error,
    create_command_result_response_success,
    create_error_response,
    get_cli,
    mcp,
)


def _write_log_file_to_server_temp_file(log_file_name: str, contents: bytes) -> Path:
    """Write log contents to a unique file in the server's temp directory."""
    temp_directory = Path(tempfile.gettempdir()) / "veos_mcp"
    temp_directory.mkdir(parents=True, exist_ok=True)
    file_name = Path(log_file_name).name
    file_descriptor, temp_name = tempfile.mkstemp(
        dir=temp_directory,
        prefix=f"{Path(file_name).stem or 'veos'}_log_",
        suffix=Path(file_name).suffix,
    )
    temp_path = Path(temp_name)
    try:
        with os.fdopen(file_descriptor, "wb") as temp_file:
            temp_file.write(contents)
    except BaseException:
        temp_path.unlink(missing_ok=True)
        raise
    return temp_path.resolve()


@mcp.tool(
    name="veos_list_all_available_log_files",
    title="List all available VEOS log files",
    description=(
        "Lists all available VEOS log files, including both bus log files (pcapng) and simulation log files. "
        "Structured content includes a CommandResultCode value for the execution of the underlying VEOS process: ok, "
        "process_failed, process_start_failed, or process_timed_out. It also includes its exit code, Stdout, and Stderr."
    ),
    annotations=ToolAnnotations(
        read_only_hint=True,
        destructive_hint=False,
        idempotent_hint=True,
        open_world_hint=False,
    ),
)
def veos_list_all_available_log_files() -> CallToolResult:
    """List the VEOS bus and simulation log files that are currently available."""
    command_result = get_cli().run_sim("show-log")
    if not command_result.success:
        return create_command_result_response_error(command_result, "Failed to retrieve the list of available log files.")
    return create_command_result_response_success(command_result)


@mcp.tool(
    name="veos_get_log_file",
    title="Gets the path to a VEOS log file",
    description=(
        "Downloads a specified VEOS log file, which can be either a bus log file (pcapng) or a simulation log file, "
        "to a unique file in the VEOS MCP server's temp directory. Call veos_list_all_available_log_files to get the "
        "list of available log files first. On success, structured content contains the LogFilePath and SizeBytes."
    ),
    annotations=ToolAnnotations(
        read_only_hint=True,
        destructive_hint=False,
        idempotent_hint=True,
        open_world_hint=False,
    ),
)
def veos_get_log_file(log_file_name: str) -> CallToolResult:
    """Download a named VEOS log file to the server's temp directory."""
    command_result = get_cli().run_sim("show-log", log_file_name)
    if not command_result.success:
        return create_command_result_response_error(command_result, "Failed to retrieve the requested VEOS log file.")

    try:
        log_file_path = _write_log_file_to_server_temp_file(log_file_name, command_result.stdout_bytes)
    except OSError as exception:
        return create_error_response(f"Failed to write the VEOS log file to the server temp directory: {exception}")

    size_bytes = log_file_path.stat().st_size
    return CallToolResult(
        is_error=False,
        content=[TextContent(type="text", text=f"Wrote the VEOS log file ({size_bytes} bytes) to '{log_file_path}'.")],
        structured_content={
            "Success": True,
            "Code": CommandResultCode.OK.value,
            "LogFileName": log_file_name,
            "LogFilePath": str(log_file_path),
            "SizeBytes": size_bytes,
        },
    )
