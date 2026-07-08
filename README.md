# dSPACE VEOS MCP server

MCP server implementation for controlling the [dSPACE VEOS](https://www.dspace.com/en/pub/home/products/sw/simulation_software/veos.cfm) simulator. This server enables LLMs to interact with the VEOS simulator and its log files.

## Prerequisites

- Installed [dSPACE VEOS](https://www.dspace.com/en/pub/home/products/sw/simulation_software/veos.cfm) on the machine where the MCP server runs.

For a developer-focused setup:
- Python 3.12 or newer.
- `uv`, the Python package and project manager used to create the environment, install dependencies, and run the server from this checkout. Install `uv` from the official Astral documentation: https://docs.astral.sh/uv/getting-started/installation/

## Getting Started

You can install the VEOS MCP server either directly from the latest GitHub Release or run it from this repository with a `uv`-based setup. You can easily verify the installation with a quick prompt, for example: "Give me the state of the VEOS simulator".

To install the latest release:

1. Download `veos-mcp-windows.zip` from the latest GitHub Release. The archive contains the server executable `veos-mcp.exe`.
2. Follow the MCP server installation instructions for your MCP client, for example Claude[↗️](https://code.claude.com/docs/en/mcp-quickstart), Codex[↗️](https://developers.openai.com/codex/mcp), GitHub Copilot[↗️](https://docs.github.com/en/copilot/how-tos/provide-context/use-mcp-in-your-ide/extend-copilot-chat-with-mcp), etc.. This is an exemplary installation for GitHub Copilot as a `.vscode/mcp.json` entry that points to the extracted executable:

   ```json
   {
     "servers": {
       "VeosMCP": {
         "type": "stdio",
         "command": "<PATH_TO_EXTRACTED_RELEASE>\\veos-mcp.exe",
         "args": [
           "--veos-version",
           "<VEOS_VERSION>"
         ]
       }
     }
   }
   ```

Alternatively, for a developer-focused `uv`-based setup:

1. Clone this repository.
2. Create the project environment and install dependencies from `pyproject.toml`:

   ```shell
   uv sync   # minimal
   uv sync --extra dev   # full developer setup
   ```

3. Follow the MCP server installation instructions for your respective MCP client to run the server using `uv run`, see [VeosMCP.cmd](VeosMCP.cmd). You can directly call this script from your MCP client, example `.vscode/mcp.json` entry:

   ```json
   {
     "servers": {
       "VeosMCP": {
         "type": "stdio",
         "command": "<PATH_TO_REPOSITORY>\\VeosMCP.cmd",
         "args": [
           "--veos-version",
           "<VEOS_VERSION>"
         ]
       }
     }
   }
   ```

4. Useful development commands:

    ```shell
    uv run pytest	# run tests
    uv run ruff format src tests	# run formatter
    uv run ruff check src tests		# run linter
    uv build	# build a wheel
    ```

## Configuration

The VEOS MCP server supports the following arguments. They can be provided in the JSON configuration above as part of the `args` list:

| Option | Description |
|--------|-------------|
| --veos-version <VEOS_VERSION> | supported version formats include `26.1`, `26-A`, `26.2`, `26-B`, `2026-A`, and `2026-B`. |
| --veos-bin-path <PATH> | target a specific VEOS installation with the path to its bin directory. |

If no `veos-version` and `veos-bin-path` are provided, the VEOS MCP server will use the newest installed VEOS installation on the machine.

## Tools
- **Simulator Control**
  - `veos_status_info`
  - `veos_apply_config`
  - `veos_load`
  - `veos_start`
  - `veos_stop`

- **Log File Access**
  - `veos_list_all_available_log_files`
  - `veos_get_log_file`

- **System Extraction**
  - `veos_get_all_signals_and_ports`

- **System Modification**
  - `veos_add_signal_connections`
  - `veos_remove_signal_connections`

## Resource Templates
- **Log Files**
  - `veos://logs/sim/{log_file_name}`
  - `veos://logs/bus/{log_file_name}`

## Example Prompts

- Load `my.osa` and run the simulation for 5 seconds.
- What signals are unconnected in `my.osa`? Do a best effort matching and connect them.
- Disconnect all the signals from the fmu EngineModel in `my.osa`.
- Enable the bus log and start the simulation, then check the bus logs for any TCP transmissions.

## Adding MCP Tools

MCP tools live in `src/veos_mcp/tools/` and are registered with the shared FastMCP instance from `veos_mcp.runtime`.

1. Add the tool implementation to an existing module in `src/veos_mcp/tools/` or create a new module there.
2. Decorate the function with `@mcp.tool(...)`. You should add a clear title and description, and set `ToolAnnotations` to describe whether the tool is read-only, destructive, idempotent, or open-world.
3. Use `get_cli().run_sim(...)` or `get_cli().run_model(...)` for VEOS CLI operations.
4. If you created a new tool module, re-export it in `src/veos_mcp/tools/__init__.py` with `from veos_mcp.tools import new_module as new_module` and add it to `__all__`; otherwise the decorator will not run when the server starts.
5. Add or update tests under `tests/tools/` for the direct Python function behavior.
6. Add the new tool name to `expected_tools` in `tests/test_mcp_surface_smoketest.py` so the MCP stdio surface test verifies that it is registered.
7. Run `pytest` and `ruff` for validation, formatting and linting.

Minimal tool shape:

```python
from veos_mcp.runtime import mcp

@mcp.tool(
    name="veos_new_tool",
    title="New tool",
    description="New tool extending the VEOS MCP server."
)
def veos_new_tool() -> str:
    return "Hello from the new VEOS MCP server tool!"
```
