# AGENTS.md

## Project purpose

`ka9q-radio-rigctld` exposes a KA9Q-Radio channel as a small Hamlib-compatible rigctld endpoint and streams its audio to a selected audio device. The repository also owns the grouped virtual-VFO controller in `scripts/virtual_vfo_streamer.sh`.

## Runtime boundaries

- Implementation and example profiles belong in this repository.
- Active group profiles and runtime state belong under `~/.config/ka9q-radio/vfo_streamer/<group>/`.
- Do not commit real machine-specific profiles, PIDs, module IDs, runtime logs, or secrets.
- The group controller must derive repository paths from its own location; do not add absolute user-home checkout paths.

## Safety and compatibility

- Preserve existing SSRC, Hamlib port, sink naming, and shutdown semantics unless a change is explicitly requested.
- Validate shell changes with `bash -n scripts/virtual_vfo_streamer.sh`.
- Validate the active Python files with `python -m py_compile ka9q_vfo_streamer.py hamlibserver.py control.py listener.py resolver.py status.py` and run the test suite. `multicast.py` is currently unfinished and is not part of the runtime.
- Treat profile files as shell configuration and document any new required variables.

## Current active examples

- `hf_aprs.conf.example`: 7048.600 kHz LSB and 10147.600 kHz USB.
- `vara_hf.conf.example`: four VARA HF channels.
