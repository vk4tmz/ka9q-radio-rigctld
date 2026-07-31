"""Reusable local-process lifecycle primitives.

This package is intentionally Linux-focused and currently lives inside
``ka9q-radio-rigctld`` while its API is proven by real consumers.
"""

from .lock import FileLock, LockUnavailable
from .model import ProcessIdentity, ProcessSnapshot, ProcessSpec, ProcessState
from .process import ManagedProcess
from .readiness import wait_for_tcp
from .state import atomic_write_json, read_json

__all__ = [
    "FileLock",
    "LockUnavailable",
    "ManagedProcess",
    "ProcessIdentity",
    "ProcessSnapshot",
    "ProcessSpec",
    "ProcessState",
    "atomic_write_json",
    "read_json",
    "wait_for_tcp",
]
