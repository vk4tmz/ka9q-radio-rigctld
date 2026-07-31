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
