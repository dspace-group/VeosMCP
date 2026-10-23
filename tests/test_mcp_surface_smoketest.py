"""Surface tests for the MCP server's exposed tools and resources."""

import asyncio
import os
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


def create_server_params() -> StdioServerParameters:
    return StdioServerParameters(
        command=sys.executable,
        args=["-m", "veos_mcp.server"],
        env={**os.environ, "VEOS_MCP_SKIP_CONFIGURE": "1"},
    )


def test_list_all_tools() -> None:
    """Test that all expected tools can be listed from the stdio server."""

    expected_tools = [
        "veos_add_signal_connections",
        "veos_apply_config",
        "veos_get_all_signals_and_ports",
        "veos_get_build_import_config_schema",
        "veos_get_full_simulation_system_data_model",
        "veos_get_log_file",
        "veos_get_system_modification_model_schema",
        "veos_list_all_available_log_files",
        "veos_load",
        "veos_remove_signal_connections",
        "veos_simulation_system_modify",
        "veos_start",
        "veos_status_info",
        "veos_stop",
        "veos_system_build",
    ]

    async def list_tool_names() -> list[str]:
        server_params = create_server_params()

        async with stdio_client(server_params) as (read, write), ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            return sorted(tool.name for tool in tools.tools)

    actual_tools = asyncio.run(list_tool_names())

    assert actual_tools == expected_tools


def test_list_all_resource_templates() -> None:
    """Test that all expected resource templates can be listed from the stdio server."""

    expected_resource_templates = [
        "veos://logs/bus/{log_file_name}",
        "veos://logs/sim/{log_file_name}",
    ]

    async def list_resource_templates() -> list[str]:
        server_params = create_server_params()

        async with stdio_client(server_params) as (read, write), ClientSession(read, write) as session:
            await session.initialize()
            templates = await session.list_resource_templates()
            return sorted(template.uri_template for template in templates.resource_templates)

    actual_resource_templates = asyncio.run(list_resource_templates())

    assert actual_resource_templates == expected_resource_templates


def test_smoketest_log_file_tool_over_mcp() -> None:
    """Test one end-to-end MCP tool call over stdio."""

    async def call_tool() -> tuple[bool, dict[str, object]]:
        server_params = create_server_params()

        async with stdio_client(server_params) as (read, write), ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool("veos_get_log_file", {"log_file_name": "veos.log"})
            assert result.structured_content is not None
            return result.is_error, result.structured_content

    is_error, structured_content = asyncio.run(call_tool())

    assert is_error is False
    assert structured_content["Code"] == "ok"
    assert structured_content["Uri"] == "veos://logs/sim/veos.log"
