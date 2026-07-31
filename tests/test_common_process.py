from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest

from common_process import FileLock, LockUnavailable, ManagedProcess, ProcessSpec, ProcessState, atomic_write_json, read_json


def test_atomic_json_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "state.json"
    atomic_write_json(path, {"hello": "world"})
    assert read_json(path) == {"hello": "world"}
    assert path.stat().st_mode & 0o777 == 0o600


def test_file_lock_is_non_blocking(tmp_path: Path) -> None:
    path = tmp_path / "lock"
    first = FileLock(path)
    second = FileLock(path)
    first.acquire()
    try:
        with pytest.raises(LockUnavailable):
            second.acquire()
    finally:
        first.release()


def test_managed_process_start_status_stop(tmp_path: Path) -> None:
    state = tmp_path / "process.json"
    process = ManagedProcess(
        spec=ProcessSpec.create(
            name="sleeper",
            command=[sys.executable, "-c", "import time; time.sleep(30)"],
            log_path=tmp_path / "process.log",
        ),
        state_path=state,
    )
    identity = process.start(startup_grace=0.05)
    assert identity.pid > 0
    assert process.status().state is ProcessState.RUNNING
    assert process.stop(terminate_timeout=1.0, kill_timeout=1.0)
    assert process.status().state is ProcessState.STOPPED


def test_pid_identity_tamper_is_stale(tmp_path: Path) -> None:
    state = tmp_path / "process.json"
    process = ManagedProcess(
        spec=ProcessSpec.create(
            name="sleeper",
            command=[sys.executable, "-c", "import time; time.sleep(30)"],
            log_path=tmp_path / "process.log",
        ),
        state_path=state,
    )
    process.start(startup_grace=0.05)
    data = json.loads(state.read_text())
    data["start_ticks"] += 1
    state.write_text(json.dumps(data))
    try:
        assert process.status().state is ProcessState.STALE
    finally:
        # Restore the identity so cleanup can safely terminate the real child.
        data["start_ticks"] -= 1
        state.write_text(json.dumps(data))
        process.stop(terminate_timeout=1.0, kill_timeout=1.0)
