"""MCP tools for VEOS simulator state, loading, and configuration."""

from mcp.types import CallToolResult, ToolAnnotations

from veos_mcp.runtime import (
    create_command_result_response_success,
    create_command_result_response_error,
    get_cli,
    mcp,
)


@mcp.tool(
    name="veos_status_info",
    title="Get VEOS Simulator Status Info",
    description=(
        "Gets the current status information of the VEOS simulator, including "
        "the simulator state. State can be one of: Unloaded, Stopped, Running, "
        "Paused, Stopped, Terminated. This also resembles the typical VEOS "
        "workflow. VEOS starts in Unloaded state. From there, you can load a "
        "model (.osa file), which transitions it to state Stopped. From "
        "Stopped, you can start the simulation, which transitions it to "
        "Running. If no pause or stop time is configured or no explicit pause "
        "or stop command is issued, the simulation will continue running "
        "forever. The Terminated state is only reached when the simulator runs "
        "into an unrecoverable error. Structured content includes a "
        "CommandResultCode value for the execution of the underlying VEOS "
        "process: ok, process_failed, process_start_failed, or "
        "process_timed_out. It also includes its exit code, Stdout, and "
        "Stderr."
    ),
    annotations=ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
def veos_status_info() -> CallToolResult:
    """Get the current VEOS simulator status information."""
    command_result = get_cli().run_sim("info")
    if not command_result.success:
        return create_command_result_response_error(
            command_result,
            "Failed to get VEOS status info.",
        )
    return create_command_result_response_success(command_result)


@mcp.tool(
    name="veos_load",
    title="Load .osa simulation model into VEOS",
    description=(
        "Loads a simulation model specified by an osa file into the VEOS "
        "simulator. If successful, this transitions the simulator to the "
        "Stopped state. If load fails, the simulator switches to the "
        "Terminated state. The tool takes the path to the osa file as input "
        "and returns the result of the load operation. If the load fails "
        "(e.g. due to invalid osa path or file), the tool returns an error "
        "message with details about the failure. Structured content includes "
        "a CommandResultCode value for the execution of the underlying VEOS "
        "process: ok, process_failed, process_start_failed, or "
        "process_timed_out. It also includes its exit code, Stdout, and "
        "Stderr."
    ),
    annotations=ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
def veos_load(osaPath: str) -> CallToolResult:
    """Load an OSA model into the VEOS simulator."""
    command_result = get_cli().run_sim("load", osaPath)
    if not command_result.success:
        return create_command_result_response_error(
            command_result,
            "Failed to load osa file onto the VEOS.",
        )
    return create_command_result_response_success(command_result)


@mcp.tool(
    name="veos_start",
    title="Start VEOS simulation",
    description=(
        "Starts the VEOS simulation. This transitions the simulator from "
        "Stopped or Paused state to Running state. An osa file must have "
        "been successfully loaded beforehand by calling the VeosLoad tool. "
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
def veos_start() -> CallToolResult:
    """Start the loaded VEOS simulation."""
    command_result = get_cli().run_sim("start")
    if not command_result.success:
        return create_command_result_response_error(
            command_result,
            "Failed to start the VEOS simulation.",
        )
    return create_command_result_response_success(command_result)


@mcp.tool(
    name="veos_stop",
    title="Stop VEOS simulation",
    description=(
        "Stops the VEOS simulation. This transitions the simulator from "
        "Running or Paused state to Stopped state. If the simulator is not "
        "in a valid state for stopping the simulation, this tool returns an "
        "error message with details about the failure. Necessary operation to "
        "access the simulation log and bus log files, as these are only "
        "finalized and accessible after the simulation is stopped. Structured "
        "content includes a CommandResultCode value for the execution of the "
        "underlying VEOS process: ok, process_failed, process_start_failed, "
        "or process_timed_out. It also includes its exit code, Stdout, and "
        "Stderr."
    ),
    annotations=ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
def veos_stop() -> CallToolResult:
    """Stop the running VEOS simulation."""
    command_result = get_cli().run_sim("stop")
    if not command_result.success:
        return create_command_result_response_error(
            command_result,
            "Failed to stop the VEOS simulation.",
        )
    return create_command_result_response_success(command_result)


@mcp.tool(
    name="veos_apply_config",
    title="Configure the VEOS simulator",
    description=(
        "Sets up and configures the VEOS simulation without starting it. The "
        "tool takes configuration parameters such as stop time, acceleration "
        "factor, and logging options as input, and returns the result of the "
        "operation. Changes in busLog and simLog only take effect if the "
        "VeosLoad tool is executed after this tool call. Only two values of "
        "Acceleration factor are meaningful in most contexts: Infinity (also "
        "equals 0 in integer representation) means as fast as possible, '1' "
        "means real-time speed. stopTime is a string representing the desired "
        "stop time for the simulation given in seconds of SimulationTime. "
        "busLog and simLog are boolean flags indicating whether to enable bus "
        "logging and simulation logging, respectively. ipAddress is a string "
        "representing the IP address of the VEOS simulator, defaulting to "
        "localhost 127.0.0.1 if not specified. Any parameter omitted from the "
        "tool call is left unchanged in the VEOS configuration. If "
        "successful, this tool returns the newly applied configuration, "
        "equivalent to calling the tool VeosStatusInfo. If the tool fails "
        "(e.g. due to invalid configuration parameters), the tool returns an "
        "error message with details about the failure. Structured content "
        "includes a CommandResultCode value for the execution of the "
        "underlying VEOS process: ok, process_failed, process_start_failed, "
        "or process_timed_out. It also includes its exit code, Stdout, and "
        "Stderr."
    ),
    annotations=ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
def veos_apply_config(
    stopTime: str | None = None,
    accelerationFactor: str | None = None,
    ipAddress: str | None = None,
    busLog: bool | None = None,
    simLog: bool | None = None,
) -> CallToolResult:
    """Apply VEOS simulator configuration without starting the simulation."""
    arguments = ["config"]
    if stopTime:
        arguments.extend(["-o", stopTime])
    if ipAddress:
        arguments.extend(["-h", ipAddress])
    if accelerationFactor:
        arguments.extend(["-a", accelerationFactor])
    if busLog is not None:
        arguments.append("--enable-bus-log" if busLog else "--disable-bus-log")
    if simLog is not None:
        arguments.append("--enable-sim-log" if simLog else "--disable-sim-log")

    command_result = get_cli().run_sim(*arguments)
    if not command_result.success:
        return create_command_result_response_error(
            command_result,
            "Failed to apply the VEOS simulation configuration.",
        )
    return create_command_result_response_success(command_result)
