# AGENTS.md

## Project purpose

`ka9q-radio-rigctld` exposes one KA9Q-Radio receiver as a small Hamlib-compatible rigctld endpoint, streams its PCM audio to a selected sink, and manages named groups of virtual VFOs.

## Ownership boundaries

- Low-level KA9Q control/status protocol code belongs in the `ka9q-radio` project.
- This repository owns Hamlib behaviour, audio-process lifecycle and grouped VFO orchestration.
- Do not reintroduce local copies of status parsing, multicast socket handling, name resolution or control-packet encoding.
- Active group profiles and runtime state belong under `~/.config/ka9q-radio/vfo_streamer/<group>/`.
- Do not commit real profiles, PIDs, PulseAudio module IDs, runtime logs or secrets.

## Safety and compatibility

- Preserve SSRC values, Hamlib ports, sink naming and shutdown semantics unless explicitly changing them.
- Keep the group controller runnable through the installed `ka9q-vfo-group` command.
- Protocol-level changes require compatible tests in `ka9q-radio` first.
- Treat profile files as shell configuration and document every new required variable.

## Validation

```bash
bash -n scripts/virtual_vfo_streamer.sh
bash -n src/ka9q_radio_rigctld/resources/virtual_vfo_streamer.sh
bash -n src/ka9q_radio_rigctld/resources/pcmrecord_to_virtualcard.sh
python -m compileall -q src tests
python -m pytest
python -m build
```

## Current active examples

- `vara_hf.conf.example`: 7048.600 kHz LSB and 10147.600 kHz USB.
- `vara_hf.conf.example`: experimental/background VARA HF channels.

## VFO group configuration

- YAML is the preferred profile format: `<group>/<group>.yaml`.
- Keep legacy `.conf` support until all deployed profiles have been migrated.
- Validate examples with `ka9q-vfo-group --config-dir runtime-profiles <group> validate`.
- Do not move lifecycle behaviour into the YAML loader; configuration and runtime orchestration remain separate during this phase.

## Shared infrastructure boundary

Generic process identity, advisory locks, atomic JSON state, signals and
readiness probes belong in the sibling `ka9q-common` project. Do not reintroduce
a local `common_process` package here. Radio-, PulseAudio- and VFO-specific
lifecycle behaviour belongs in `ka9q_radio_rigctld`.

Dependency direction is one way: `ka9q-common` may not depend on this project.

The shell group backend remains the compatibility baseline until the Python
backend has completed real start/status/restart/stop and failure-recovery tests.
