"""MCP tools for enumerating VEOS log files and returning resource links."""

from mcp.types import CallToolResult, ResourceLink, ToolAnnotations
from pydantic import AnyUrl

from veos_mcp.models.cli_command_result import CommandResultCode
from veos_mcp.runtime import (
    create_command_result_response_error,
    create_command_result_response_success,
    get_cli,
    mcp,
)


@mcp.tool(
    name="veos_list_all_available_log_files",
    title="List all available VEOS log files",
    description=(
        "Lists all available VEOS log files, including both bus log files (pcapng) and simulation log files. "
        "Structured content includes a CommandResultCode value for the execution of the underlying VEOS process: ok, "
        "process_failed, process_start_failed, or process_timed_out. It also includes its exit code, Stdout, and Stderr."
    ),
    annotations=ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
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
    title="Get VEOS log file resource link",
    description=(
        "Gets the resource link to a specified VEOS log file, which can be either a bus log file (pcapng) or a "
        "simulation log file. Call veos_list_all_available_log_files to get the list of available log files first. "
        "This tool does not fail, hence it will not provide an error message."
    ),
    annotations=ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
def veos_get_log_file(log_file_name: str) -> CallToolResult:
    """Return an MCP resource link for a named VEOS log file."""
    is_pcapng_file = log_file_name.lower().endswith(".pcapng")
    resource_uri = f"veos://logs/bus/{log_file_name}" if is_pcapng_file else f"veos://logs/sim/{log_file_name}"
    mime_type = "application/vnd.tcpdump.pcap" if is_pcapng_file else "text/plain"
    description = "VEOS bus log file in pcapng format." if is_pcapng_file else "VEOS simulation log file in plain text format."
    return CallToolResult(
        isError=False,
        content=[
            ResourceLink(
                type="resource_link",
                uri=AnyUrl(resource_uri),
                name=log_file_name,
                title=log_file_name,
                description=description,
                mimeType=mime_type,
            )
        ],
        structuredContent={
            "Success": True,
            "Code": CommandResultCode.OK.value,
            "LogFileName": log_file_name,
            "Uri": resource_uri,
            "MimeType": mime_type,
            "Description": description,
        },
    )
