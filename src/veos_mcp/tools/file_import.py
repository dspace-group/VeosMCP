"""MCP tool for importing files into VEOS simulation systems."""

from mcp.types import CallToolResult, TextContent, ToolAnnotations

from veos_mcp.models.errors import ErrorType, VeosError
from veos_mcp.runtime import create_error_response, get_automation, mcp


@mcp.tool(
    name="veos_import_file",
    title="Import a file into a VEOS simulation system",
    description=(
        "Imports a VEOS-supported file into an existing OSA simulation system and saves the updated OSA file. "
        "Supported formats depend on the selected VEOS version and include OSA, FMU, VECU, SIC, BSC, and JSON files. "
        "VEOS uses the default import and build settings for the file type. If successful, structured content "
        "includes the build status, build output, and imported application processes. Importing can invalidate "
        "VEOS Player automation references to existing VPUs and ports."
    ),
    annotations=ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=False,
    ),
)
def veos_import_file(osa_path: str, import_file_path: str) -> CallToolResult:
    """Import a supported file into an OSA simulation system."""
    try:
        import_result = get_automation().import_file(osa_path, import_file_path)
    except Exception as exception:
        return create_error_response(f"Failed to import file {import_file_path} into VEOS: {exception}")

    if not import_result.success:
        error = VeosError(
            Type=ErrorType.PERMANENT_ERROR,
            Message=f"VEOS could not build and import file {import_file_path}. See BuildOutput for details.",
        )
        return CallToolResult(
            isError=True,
            content=[TextContent(type="text", text=error.model_dump_json(by_alias=True))],
            structuredContent=import_result.to_structured_content(),
        )

    return CallToolResult(
        isError=False,
        content=[TextContent(type="text", text=f"Imported file {import_file_path} into VEOS.")],
        structuredContent=import_result.to_structured_content(),
    )
