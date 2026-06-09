"""Server startup and registration for the VEOS MCP server."""


import argparse
from collections.abc import Sequence

import veos_mcp.tools # pylint: disable=unused-import
import veos_mcp.resources # pylint: disable=unused-import

from veos_mcp.runtime import mcp, configure

def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse command line arguments for direct server execution."""
    parser = argparse.ArgumentParser(description="Run the VEOS MCP server.")
    parser.add_argument(
        "--veos-version",
        required=False,
        help="VEOS version, e.g. '26.1'. If not provided, the server will use the newest VEOS installation.",
    )
    parser.add_argument(
        "--veos-path",
        required=False,
        help=argparse.SUPPRESS,
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    """Run the VEOS MCP server over stdio."""
    args = parse_args(argv)
    configure(veos_version=args.veos_version, veos_path=args.veos_path)

    mcp.run()


if __name__ == "__main__":
    main()
