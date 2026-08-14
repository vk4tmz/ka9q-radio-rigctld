from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path
import shutil
import socket
from typing import Any

from ka9q_common.io import atomic_write_json, read_json
from ka9q_common.process import (
    FileLock,
    LockUnavailable,
    ManagedProcess,
    ProcessSpec,
    ProcessState,
)
from ka9q_common.time import utc_timestamp

from .config import GroupConfig
from .pulse import PulseManager, PulseModule


class LifecycleError(RuntimeError):
    pass


@dataclass(frozen=True)
class ChannelRuntime:
    id: str
    frequency_hz: int
    mode: str
    sink: str
    ssrc: int
    port: int
    process_state_path: str
    log_path: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ChannelRuntime":
        return cls(
            id=str(data["id"]),
            frequency_hz=int(data["frequency_hz"]),
            mode=str(data["mode"]),
            sink=str(data["sink"]),
            ssrc=int(data["ssrc"]),
            port=int(data["port"]),
            process_state_path=str(data["process_state_path"]),
            log_path=str(data["log_path"]),
        )


@dataclass(frozen=True)
class GroupRuntimeState:
    schema_version: int
    group_id: str
    created_at: str
    modules: tuple[PulseModule, ...]
    channels: tuple[ChannelRuntime, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "group_id": self.group_id,
            "created_at": self.created_at,
            "modules": [module.to_dict() for module in self.modules],
            "channels": [channel.to_dict() for channel in self.channels],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GroupRuntimeState":
        return cls(
            schema_version=int(data.get("schema_version", 1)),
            group_id=str(data["group_id"]),
            created_at=str(data.get("created_at", "")),
            modules=tuple(PulseModule.from_dict(item) for item in data.get("modules", [])),
            channels=tuple(ChannelRuntime.from_dict(item) for item in data.get("channels", [])),
        )


class GroupLifecycle:
    def __init__(
        self,
        *,
        config: GroupConfig,
        state_root: str | Path | None = None,
        pulse: PulseManager | None = None,
        streamer_command: str | None = None,
    ) -> None:
        self.config = config
        root = Path(state_root) if state_root is not None else Path.home() / ".local" / "state" / "ka9q-radio" / "vfo_streamer"
        self.group_state_dir = root.expanduser().resolve() / config.group_id
        self.state_path = self.group_state_dir / "state.json"
        self.lock_path = self.group_state_dir / ".group.lock"
        self.pulse = pulse or PulseManager()
        self.streamer_command = streamer_command or shutil.which("ka9q-vfo-streamer") or "ka9q-vfo-streamer"

    def _channel_runtime(self, offset: int, channel: Any) -> ChannelRuntime:
        sink = channel.sink or f"vc_{self.config.group_id}_{channel.id}"
        return ChannelRuntime(
            id=channel.id,
            frequency_hz=channel.frequency_hz,
            mode=channel.mode,
            sink=sink,
            ssrc=self.config.base_ssrc + offset,
            port=self.config.base_port + offset,
            process_state_path=str(self.group_state_dir / "processes" / f"{channel.id}.json"),
            log_path=str(self.group_state_dir / "logs" / f"vfo_{channel.id}_{channel.frequency_hz}.log"),
        )

    def _process(self, runtime: ChannelRuntime) -> ManagedProcess:
        command = [
            self.streamer_command,
            self.config.radio,
            str(runtime.ssrc),
            str(runtime.frequency_hz),
            runtime.mode,
            "-ar",
            str(self.config.sample_rate),
            "-ad",
            runtime.sink,
            "--host",
            "localhost",
            "--port",
            str(runtime.port),
        ]
        if self.config.multicast_interface:
            command.extend(["--multicast-interface", self.config.multicast_interface])
        if self.config.status_hostip:
            command.extend(["--status-hostip", self.config.status_hostip])
        return ManagedProcess(
            spec=ProcessSpec.create(
                name=f"{self.config.group_id}:{runtime.id}",
                command=command,
                log_path=runtime.log_path,
            ),
            state_path=runtime.process_state_path,
        )

    def load_state(self) -> GroupRuntimeState | None:
        data = read_json(self.state_path)
        if not isinstance(data, dict):
            return None
        try:
            return GroupRuntimeState.from_dict(data)
        except (KeyError, TypeError, ValueError):
            return None

    def start(self) -> GroupRuntimeState:
        self.group_state_dir.mkdir(parents=True, exist_ok=True)
        try:
            with FileLock(self.lock_path):
                self._stop_unlocked()
                modules: list[PulseModule] = []
                channels: list[ChannelRuntime] = []
                started: list[ManagedProcess] = []
                try:
                    for offset, channel in enumerate(self.config.enabled_channels):
                        runtime = self._channel_runtime(offset, channel)
                        module = self.pulse.load_null_sink(
                            sink=runtime.sink,
                            description=f"{self.config.group_id} VFO {runtime.id}",
                            frequency_hz=runtime.frequency_hz,
                        )
                        modules.append(module)
                        process = self._process(runtime)
                        process.start()
                        started.append(process)
                        channels.append(runtime)
                    state = GroupRuntimeState(
                        schema_version=1,
                        group_id=self.config.group_id,
                        created_at=utc_timestamp(),
                        modules=tuple(modules),
                        channels=tuple(channels),
                    )
                    atomic_write_json(self.state_path, state.to_dict())
                    return state
                except Exception:
                    for process in reversed(started):
                        process.stop()
                    self.pulse.unload_modules(reversed(modules))
                    self.state_path.unlink(missing_ok=True)
                    raise
        except LockUnavailable as exc:
            raise LifecycleError(str(exc)) from exc

    def stop(self) -> None:
        self.group_state_dir.mkdir(parents=True, exist_ok=True)
        try:
            with FileLock(self.lock_path):
                self._stop_unlocked()
        except LockUnavailable as exc:
            raise LifecycleError(str(exc)) from exc

    def _stop_unlocked(self) -> None:
        state = self.load_state()
        if state is None:
            return
        for runtime in reversed(state.channels):
            self._process(runtime).stop()
        self.pulse.unload_modules(reversed(state.modules))
        self.state_path.unlink(missing_ok=True)

    def restart(self) -> GroupRuntimeState:
        return self.start()

    def status_rows(self) -> list[dict[str, Any]]:
        state = self.load_state()
        sinks = self.pulse.sink_names()
        runtime_by_id = {} if state is None else {channel.id: channel for channel in state.channels}
        rows: list[dict[str, Any]] = []
        allocation = 0
        for channel in self.config.channels:
            if not channel.enabled:
                rows.append({
                    "id": channel.id,
                    "frequency_hz": channel.frequency_hz,
                    "process": "-",
                    "sink": "-",
                    "rigctld": "-",
                    "status": "DISABLED",
                })
                continue
            runtime = runtime_by_id.get(channel.id) or self._channel_runtime(allocation, channel)
            allocation += 1
            snapshot = self._process(runtime).status()
            sink_ok = runtime.sink in sinks
            port_ok = _tcp_open("127.0.0.1", runtime.port)
            if snapshot.state is ProcessState.RUNNING and sink_ok and port_ok:
                overall = "RUNNING"
            elif snapshot.state is ProcessState.STOPPED and not sink_ok and not port_ok:
                overall = "STOPPED"
            elif snapshot.state is ProcessState.STALE:
                overall = "STALE"
            else:
                overall = "DEGRADED"
            rows.append({
                "id": runtime.id,
                "frequency_hz": runtime.frequency_hz,
                "process": f"PID {snapshot.identity.pid}" if snapshot.identity and snapshot.state is ProcessState.RUNNING else snapshot.state.value,
                "sink": "present" if sink_ok else "missing",
                "rigctld": f":{runtime.port} open" if port_ok else f":{runtime.port} closed",
                "status": overall,
            })
        return rows


def _tcp_open(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=0.15):
            return True
    except OSError:
        return False
