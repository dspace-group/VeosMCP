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
        "veos_get_simulation_targets",
        "veos_get_veos_data_model_and_modify_schema",
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

    expected_resource_templates = []

    async def list_resource_templates() -> list[str]:
        server_params = create_server_params()

        async with stdio_client(server_params) as (read, write), ClientSession(read, write) as session:
            await session.initialize()
            templates = await session.list_resource_templates()
            return sorted(template.uri_template for template in templates.resource_templates)

    actual_resource_templates = asyncio.run(list_resource_templates())

    assert actual_resource_templates == expected_resource_templates
