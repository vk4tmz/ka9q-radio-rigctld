from __future__ import annotations

import logging
import threading
import time
from typing import Any

from ka9q_common.network import resolve_multicast_interface, resolve_status_hostip
from ka9qradio import Ka9qRadioClient, ReceiverConfig, StatusListener, StatusType


class RadioSession:
    """Long-running single-SSRC adapter over the shared ka9q-radio package."""

    def __init__(
        self,
        radio: str,
        ssrc: int,
        *,
        multicast_interface: str | None = None,
        status_interface: str | None = None,
        status_poll_seconds: float = 0.5,
    ) -> None:
        self.log = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.radio = radio
        self.ssrc = ssrc
        self.status_poll_seconds = status_poll_seconds
        self.multicast_interface = resolve_multicast_interface(
            cli=multicast_interface, logger=self.log
        ).value
        self.status_interface = resolve_status_hostip(
            cli=status_interface, default="0.0.0.0", logger=self.log
        ).value or "0.0.0.0"
        self.client = Ka9qRadioClient(radio, interface=self.multicast_interface)
        self.listener = StatusListener(
            radio,
            interface=self.status_interface,
            timeout=min(0.2, status_poll_seconds),
        )
        self.status: dict[int, dict[StatusType | int, Any]] = {}
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._run,
            name=f"ka9q-status-{self.ssrc}",
            daemon=True,
        )
        self._thread.start()

    def _run(self) -> None:
        while not self._stop.is_set():
            try:
                latest = self.listener.latest(
                    duration=self.status_poll_seconds,
                    ssrc=self.ssrc,
                )
                if latest:
                    self.status.update(latest)
            except Exception:
                self.log.exception("Unable to collect KA9Q status for SSRC %s", self.ssrc)
                self._stop.wait(self.status_poll_seconds)

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=max(2.0, self.status_poll_seconds * 3))
            self._thread = None

    def tune(self, frequency_hz: float, preset: str) -> None:
        receiver = ReceiverConfig(
            ssrc=self.ssrc,
            frequency_hz=frequency_hz,
            preset=preset.lower(),
        )
        self.client.apply(receiver)

    def latest_status(self) -> dict[StatusType | int, Any] | None:
        return self.status.get(self.ssrc)

    def wait_for_status(self, timeout: float | None = None) -> dict[StatusType | int, Any] | None:
        deadline = None if timeout is None else time.monotonic() + timeout
        while deadline is None or time.monotonic() < deadline:
            status = self.latest_status()
            if status is not None:
                return status
            if self._stop.wait(0.1):
                break
        return None
