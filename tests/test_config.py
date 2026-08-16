from pathlib import Path

import pytest

from ka9q_radio_rigctld.config import ConfigError, load_group_config


ROOT = Path(__file__).resolve().parents[1]


def test_vara_example_loads() -> None:
    config = load_group_config(
        ROOT / "examples/vfo-streamer/vara_hf.yaml.example",
        expected_group_id="vara_hf",
    )
    assert len(config.enabled_channels) == 4
    assert config.enabled_channels[-1].frequency_hz == 14105000


def test_disabled_channel_is_not_generated(tmp_path: Path) -> None:
    profile = tmp_path / "test.yaml"
    profile.write_text(
        """
group:
  id: test
  radio: hf.local
  sample_rate: 12000
allocation:
  base_ssrc: 100
  base_port: 5000
channels:
  - id: one
    enabled: false
    frequency_hz: 1000000
    mode: usb
  - id: two
    enabled: true
    frequency_hz: 2000000
    mode: lsb
""",
        encoding="utf-8",
    )
    config = load_group_config(profile, expected_group_id="test")
    generated = config.to_legacy_shell()
    assert "one 1000000" not in generated
    assert "two 2000000 lsb" in generated


def test_group_id_must_match(tmp_path: Path) -> None:
    profile = tmp_path / "test.yaml"
    profile.write_text(
        """
group:
  id: other
  radio: hf.local
  sample_rate: 12000
allocation:
  base_ssrc: 100
  base_port: 5000
channels:
  - id: one
    frequency_hz: 1000000
    mode: usb
""",
        encoding="utf-8",
    )
    with pytest.raises(ConfigError, match="must match"):
        load_group_config(profile, expected_group_id="test")


def test_optional_network_config_is_loaded_and_exported_to_legacy_shell(tmp_path: Path) -> None:
    profile = tmp_path / "test.yaml"
    profile.write_text(
        """
group:
  id: test
  radio: hf.local
  sample_rate: 12000
network:
  multicast_interface: 192.0.2.10
  status_hostip: 192.0.2.11
allocation:
  base_ssrc: 100
  base_port: 5000
channels:
  - id: one
    frequency_hz: 1000000
    mode: usb
""",
        encoding="utf-8",
    )
    config = load_group_config(profile, expected_group_id="test")
    assert config.multicast_interface == "192.0.2.10"
    assert config.status_hostip == "192.0.2.11"
    generated = config.to_legacy_shell()
    assert "MULTICAST_INTERFACE='192.0.2.10'" in generated
    assert "STATUS_HOSTIP='192.0.2.11'" in generated
