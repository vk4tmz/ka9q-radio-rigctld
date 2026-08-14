from __future__ import annotations

from pathlib import Path

from ka9q_radio_rigctld.config import ChannelConfig, GroupConfig
from ka9q_radio_rigctld.lifecycle import GroupLifecycle
from ka9q_radio_rigctld.pulse import PulseModule


class FakePulse:
    def __init__(self) -> None:
        self.modules: list[PulseModule] = []

    def load_null_sink(self, *, sink: str, description: str, frequency_hz: int) -> PulseModule:
        module = PulseModule(sink=sink, frequency_hz=frequency_hz, module_id=100 + len(self.modules))
        self.modules.append(module)
        return module

    def unload_modules(self, modules):
        for module in list(modules):
            self.modules = [item for item in self.modules if item.module_id != module.module_id]
        return []

    def sink_names(self) -> set[str]:
        return {module.sink for module in self.modules}


def test_disabled_channels_appear_in_status(tmp_path: Path) -> None:
    config = GroupConfig(
        group_id="test",
        radio="hf.local",
        sample_rate=12000,
        base_ssrc=100,
        base_port=4500,
        channels=(
            ChannelConfig("enabled", 7000000, "usb", True, "vc_test_enabled"),
            ChannelConfig("disabled", 7100000, "usb", False, "vc_test_disabled"),
        ),
    )
    lifecycle = GroupLifecycle(config=config, state_root=tmp_path, pulse=FakePulse())
    rows = lifecycle.status_rows()
    assert rows[0]["status"] == "STOPPED"
    assert rows[1]["status"] == "DISABLED"


def test_streamer_command_forwards_yaml_network_values(tmp_path: Path) -> None:
    config = GroupConfig(
        group_id="test",
        radio="hf.local",
        sample_rate=12000,
        base_ssrc=100,
        base_port=4500,
        channels=(ChannelConfig("one", 7000000, "usb", True, "vc_test_one"),),
        multicast_interface="192.0.2.10",
        status_hostip="192.0.2.11",
    )
    lifecycle = GroupLifecycle(
        config=config, state_root=tmp_path, pulse=FakePulse(), streamer_command="ka9q-vfo-streamer"
    )
    runtime = lifecycle._channel_runtime(0, config.enabled_channels[0])
    command = list(lifecycle._process(runtime).spec.command)
    assert command[-4:] == [
        "--multicast-interface", "192.0.2.10",
        "--status-hostip", "192.0.2.11",
    ]


def test_python_status_requires_audio_helper(monkeypatch, tmp_path: Path) -> None:
    config = GroupConfig(
        group_id="test",
        radio="hf.local",
        sample_rate=12000,
        base_ssrc=100,
        base_port=4500,
        channels=(ChannelConfig("one", 7000000, "usb", True, "vc_test_one"),),
    )
    lifecycle = GroupLifecycle(config=config, state_root=tmp_path, pulse=FakePulse())
    runtime = lifecycle._channel_runtime(0, config.enabled_channels[0])

    from ka9q_common.process import ProcessIdentity, ProcessSnapshot, ProcessState
    import ka9q_radio_rigctld.lifecycle as lifecycle_module

    identity = ProcessIdentity(pid=1234, start_ticks=1, command=("streamer",), pgid=1234, started_at="now")
    class FakeProcess:
        def status(self):
            return ProcessSnapshot(ProcessState.RUNNING, identity)

    monkeypatch.setattr(lifecycle, "_process", lambda _runtime: FakeProcess())
    lifecycle.pulse.modules.append(PulseModule(sink=runtime.sink, frequency_hz=runtime.frequency_hz, module_id=100))
    monkeypatch.setattr(lifecycle_module, "_tcp_open", lambda host, port: True)
    monkeypatch.setattr(lifecycle_module, "_audio_helper_alive", lambda pid: False)
    rows = lifecycle.status_rows()
    assert rows[0]["audio"] == "DEAD"
    assert rows[0]["status"] == "DEGRADED"

    monkeypatch.setattr(lifecycle_module, "_audio_helper_alive", lambda pid: True)
    rows = lifecycle.status_rows()
    assert rows[0]["audio"] == "OK"
    assert rows[0]["status"] == "RUNNING"
