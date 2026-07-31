from __future__ import annotations

from dataclasses import asdict, dataclass
import shutil
import subprocess
from typing import Iterable


class PulseError(RuntimeError):
    pass


@dataclass(frozen=True)
class PulseModule:
    sink: str
    frequency_hz: int
    module_id: int

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "PulseModule":
        return cls(
            sink=str(data["sink"]),
            frequency_hz=int(data["frequency_hz"]),
            module_id=int(data["module_id"]),
        )


class PulseManager:
    def __init__(self, executable: str = "pactl") -> None:
        self.executable = executable

    def require(self) -> None:
        if shutil.which(self.executable) is None:
            raise PulseError(f"required command not found: {self.executable}")

    def load_null_sink(self, *, sink: str, description: str, frequency_hz: int) -> PulseModule:
        self.require()
        completed = subprocess.run(
            [
                self.executable,
                "load-module",
                "module-null-sink",
                f"sink_name={sink}",
                f"sink_properties=device.description={description}",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode != 0:
            detail = completed.stderr.strip() or completed.stdout.strip()
            raise PulseError(f"failed to create sink {sink}: {detail}")
        try:
            module_id = int(completed.stdout.strip())
        except ValueError as exc:
            raise PulseError(f"unexpected pactl module id for {sink}: {completed.stdout!r}") from exc
        return PulseModule(sink=sink, frequency_hz=frequency_hz, module_id=module_id)

    def unload_modules(self, modules: Iterable[PulseModule]) -> list[str]:
        warnings: list[str] = []
        for module in modules:
            completed = subprocess.run(
                [self.executable, "unload-module", str(module.module_id)],
                check=False,
                capture_output=True,
                text=True,
            )
            if completed.returncode != 0:
                detail = completed.stderr.strip() or completed.stdout.strip()
                warnings.append(f"failed to unload module {module.module_id}: {detail}")
        return warnings

    def sink_names(self) -> set[str]:
        self.require()
        completed = subprocess.run(
            [self.executable, "list", "short", "sinks"],
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode != 0:
            return set()
        names: set[str] = set()
        for line in completed.stdout.splitlines():
            fields = line.split("\t")
            if len(fields) >= 2:
                names.add(fields[1])
        return names
