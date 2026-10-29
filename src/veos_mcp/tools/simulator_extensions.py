"""MCP tools for system/osa file build."""

from mcp.types import CallToolResult, TextContent, ToolAnnotations

from veos_mcp.runtime import (
    get_cli,
    mcp,
)


@mcp.tool(
    name="veos_get_cosim_docs",
    title="Get VEOS CoSim documentation",
    description="Returns VEOS CoSimulation interface documentation. DsVeosCoSim instances are imported from JSON as part of a veos_system_build. "
    "This tool returns the JSON schema files and the link to the GitHub documentation",
    annotations=ToolAnnotations(
        read_only_hint=True,
        destructive_hint=False,
        idempotent_hint=True,
        open_world_hint=False,
    ),
)
def veos_get_cosim_docs() -> CallToolResult:
    cli = get_cli()

    base_schema_path = f"{cli.get_installation().schema_path / 'simulator-extension.base.schema.json'}"
    cosim_schema_path = f"{cli.get_installation().schema_path / 'DsVeosCoSim.schema.json'}"

    response = TextContent(
        text=f"{cosim_schema_path}; {base_schema_path}; veos-cosim-client github doc: https://github.com/dspace-group/veos-cosim-client"
    )

    return CallToolResult(is_error=False, content=[response])


@mcp.tool(
    name="veos_get_qemu_docs",
    title="Get VEOS Qemu extension documentation",
    description="Returns VEOS Qemu extension documentation. DsVeosQemu instances are imported from JSON as part of a veos_system_build. "
    "This tool returns the JSON schema files",
    annotations=ToolAnnotations(
        read_only_hint=True,
        destructive_hint=False,
        idempotent_hint=True,
        open_world_hint=False,
    ),
)
def veos_get_qemu_docs() -> CallToolResult:
    cli = get_cli()

    base_schema_path = f"{cli.get_installation().schema_path / 'simulator-extension.base.schema.json'}"
    cosim_schema_path = f"{cli.get_installation().schema_path / 'DsVeosCoSim.schema.json'}"

    response = TextContent(
        text=f"{cosim_schema_path}; {base_schema_path}; veos-cosim-client github doc: https://github.com/dspace-group/veos-cosim-client"
    )

    return CallToolResult(is_error=False, content=[response])


@mcp.tool(
    name="veos_get_hsil_docs",
    title="Get VEOS HSIL CoSim documentation",
    description="Returns HSIL CoSim interface documentation. HSIL instances are imported from JSON as part of a veos_system_build. "
    "This tool returns the JSON schema files and the link to the GitHub documentation",
    annotations=ToolAnnotations(
        read_only_hint=True,
        destructive_hint=False,
        idempotent_hint=True,
        open_world_hint=False,
    ),
)
def veos_get_hsil_docs() -> CallToolResult:
    cli = get_cli()

    hsil_schema_path = f"{cli.get_installation().schema_path / 'hsil-simulation-configuration.schema'}"

    # TODO other links might be needed: https://github.com/dspace-group/hsil-lib
    response = TextContent(text=f"{hsil_schema_path}")

    return CallToolResult(is_error=False, content=[response])
