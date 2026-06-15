"""MCP tools for editing VEOS model signal connections."""

from mcp.types import CallToolResult, ToolAnnotations

from veos_mcp.runtime import (
    create_command_result_response_success,
    create_command_result_response_error,
    get_cli,
    mcp,
)


@mcp.tool(
    name="veos_add_signal_connection",
    title="Connect signals given a JSON file",
    description=(
        "Adds signal connections that are specified in a list within the JSON "
        "file to the given VEOS osa file. Example JSON that adds two "
        "connections, the signal references are the signal paths:\n"
        "{\n"
        '    "CommunicationPackages": [\n'
        "        {\n"
        '            "PackageType": "StandardCommunicationPackage",\n'
        '            "SignalConnections": [\n'
        "                {\n"
        '                    "InSignalReference": "/Consumer/ProducerData/Sc1_ProducerData",\n'
        '                    "OutSignalReference": "/Producer/ProducerData/Sa1_ProducerData"\n'
        "                },\n"
        "                {\n"
        '                    "InSignalReference": "/Consumer/ProducerData/Sc2_ProducerData",\n'
        '                    "OutSignalReference": "/Producer/ProducerData/Sa2_ProducerData"\n'
        "                }\n"
        "            ]\n"
        "        }\n"
        "    ]\n"
        "}\n"
        "If successful, this tool returns a success message. If the tool "
        "fails (e.g. due to invalid JSON file or invalid signal references), "
        "the tool returns an error message with details about the failure. "
        "Structured content includes a CommandResultCode value for the "
        "execution of the underlying VEOS process: ok, process_failed, "
        "process_start_failed, or process_timed_out. It also includes its "
        "exit code, Stdout, and Stderr."
    ),
    annotations=ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
def veos_add_signal_connection(osaPath: str, jsonPath: str) -> CallToolResult:
    """Add signal connections from a JSON file to an OSA model."""
    command_result = get_cli().run_model("connect", osaPath, "-c", jsonPath)
    if not command_result.success:
        return create_command_result_response_error(
            command_result,
            f"Failed to add signal connection from JSON file {jsonPath} "
            "on the VEOS model.",
        )

    return create_command_result_response_success(command_result)


@mcp.tool(
    name="veos_remove_signal_connection",
    title="Disconnect signals given in a JSON file",
    description=(
        "Removes signal connections that are specified in a list within the "
        "JSON file from the given VEOS osa file. Example JSON that removes "
        "two connections, the signal references are the signal paths:\n"
        "{\n"
        '    "SignalConnections": [\n'
        "        {\n"
        '            "InSignalReference": "/Consumer/ProducerData/Sc1_ProducerData",\n'
        '            "OutSignalReference": "/Producer/ProducerData/Sa1_ProducerData"\n'
        "        },\n"
        "        {\n"
        '            "InSignalReference": "/Consumer/ProducerData/Sc2_ProducerData",\n'
        '            "OutSignalReference": "/Producer/ProducerData/Sa2_ProducerData"\n'
        "        }\n"
        "    ]\n"
        "}\n"
        "If successful, this tool returns a success message. If the tool "
        "fails (e.g. due to invalid JSON file or invalid signal references), "
        "the tool returns an error message with details about the failure. "
        "Structured content includes a CommandResultCode value for the "
        "execution of the underlying VEOS process: ok, process_failed, "
        "process_start_failed, or process_timed_out. It also includes its "
        "exit code, Stdout, and Stderr."
    ),
    annotations=ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
def veos_remove_signal_connection(osaPath: str, jsonPath: str) -> CallToolResult:
    """Remove signal connections from a JSON file from an OSA model."""
    command_result = get_cli().run_model("remove", osaPath, "-c", jsonPath)
    if not command_result.success:
        return create_command_result_response_error(
            command_result,
            f"Failed to remove signal connection from JSON file {jsonPath} "
            "on the VEOS model.",
        )

    return create_command_result_response_success(command_result)
