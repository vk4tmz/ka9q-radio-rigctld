from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Sequence


class ProcessState(str, Enum):
    RUNNING = "RUNNING"
    STOPPED = "STOPPED"
    STALE = "STALE"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class ProcessSpec:
    name: str
    command: tuple[str, ...]
    log_path: Path
    working_directory: Path | None = None
    environment: dict[str, str] | None = None

    @classmethod
    def create(
        cls,
        *,
        name: str,
        command: Sequence[str],
        log_path: str | Path,
        working_directory: str | Path | None = None,
        environment: dict[str, str] | None = None,
    ) -> "ProcessSpec":
        if not name.strip():
            raise ValueError("process name must not be empty")
        if not command:
            raise ValueError("process command must not be empty")
        return cls(
            name=name,
            command=tuple(str(part) for part in command),
            log_path=Path(log_path),
            working_directory=None if working_directory is None else Path(working_directory),
            environment=environment,
        )


@dataclass(frozen=True)
class ProcessIdentity:
    pid: int
    start_ticks: int
    command: tuple[str, ...]
    pgid: int
    started_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProcessIdentity":
        return cls(
            pid=int(data["pid"]),
            start_ticks=int(data["start_ticks"]),
            command=tuple(str(value) for value in data["command"]),
            pgid=int(data.get("pgid", data["pid"])),
            started_at=str(data["started_at"]),
        )


@dataclass(frozen=True)
class ProcessSnapshot:
    state: ProcessState
    identity: ProcessIdentity | None
    reason: str = ""
