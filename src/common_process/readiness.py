from __future__ import annotations

import socket
import time


def wait_for_tcp(host: str, port: int, *, timeout: float = 5.0, interval: float = 0.1) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with socket.create_connection((host, port), timeout=min(interval, 0.5)):
                return True
        except OSError:
            time.sleep(interval)
    return False
