# Architecture

## Single VFO runtime

`ka9q_vfo_streamer.py` creates or reuses one KA9Q-Radio SSRC, starts the audio stream, and exposes a minimal Hamlib-compatible TCP endpoint.

## Group orchestration

`scripts/virtual_vfo_streamer.sh` manages a named group of VFOs:

1. Load `~/.config/ka9q-radio/vfo_streamer/<group>/<group>.conf`.
2. Create one PulseAudio/PipeWire null sink per configured channel.
3. Start one `ka9q_vfo_streamer.py` process per channel.
4. Record process IDs and PulseAudio module IDs beside the active profile.
5. Stop only processes identified as KA9Q VFO streamers and unload the recorded sinks.

The controller is part of this repository because it depends directly on the Python streamer's command-line interface, process identity, SSRC allocation, Hamlib port allocation, and audio-device behaviour.

## Configuration boundary

Repository examples live in `examples/vfo-streamer/`. Active profiles and runtime state are external:

```text
~/.config/ka9q-radio/vfo_streamer/
├── hf_aprs/
│   ├── hf_aprs.conf
│   ├── logs/
│   ├── vfo_pids.txt
│   └── virtual_card_module_ids
└── vara_hf/
    └── vara_hf.conf
```
