"""MCP tools for system/osa file build."""

import anyio
from anyio import to_thread
from mcp.server.mcpserver import Context
from mcp.types import CallToolResult, TextContent, ToolAnnotations

from veos_mcp.models.cli_command_result import CliCommandResult
from veos_mcp.runtime import (
    create_command_result_response_error,
    create_command_result_response_success,
    create_error_response,
    get_cli,
    mcp,
)


@mcp.tool(
    name="get_build_import_config_schema",
    title="Get Build Import Config Schema",
    description="Build/Import config schema for configuring the build/import of container/model. Yaml file has to be placed next to the container (fmu/sic/bsc/ssp).",
)
def veos_get_build_import_config_schema() -> CallToolResult:
    cli = get_cli()

    if cli.get_installation().year < 2026 or (cli.get_installation().year == 2026 and cli.get_installation().release == "A"):
        return create_error_response("Schema support from release VEOS 26-B.")

    context = TextContent(
        text="The yaml file should be placed next to the container (fmu/sic/bsc/ssp) as a <container>.icfg.yaml file, <container>.icfg.yaml is also accepted. "
        "Naming convention: Controller.fmu Controller.fmu.icfg.yaml"
        "If and only if multiple config build files for same containter are needed, specify a config_identifier for the system_build tool call by following this naming:"
        " <container>.<identifier>.icfg.yaml. If no yaml is provided, the build/import will use the default VEOS configurations, "
        "same for properties within the schema. Prefer to only set the necessary properties that are explicitly defined/requested by the user."
    )
    path = TextContent(text=f"{cli.get_installation().schema_path / 'import-config.schema.json'}")

    return CallToolResult(is_error=False, content=[context, path])


@mcp.tool(
    name="system_build",
    title="Building an osa file describing the simulation system",
    description="Tool for building/importing models into one simulation system, described as an osa file.",
    annotations=ToolAnnotations(
        read_only_hint=False,
        destructive_hint=False,
        idempotent_hint=True,
        open_world_hint=False,
    ),
)
async def system_build_tool(
    target_osa_path: str,
    models: list[str],
    ctx: Context,
    config_identifier: str | None = None,
    log_file: str | None = None,
    build_directory: str | None = None,
) -> CallToolResult:

    if config_identifier is not None:
        config_name_argument = ["--config-name", config_identifier]
    else:
        config_name_argument = []

    if log_file is not None:
        log_file_argument = ["--log-file-path", log_file]
    else:
        log_file_argument = []

    if build_directory is not None:
        build_directory_argument = ["--build-directory", build_directory]
    else:
        build_directory_argument = []

    build_cli_arguments = (
        "multi",
        *models,
        "--output-file",
        target_osa_path,
        *config_name_argument,
        *log_file_argument,
        *build_directory_argument,
    )

    # builds can take 20 minutes, prevent timeouts by reporting progress to client

    async def report_build_heartbeat(ctx: Context) -> None:
        heartbeat_counter = 0
        while True:
            await ctx.report_progress(progress=heartbeat_counter, message="Build in progress.")
            heartbeat_counter += 1
            await anyio.sleep(15)

    cli = get_cli()

    async def run_build_with_heartbeat() -> CliCommandResult:
        result: CliCommandResult | None = None
        async with anyio.create_task_group() as task_group:
            task_group.start_soon(report_build_heartbeat, ctx)
            try:
                result = await to_thread.run_sync(cli.run_build, *build_cli_arguments)
            finally:
                task_group.cancel_scope.cancel()
        if result is None:
            raise RuntimeError("VEOS build completed without a command result.")
        return result

    command_result = await run_build_with_heartbeat()

    if not command_result.success:
        return create_command_result_response_error(command_result, f"Failed to build OSA file at {target_osa_path}.")

    return create_command_result_response_success(command_result)
