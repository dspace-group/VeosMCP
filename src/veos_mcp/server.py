"""Server startup and registration for the VEOS MCP server."""


import argparse
from collections.abc import Sequence

import importlib
import logging
import pkgutil

from veos_mcp.runtime import mcp, configure

def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse command line arguments for direct server execution."""
    parser = argparse.ArgumentParser(description="Run the VEOS MCP server.")
    parser.add_argument(
        "--veos-path",
        required=True,
        help="Path to the VEOS bin directory containing veos-sim and veos-model.",
    )
    return parser.parse_args(argv)


def load_components(package_name: str, recursive: bool = True) -> None:
    """Auto-discover and register MCP components from a package."""
    try:
        package = importlib.import_module(package_name)
    except ImportError as exception:
        raise RuntimeError(f"Could not import package '{package_name}': {exception}") from exception

    if not hasattr(package, "__path__"):
        raise ValueError(f"{package_name} is not a package")

    iterator = (
        pkgutil.walk_packages(package.__path__, package.__name__ + ".")
        if recursive
        else pkgutil.iter_modules(package.__path__, package.__name__ + ".")
    )

    for module_info in iterator:
        module_name = module_info.name

        if module_name.split(".")[-1].startswith("_"):
            continue

        try:
            importlib.import_module(module_name)
        except Exception as exception:
            logging.warning("Failed to load module %s: %s", module_name, exception)
        logging.debug("Loaded module: %s", module_name)



def main(argv: Sequence[str] | None = None) -> None:
    """Run the VEOS MCP server over stdio."""
    args = parse_args(argv)
    configure(args.veos_path)

    load_components("veos_mcp.tools")
    load_components("veos_mcp.resources")

    mcp.run()


if __name__ == "__main__":
    main()
