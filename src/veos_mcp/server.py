"""Server startup and registration for the VEOS MCP server."""

import argparse
import os
from collections.abc import Sequence

import veos_mcp.resources  # noqa: F401
import veos_mcp.tools  # noqa: F401
from veos_mcp.runtime import configure_cli, mcp


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse command line arguments for direct server execution."""
    parser = argparse.ArgumentParser(description="Run the VEOS MCP server.")
    parser.add_argument(
        "--veos-version",
        required=False,
        help="VEOS version, e.g. '26.1'. If not provided, the server will use the newest VEOS installation.",
    )
    parser.add_argument("--veos-bin-path", required=False, help=argparse.SUPPRESS)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    """Run the VEOS MCP server over stdio."""
    args = parse_args(argv)

    if os.environ.get("VEOS_MCP_SKIP_CONFIGURE") != "1":
        configure_cli(veos_version=args.veos_version, veos_bin_path=args.veos_bin_path)

    mcp.run()


if __name__ == "__main__":
    main()
