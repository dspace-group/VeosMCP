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

## User Setup

Run the MCP server from this checkout with the newest installed VEOS version:

`uv run veos-mcp`

To select a specific installed VEOS version, pass `--veos-version`:

`uv run veos-mcp --veos-version 26.1`

Supported version formats include `26.1`, `26.2`, `2026-A`, and `2026-B`.

Use `--veos-path C:\\Path\\To\\VEOS\\bin\\veos.exe` only as an advanced override when you need to target a specific VEOS executable directly instead of resolving an installed VEOS version.

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



## VS Code MCP Configuration

To register the server in a workspace-local VS Code MCP configuration, create `.vscode/mcp.json` with a stdio server entry that runs the `veos-mcp` command through `uv`. This does not require the developer setup unless you also want to run tests, linting, or builds.

```json
{
	"servers": {
		"veos-mcp": {
			"type": "stdio",
			"command": "uv",
			"args": [
				"run",
				"veos-mcp"
			],
			"cwd": "${workspaceFolder}"
		}
	}
}
```

This configuration uses the newest installed VEOS version. To pin a specific installed VEOS version, use this configuration instead:

```json
{
	"servers": {
		"veos-mcp": {
			"type": "stdio",
			"command": "uv",
			"args": [
				"run",
				"veos-mcp",
				"--veos-version",
				"26.1"
			],
			"cwd": "${workspaceFolder}"
		}
	}
}
```

Use `--veos-path` only as an advanced override when you need to point to a specific VEOS executable such as `C:\\Path\\To\\VEOS\\bin\\veos.exe` instead of resolving an installed version.

## Example Prompts

- Prompt: `Get the current VEOS simulator status.`
	Result: VS Code can call `veos_status_info` and return structured status data such as the simulator state and command result code, for example `Code: ok`.

- Prompt: `List the VEOS log files that are currently available.`
	Result: VS Code can call `veos_list_all_available_log_files` and return the available simulation and bus log file names.

- Prompt: `Open the Simulation.log resource from VEOS.`
	Result: VS Code can call `veos_get_log_file` for `Simulation.log`, receive the resource URI `logs://sim/Simulation.log`, and then read the plain-text log resource.

- Prompt: `Inspect all signals and ports in C:\\Models\\Demo.osa.`
	Result: VS Code can call `veos_get_all_signals_and_ports` and return structured signal, port, and connection data extracted from the OSA model.
