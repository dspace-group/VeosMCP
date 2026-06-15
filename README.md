# dSPACE VEOS MCP server

Python MCP server for controlling the dSPACE VEOS simulator.

## Structure

- `src/veos_mcp/tools/`: VEOS MCP tool implementations
- `src/veos_mcp/resources/`: VEOS MCP resource implementations

## Prerequisites

- Python 3.12 or newer
- `uv`
- dSPACE VEOS installed on the machine

The Python package, MCP server name, and command are `veos-mcp`.

## Installation

Run the MCP server from this checkout with the newest installed VEOS version:

`uv run veos-mcp`

To select a specific installed VEOS version, pass `--veos-version`:

`uv run veos-mcp --veos-version 26.1`

Supported version formats include `26.1`, `26-A`, `26.2`, `26-B`, `2026-A`, and `2026-B`.

Use `--veos-path path\\to\\VEOS\\bin\\` only as an advanced override when you need to target a specific VEOS installation directly instead of resolving from a given VEOS version.

MCP server installation depends on the agent or client that should use the server. Configure Claude Code, CodeX, GitHub Copilot, or another MCP-capable client according to that client's MCP server setup instructions. The server should be registered as a stdio MCP server that runs `uv` in this checkout and starts the `veos-mcp` command. The example below shows one installation for GitHub Copilot.

### GitHub Copilot in VS Code

For GitHub Copilot in VS Code, create `.vscode/mcp.json` with a workspace-local MCP server entry. This does not require the developer setup unless you also want to run tests, linting, or builds.

```json
{
	"servers": {
		"VeosMCP": {
			"type": "stdio",
			"command": "uv",
			"args": [
				"--directory",
				"C:\\repos\\VeosMCP",
				"run",
				"veos-mcp",
				"--veos-version",
				"26-A"
				]
		}
	}
}
```

## Developer Setup

1. Create the project environment and install the development dependencies from the committed lockfile:

	`uv sync --python 3.12 --extra dev`

2. Run the server:

	`uv run veos-mcp`

	Use `--veos-version 26.1` when you need to pin the server to a specific installed VEOS version.

## Validation

- Run tests: `uv run pytest`
- Run pylint: `uv run pylint src tests`
- Build a wheel: `uv build`

## Dependency Licenses

Direct dependency license metadata checked from the current project environment:

| Dependency | Scope | License |
| --- | --- | --- |
| `mcp` | Runtime | MIT |
| `pydantic` | Runtime | MIT |
| `pythonnet` | Runtime | MIT |
| `pylint` | Development | GPL-2.0-or-later |
| `pytest` | Development | MIT |

## How to extend the server with a new tool

MCP tools live in `src/veos_mcp/tools/` and are registered with the shared FastMCP instance from `veos_mcp.runtime`.

1. Add the tool implementation to an existing module in `src/veos_mcp/tools/` or create a new module there.
2. Decorate the function with `@mcp.tool(...)`. You should add a clear title and description, and set `ToolAnnotations` to describe whether the tool is read-only, destructive, idempotent, or open-world.
3. Use `get_cli().run_sim(...)` or `get_cli().run_model(...)` for VEOS CLI operations. You can return responses through `create_command_result_response(...)` and use `create_error(...)` for failed VEOS commands.
4. If you created a new tool module, import it in `src/veos_mcp/tools/__init__.py`; otherwise the decorator will not run when the server starts.
5. Add or update tests under `tests/tools/` for the direct Python function behavior.
6. Add the new tool name to `expected_tools` in `tests/test_mcp_surface_smoketest.py` so the MCP stdio surface test verifies that it is registered.
7. Run `uv run pytest` and `uv run pylint src tests`.

Minimal tool shape:

```python
from veos_mcp.runtime import mcp

@mcp.tool(
    name="veos_new_tool",
    title="New Server Tool",
    description="Tool extending the VEOS MCP server."
)
def veos_new_tool() -> str:
    return "Executed the new VEOS tool."
```

## Example Prompts

- TODO
