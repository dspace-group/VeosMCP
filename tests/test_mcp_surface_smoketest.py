"""Surface tests for the MCP server's exposed tools and resources."""

import asyncio
from pathlib import Path
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


def create_fake_veos_executable(tmp_path: Path) -> Path:
    """Create a minimal VEOS stub executable for subprocess-based MCP tests."""
    if sys.platform.startswith("win"):
        veos_path = tmp_path / "veos.cmd"
        veos_path.write_text("@echo off\r\nexit /b 0\r\n", encoding="utf-8")
        return veos_path

    veos_path = tmp_path / "veos"
    veos_path.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    veos_path.chmod(0o755)
    return veos_path


def create_server_params(veos_path: Path) -> StdioServerParameters:
    return StdioServerParameters(
        command=sys.executable,
        args=["-m", "veos_mcp.server", "--veos-path", str(veos_path)],
    )


def test_list_all_tools(tmp_path: Path) -> None:
    """Test that all expected tools can be listed from the stdio server."""

    expected_tools = [
        "veos_add_signal_connection",
        "veos_apply_config",
        "veos_get_all_signals_and_ports",
        "veos_get_log_file",
        "veos_list_all_available_log_files",
        "veos_load",
        "veos_remove_signal_connection",
        "veos_start",
        "veos_status_info",
        "veos_stop",
    ]

    async def list_tool_names() -> list[str]:
        server_params = create_server_params(create_fake_veos_executable(tmp_path))
        
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = await session.list_tools()
                return sorted(tool.name for tool in tools.tools)

    actual_tools = asyncio.run(list_tool_names())

    assert actual_tools == expected_tools


def test_list_all_resource_templates(tmp_path: Path) -> None:
    """Test that all expected resource templates can be listed from the stdio server."""

    expected_resource_templates = [
        "logs://bus/{logFileName}",
        "logs://sim/{logFileName}",
    ]

    async def list_resource_templates() -> list[str]:
        server_params = create_server_params(create_fake_veos_executable(tmp_path))

        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                templates = await session.list_resource_templates()
                return sorted(template.uriTemplate for template in templates.resourceTemplates)

    actual_resource_templates = asyncio.run(list_resource_templates())

    assert actual_resource_templates == expected_resource_templates


def test_smoketest_log_file_tool_over_mcp(tmp_path: Path) -> None:
    """Test one end-to-end MCP tool call over stdio."""

    async def call_tool() -> tuple[bool, str]:
        server_params = create_server_params(create_fake_veos_executable(tmp_path))

        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool("veos_status_info", {})
                assert result.structuredContent is not None
                return result.isError, result.structuredContent["Code"]

    is_error, result_code = asyncio.run(call_tool())

    assert is_error is False
    assert result_code == "ok"