"""Shared helpers for VEOS MCP tool tests."""

import json
from typing import cast

from mcp.types import CallToolResult, TextContent

from veos_mcp.models.cli_command_result import CliCommandResult


class RecordingModelCliMock:
    def __init__(self, result: CliCommandResult) -> None:
        self._result = result
        self.model_calls: list[tuple[str, ...]] = []

    def run_model(self, *arguments: str) -> CliCommandResult:
        self.model_calls.append(arguments)
        return self._result


class RecordingSimCliMock:
    def __init__(self, sim_result: CliCommandResult) -> None:
        self._sim_result = sim_result
        self.sim_calls: list[tuple[str, ...]] = []

    def run_sim(self, *arguments: str) -> CliCommandResult:
        self.sim_calls.append(arguments)
        return self._sim_result


def assert_command_result_structured_content(
    tool_name: str,
    structured_content: dict[str, object],
) -> None:
    assert "Success" in structured_content, f"{tool_name} should include Success in structured content."
    assert "Code" in structured_content, f"{tool_name} should include Code in structured content."
    assert "Stdout" in structured_content, f"{tool_name} should include Stdout in structured content."
    assert "Stderr" in structured_content, f"{tool_name} should include Stderr in structured content."
    assert "ExitCode" in structured_content, f"{tool_name} should include ExitCode in structured content."


def assert_error_text_content(result: CallToolResult, expected_message: str) -> None:
    assert result.content is not None, "Expected text content in the tool result."
    text_content = cast(TextContent, result.content[0])
    payload = json.loads(text_content.text)
    assert payload["Type"] == "PermanentError"
    assert payload["Message"] == expected_message
