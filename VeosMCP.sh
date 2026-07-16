#!/usr/bin/env sh

set -eu

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)

exec uv --directory "$script_dir" run python -m veos_mcp.server "$@"