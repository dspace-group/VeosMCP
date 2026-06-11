"""VEOS CLI path resolution and subprocess execution helpers."""

from pathlib import Path
import subprocess

from threading import Lock
from collections.abc import Iterable

from veos_mcp.models.cli_command_result import CliCommandResult, CommandResultCode
from veos_mcp.veos_path_resolver import resolve_veos_path


DEFAULT_COMMAND_TIMEOUT_SECONDS = 40.0
_COMMAND_GATE = Lock()


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
        stdout_bytes, stderr_bytes = process.communicate(
            timeout=command_timeout_seconds
        )
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
        *,
        veos_version: str | None,
        veos_path: str | None,
        command_timeout_seconds: float = DEFAULT_COMMAND_TIMEOUT_SECONDS,
    ) -> None:

        if veos_path is not None:
            self.veos_path = Path(veos_path)
            if not self.veos_path.is_file():
                raise ValueError(
                    f"Provided VEOS path is invalid, make sure that the provided path '{veos_path}' "
                    f"points to an existing veos.exe."
                )
        else:
            self.veos_path = resolve_veos_path(veos_version)
        self.command_timeout_seconds = command_timeout_seconds

    def run_sim(self, *arguments: str) -> CliCommandResult:
        """Run the VEOS simulator CLI with serialized access."""
        return self._run_locked(self.veos_path, ("sim", *arguments))

    def run_model(self, *arguments: str) -> CliCommandResult:
        """Run the VEOS model CLI with serialized access."""
        return self._run_locked(self.veos_path, ("model", *arguments))

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
