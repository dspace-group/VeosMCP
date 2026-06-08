"""MCP resources that expose VEOS simulation and bus log file contents."""


from veos_mcp.runtime import get_cli, mcp


def _read_log_file(logFileName: str) -> str | bytes:
    """Read a VEOS log file and return raw text or bytes for FastMCP."""
    command_result = get_cli().run_sim("show-log", logFileName)

    if not command_result.success:
        return f"Error retrieving log file: {command_result.stderr}"

    return bytes(command_result.stdout_bytes) if logFileName.lower().endswith(".pcapng") else command_result.stdout


@mcp.resource(
    "logs://sim/{logFileName}",
    name="veos_get_sim_log_file_resource",
    title="VEOS Log File",
    mime_type="text/plain",
    description="Resource for accessing the contents of a VEOS Simulation.log file.",
)
def veos_get_sim_log_file_resource(logFileName: str) -> str:
    log_contents = _read_log_file(logFileName)
    return log_contents if isinstance(log_contents, str) else bytes(log_contents).decode("utf-8", errors="replace")


@mcp.resource(
    "logs://bus/{logFileName}",
    name="veos_get_bus_log_file_resource",
    title="VEOS Bus Log File",
    mime_type="application/vnd.tcpdump.pcap",
    description="Resource for accessing the contents of a VEOS Bus log file.",
)
def veos_get_bus_log_file_resource(logFileName: str) -> bytes:
    log_contents = _read_log_file(logFileName)
    return log_contents.encode("utf-8") if isinstance(log_contents, str) else bytes(log_contents)