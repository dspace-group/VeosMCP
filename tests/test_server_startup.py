"""Startup tests for the MCP server."""

import asyncio
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import pytest

from veos_mcp import server

def collect_exception_messages(exception: BaseException) -> list[str]:
    """Flatten nested exception groups into a list of messages."""
    messages = [str(exception)]
    if isinstance(exception, BaseExceptionGroup):
        for nested_exception in exception.exceptions:
            messages.extend(collect_exception_messages(nested_exception))
    return messages


def test_argument_veos_path_missing(capsys: pytest.CaptureFixture[str]) -> None:
    """Test the direct server entrypoint error when the --veos-path argument is missing."""
    with pytest.raises(SystemExit) as exc_info:
        server.main([])

    captured = capsys.readouterr()

    assert exc_info.value.code == 2
    assert "--veos-path" in captured.err
    assert "required" in captured.err


def test_argument_veos_path_invalid() -> None:
    """Test the direct server entrypoint error when the --veos-path argument is invalid."""
    with pytest.raises(FileNotFoundError) as exc_info:
        server.main(["--veos-path", "invalid_path"])

    assert "--veos-path" in str(exc_info.value)
    assert "invalid_path" in str(exc_info.value)


def test_argument_veos_path_missing_via_mcp() -> None:
    """Test that the server fails to start if the --veos-path argument is missing."""
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "veos_mcp.server"]
    )

    async def start_server() -> None:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

    with pytest.raises(BaseExceptionGroup) as exc_info:
        asyncio.run(start_server())

    messages = collect_exception_messages(exc_info.value)
    assert any("Connection closed" in message for message in messages), (
        "Expected server startup without --veos-path to fail by closing the MCP connection."
    )