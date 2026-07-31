from __future__ import annotations

from datetime import datetime, timezone
import os
from pathlib import Path
import signal
import subprocess
import time
from typing import Any

from .model import ProcessIdentity, ProcessSnapshot, ProcessSpec, ProcessState
from .state import atomic_write_json, read_json


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _proc_start_ticks(pid: int) -> int:
    # /proc/<pid>/stat field 22. The command name may contain spaces and parentheses,
    # so split only after the final ')'.
    raw = Path(f"/proc/{pid}/stat").read_text(encoding="utf-8")
    remainder = raw[raw.rfind(")") + 2 :].split()
    return int(remainder[19])


def _proc_cmdline(pid: int) -> tuple[str, ...]:
    raw = Path(f"/proc/{pid}/cmdline").read_bytes()
    return tuple(part.decode("utf-8", errors="replace") for part in raw.split(b"\0") if part)


def _is_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


class ManagedProcess:
    def __init__(self, *, spec: ProcessSpec, state_path: str | Path) -> None:
        self.spec = spec
        self.state_path = Path(state_path)

    def _load_identity(self) -> ProcessIdentity | None:
        data = read_json(self.state_path)
        if not isinstance(data, dict):
            return None
        try:
            return ProcessIdentity.from_dict(data)
        except (KeyError, TypeError, ValueError):
            return None

    def status(self) -> ProcessSnapshot:
        identity = self._load_identity()
        if identity is None:
            return ProcessSnapshot(ProcessState.STOPPED, None, "no state file")
        if not _is_alive(identity.pid):
            return ProcessSnapshot(ProcessState.STALE, identity, "PID is not running")
        try:
            start_ticks = _proc_start_ticks(identity.pid)
            command = _proc_cmdline(identity.pid)
        except (FileNotFoundError, ProcessLookupError):
            return ProcessSnapshot(ProcessState.STALE, identity, "process disappeared")
        if start_ticks != identity.start_ticks:
            return ProcessSnapshot(ProcessState.STALE, identity, "PID was reused")
        if command != identity.command:
            return ProcessSnapshot(ProcessState.STALE, identity, "command line no longer matches")
        return ProcessSnapshot(ProcessState.RUNNING, identity)

    def start(self, *, startup_grace: float = 0.25) -> ProcessIdentity:
        current = self.status()
        if current.state is ProcessState.RUNNING:
            raise RuntimeError(f"process already running: {self.spec.name}")
        self.spec.log_path.parent.mkdir(parents=True, exist_ok=True)
        environment: dict[str, str] | None = None
        if self.spec.environment is not None:
            environment = os.environ.copy()
            environment.update(self.spec.environment)
        with self.spec.log_path.open("ab", buffering=0) as log_handle:
            process = subprocess.Popen(
                list(self.spec.command),
                cwd=None if self.spec.working_directory is None else self.spec.working_directory,
                env=environment,
                stdin=subprocess.DEVNULL,
                stdout=log_handle,
                stderr=subprocess.STDOUT,
                start_new_session=True,
                close_fds=True,
            )
        time.sleep(startup_grace)
        if process.poll() is not None:
            raise RuntimeError(
                f"process exited during startup: {self.spec.name} (exit {process.returncode}); "
                f"see {self.spec.log_path}"
            )
        identity = ProcessIdentity(
            pid=process.pid,
            start_ticks=_proc_start_ticks(process.pid),
            command=_proc_cmdline(process.pid),
            pgid=os.getpgid(process.pid),
            started_at=_utc_now(),
        )
        atomic_write_json(self.state_path, identity.to_dict())
        return identity

    def stop(self, *, terminate_timeout: float = 2.0, kill_timeout: float = 1.0) -> bool:
        snapshot = self.status()
        if snapshot.identity is None:
            self.state_path.unlink(missing_ok=True)
            return False
        if snapshot.state is not ProcessState.RUNNING:
            self.state_path.unlink(missing_ok=True)
            return False
        identity = snapshot.identity
        try:
            os.killpg(identity.pgid, signal.SIGTERM)
        except ProcessLookupError:
            self.state_path.unlink(missing_ok=True)
            return False
        if self._wait_stopped(identity.pid, terminate_timeout):
            self.state_path.unlink(missing_ok=True)
            return True
        try:
            os.killpg(identity.pgid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        self._wait_stopped(identity.pid, kill_timeout)
        self.state_path.unlink(missing_ok=True)
        return True

    @staticmethod
    def _wait_stopped(pid: int, timeout: float) -> bool:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if not _is_alive(pid):
                return True
            time.sleep(0.05)
        return not _is_alive(pid)
