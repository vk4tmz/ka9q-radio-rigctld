from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys

from .config import ConfigError, GroupConfig, load_group_config

DEFAULT_CONFIG_DIR = Path.home() / ".config" / "ka9q-radio" / "vfo_streamer"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ka9q-vfo-group",
        description="Manage configured KA9Q virtual VFO groups.",
    )
    parser.add_argument(
        "-c",
        "--config-dir",
        type=Path,
        default=DEFAULT_CONFIG_DIR,
        help=f"profile directory (default: {DEFAULT_CONFIG_DIR})",
    )
    parser.add_argument("group_or_list", help="group ID or 'list'")
    parser.add_argument(
        "action",
        nargs="?",
        choices=("start", "stop", "restart", "status", "validate"),
        help="group action",
    )
    return parser


def _yaml_path(config_dir: Path, group_id: str) -> Path:
    group_dir = config_dir / group_id
    for suffix in ("yaml", "yml"):
        candidate = group_dir / f"{group_id}.{suffix}"
        if candidate.is_file():
            return candidate
    return group_dir / f"{group_id}.yaml"


def _write_generated_config(config_dir: Path, config: GroupConfig) -> Path:
    group_dir = config_dir / config.group_id
    group_dir.mkdir(parents=True, exist_ok=True)
    generated = group_dir / f".{config.group_id}.generated.conf"
    temporary = generated.with_suffix(generated.suffix + ".tmp")
    temporary.write_text(config.to_legacy_shell(), encoding="utf-8")
    os.chmod(temporary, 0o600)
    os.replace(temporary, generated)
    return generated


def main() -> int:
    args = _parser().parse_args()
    config_dir = args.config_dir.expanduser().resolve()

    if args.group_or_list.lower() == "list":
        if args.action is not None:
            _parser().error("list does not accept an action")
        return _exec_shell(["--config-dir", str(config_dir), "list"])

    group_id = args.group_or_list
    if args.action is None:
        _parser().error("a group action is required")

    yaml_path = _yaml_path(config_dir, group_id)
    legacy_path = config_dir / group_id / f"{group_id}.conf"

    if yaml_path.is_file():
        try:
            config = load_group_config(yaml_path, expected_group_id=group_id)
        except ConfigError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1

        print(f"Configuration valid: {yaml_path}")
        print(f"Enabled channels: {len(config.enabled_channels)}")
        if args.action == "validate":
            for offset, channel in enumerate(config.enabled_channels):
                print(
                    f"  {channel.id}: {channel.frequency_hz} Hz {channel.mode} "
                    f"SSRC={config.base_ssrc + offset} PORT={config.base_port + offset}"
                )
            return 0

        generated = _write_generated_config(config_dir, config)
        environment = os.environ.copy()
        environment["VFO_GROUP_CONFIG_FILE"] = str(generated)
        return _exec_shell(
            ["--config-dir", str(config_dir), group_id, args.action],
            environment=environment,
        )

    if args.action == "validate":
        if legacy_path.is_file():
            print(f"Legacy shell profile found: {legacy_path}")
            print("Validation is performed by the legacy controller during start/status.")
            return 0
        print(f"ERROR: no YAML or legacy profile found for group {group_id!r}", file=sys.stderr)
        return 1

    return _exec_shell(["--config-dir", str(config_dir), group_id, args.action])


def _exec_shell(arguments: list[str], *, environment: dict[str, str] | None = None) -> int:
    script = Path(__file__).resolve().parent / "resources" / "virtual_vfo_streamer.sh"
    if not script.is_file():
        print(f"ERROR: bundled group controller not found: {script}", file=sys.stderr)
        return 1
    os.execve(
        "/usr/bin/env",
        ["env", "bash", str(script), *arguments],
        environment or os.environ.copy(),
    )
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
