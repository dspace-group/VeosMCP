# VeosMCP

Python MCP server for controlling the dSPACE VEOS simulator.

## Structure

- `src/veos_mcp/server.py`: FastMCP startup, `--veos-path` handling, tool/resource registration
- `src/veos_mcp/veos_cli.py`: VEOS executable resolution, subprocess execution, timeout handling, locking
- `src/veos_mcp/tools/`: VEOS MCP tool implementations
- `src/veos_mcp/resources/`: VEOS MCP resource implementations
- `src/veos_mcp/schemas/`: MCP-facing pydantic models
- `tests/`: unit tests for command execution and signal summary extraction
- `test-assets/`: sample OSA model copied from the original repository

## Setup

1. Create a virtual environment with Python 3.12.
2. Install the project and development dependencies:

	`.venv\\Scripts\\python.exe -m pip install -e ".[dev]"`

3. Run the server by pointing it at the VEOS `bin` directory:

	`.venv\\Scripts\\veos-mcp.exe --veos-path C:\\Path\\To\\VEOS\\bin`

## Validation

- Run tests: `.venv\\Scripts\\python.exe -m pytest`
- Run pylint: `.venv\\Scripts\\python.exe -m pylint src tests`
