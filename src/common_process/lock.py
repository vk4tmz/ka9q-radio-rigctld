from __future__ import annotations

import fcntl
from pathlib import Path
from types import TracebackType
from typing import IO


class LockUnavailable(RuntimeError):
    """Raised when a non-blocking advisory lock cannot be acquired."""


class FileLock:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._handle: IO[str] | None = None

    def acquire(self, *, blocking: bool = False) -> None:
        if self._handle is not None:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        handle = self.path.open("a+", encoding="utf-8")
        flags = fcntl.LOCK_EX | (0 if blocking else fcntl.LOCK_NB)
        try:
            fcntl.flock(handle.fileno(), flags)
        except BlockingIOError as exc:
            handle.close()
            raise LockUnavailable(f"lock already held: {self.path}") from exc
        self._handle = handle

    def release(self) -> None:
        if self._handle is None:
            return
        fcntl.flock(self._handle.fileno(), fcntl.LOCK_UN)
        self._handle.close()
        self._handle = None

    def __enter__(self) -> "FileLock":
        self.acquire()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.release()
