"""MCP tool for importing files with the VEOS Model and Build Consoles."""

from pathlib import Path
from typing import Literal

from mcp.types import CallToolResult, ToolAnnotations

from veos_mcp.runtime import (
    create_command_result_response_error,
    create_command_result_response_success,
    create_error_response,
    get_cli,
    mcp,
)

ImportFileType = Literal[
    "osa",
    "json",
    "fmu",
    "sic",
    "bsc",
    "smc",
    "classic-vecu",
    "adaptive-vecu",
]

_MODEL_IMPORT_TYPES = {"osa", "json"}
_BUILD_TYPES_BY_EXTENSION = {
    ".fmu": "fmu",
    ".sic": "sic",
    ".bsc": "bsc",
    ".smc": "smc",
}


def _resolve_file_type(import_file_path: str, file_type: ImportFileType | None) -> str | None:
    if file_type is not None:
        return file_type

    extension = Path(import_file_path).suffix.lower()
    if extension in {".osa", ".json"}:
        return extension.removeprefix(".")
    return _BUILD_TYPES_BY_EXTENSION.get(extension)


@mcp.tool(
    name="veos_import_file",
    title="Import a file into a VEOS simulation system",
    description=(
        "Imports a VEOS-supported file into an existing OSA and saves the updated OSA using the headless VEOS "
        "Model or Build Console. File types OSA, JSON, FMU, SIC, BSC, and SMC are inferred from their extension. "
        "For VECU files, file_type must be classic-vecu or adaptive-vecu. An explicit file_type can also be used "
        "for a supported container with a nonstandard extension. VEOS uses the default build settings."
    ),
    annotations=ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=False,
    ),
)
def veos_import_file(
    osa_path: str,
    import_file_path: str,
    file_type: ImportFileType | None = None,
) -> CallToolResult:
    """Import a supported file into an OSA simulation system."""
    resolved_file_type = _resolve_file_type(import_file_path, file_type)
    if resolved_file_type is None:
        return create_error_response(
            f"Could not determine the VEOS import type for {import_file_path}. "
            "Specify file_type; VECU files require classic-vecu or adaptive-vecu."
        )

    if resolved_file_type in _MODEL_IMPORT_TYPES:
        command_result = get_cli().run_model(
            "import",
            osa_path,
            "--path",
            import_file_path,
            "--save-only-on-success",
        )
    else:
        command_result = get_cli().run_build(
            resolved_file_type,
            import_file_path,
            "--output-file",
            osa_path,
        )

    if not command_result.success:
        return create_command_result_response_error(
            command_result,
            f"Failed to import file {import_file_path} into VEOS OSA {osa_path}.",
        )

    return create_command_result_response_success(command_result)
