from pathlib import Path

import pytest

from ka9q_radio_rigctld.config import ConfigError, load_group_config


ROOT = Path(__file__).resolve().parents[1]


def test_hf_aprs_example_loads() -> None:
    config = load_group_config(
        ROOT / "examples/vfo-streamer/hf_aprs.yaml.example",
        expected_group_id="hf_aprs",
    )
    assert [channel.id for channel in config.enabled_channels] == ["7048", "10147"]
    assert config.base_ssrc == 9999991
    assert config.base_port == 4591


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
