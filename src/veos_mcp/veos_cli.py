"""VEOS CLI path resolution and subprocess execution helpers."""

from __future__ import annotations

import os
import subprocess
from collections.abc import Iterable
from pathlib import Path
from threading import Lock

from veos_mcp.schemas.cli_command_result import CliCommandResult, CommandResultCode


DEFAULT_COMMAND_TIMEOUT_SECONDS = 40.0
_COMMAND_GATE = Lock()


def resolve_executable_path(base_path: Path, file_name: str) -> Path:
    """Resolve a VEOS executable path from the configured VEOS bin directory."""
    resolved_path = Path(f"{base_path / file_name}.exe") if os.name == "nt" else base_path / file_name
    return resolved_path if resolved_path.is_file() else Path()


def run_process_command(
    executable_path: str | Path,
    arguments: Iterable[str],
    *,
    command_timeout_seconds: float = DEFAULT_COMMAND_TIMEOUT_SECONDS,
) -> CliCommandResult:
    """Run a VEOS subprocess and normalize its exit state and output."""
    resolved_executable = Path(executable_path)
    command_name = resolved_executable.name or str(executable_path)

    try:
        process = _start_process(resolved_executable, arguments)
    except OSError as exception:
        return CliCommandResult(
            success=False,
            exit_code=None,
            code=CommandResultCode.PROCESS_START_FAILED,
            stdout="",
            stdout_bytes=b"",
            stderr=str(exception),
        )

    with process:
        _close_stdin(process)
        return _collect_process_result(
            process,
            command_name,
            command_timeout_seconds,
        )


def _start_process(
    resolved_executable: Path,
    arguments: Iterable[str],
) -> subprocess.Popen[bytes]:
    return subprocess.Popen(
        [str(resolved_executable), *arguments],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _close_stdin(process: subprocess.Popen[bytes]) -> None:
    if process.stdin is not None:
        process.stdin.close()


def _collect_process_result(
    process: subprocess.Popen[bytes],
    command_name: str,
    command_timeout_seconds: float,
) -> CliCommandResult:
    try:
        stdout_bytes, stderr_bytes = process.communicate(timeout=command_timeout_seconds)
    except subprocess.TimeoutExpired:
        return _timeout_result(process, command_name, command_timeout_seconds)
    return _completed_result(process.returncode, stdout_bytes, stderr_bytes)


def _timeout_result(
    process: subprocess.Popen[bytes],
    command_name: str,
    command_timeout_seconds: float,
) -> CliCommandResult:
    cleanup_error = _kill_process(process, command_name)
    return CliCommandResult(
        success=False,
        exit_code=None,
        code=CommandResultCode.PROCESS_TIMED_OUT,
        stdout="",
        stdout_bytes=b"",
        stderr=(
            f"The VEOS command {command_name} timed out after "
            f"{command_timeout_seconds:0.0f} seconds.{cleanup_error}"
        ),
    )


def _kill_process(process: subprocess.Popen[bytes], command_name: str) -> str:
    try:
        _kill_and_wait(process)
    except OSError as exception:
        return f" Failed to terminate timed-out process {command_name}: {exception}"
    return ""


def _kill_and_wait(process: subprocess.Popen[bytes]) -> None:
    process.kill()
    process.communicate()


def _completed_result(
    exit_code: int,
    stdout_bytes: bytes,
    stderr_bytes: bytes,
) -> CliCommandResult:
    stdout = stdout_bytes.decode("utf-8", errors="replace").strip()
    stderr = stderr_bytes.decode("utf-8", errors="replace").strip()

    if exit_code == 0:
        return CliCommandResult(
            success=True,
            exit_code=exit_code,
            code=CommandResultCode.OK,
            stdout=stdout,
            stdout_bytes=stdout_bytes,
            stderr=stderr,
        )

    return CliCommandResult(
        success=False,
        exit_code=exit_code,
        code=CommandResultCode.PROCESS_FAILED,
        stdout=stdout,
        stdout_bytes=stdout_bytes,
        stderr=stderr,
    )


class VeosCli:
    """Facade for serialized VEOS simulator and model CLI access."""

    def __init__(
        self,
        veos_path: str | Path,
        *,
        command_timeout_seconds: float = DEFAULT_COMMAND_TIMEOUT_SECONDS,
    ) -> None:
        normalized_path = Path(veos_path)
        if not str(veos_path).strip():
            raise RuntimeError(
                "Missing required command line argument '--veos-path'. "
                "Configure it in the MCP server startup arguments."
            )
        if not normalized_path.is_dir():
            raise FileNotFoundError(
                "command line argument '--veos-path' does not point to a valid directory: "
                f"{veos_path}"
            )

        sim_path = resolve_executable_path(normalized_path, "veos-sim")
        model_path = resolve_executable_path(normalized_path, "veos-model")
        if not sim_path or not model_path:
            raise FileNotFoundError(
                "command line argument '--veos-path' does not point to a valid VEOS "
                f"installation path: {veos_path}. Make sure that the path points to the "
                "bin directory of your local VEOS installation."
            )

        self.veos_path = normalized_path
        self.sim_path = sim_path
        self.model_path = model_path
        self.command_timeout_seconds = command_timeout_seconds

    @classmethod
    def from_executables(
        cls,
        sim_path: str | Path,
        model_path: str | Path,
        *,
        command_timeout_seconds: float = DEFAULT_COMMAND_TIMEOUT_SECONDS,
    ) -> "VeosCli":
        """Create an instance with explicit executable paths for tests."""
        instance = cls.__new__(cls)
        instance.veos_path = Path(sim_path).parent
        instance.sim_path = Path(sim_path)
        instance.model_path = Path(model_path)
        instance.command_timeout_seconds = command_timeout_seconds
        return instance

    def run_sim(self, *arguments: str) -> CliCommandResult:
        """Run the VEOS simulator CLI with serialized access."""
        return self._run_locked(self.sim_path, arguments)

    def run_model(self, *arguments: str) -> CliCommandResult:
        """Run the VEOS model CLI with serialized access."""
        return self._run_locked(self.model_path, arguments)

    def _run_locked(
        self,
        executable_path: Path,
        arguments: tuple[str, ...],
    ) -> CliCommandResult:
        with _COMMAND_GATE:
            return run_process_command(
                executable_path,
                arguments,
                command_timeout_seconds=self.command_timeout_seconds,
            )
