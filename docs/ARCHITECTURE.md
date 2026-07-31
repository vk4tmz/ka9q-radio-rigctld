# Architecture

## Responsibilities

`ka9q-radio-rigctld` provides the application layer around a single KA9Q-Radio receiver:

- a small Hamlib-compatible `rigctld` TCP endpoint;
- one RTP/PCM audio stream into a selected PulseAudio/PipeWire sink;
- grouped VFO lifecycle management through `ka9q-vfo-group`.

The low-level KA9Q multicast protocol is owned by the separate `ka9q-radio` package. This project imports its:

- `Ka9qRadioClient` for control updates;
- `ReceiverConfig` for receiver validation;
- `StatusListener` for multicast status reception;
- `StatusType` and `KA9Q_PRESETS` protocol definitions.

This repository no longer maintains its own control encoder, status parser, resolver, discovery client, or multicast implementation.

## Single VFO runtime

`ka9q-vfo-streamer` performs the following sequence:

1. Start `HamlibServer` for one SSRC.
2. Create or retune that receiver through `ka9q-radio`.
3. Collect status for the same SSRC in a background listener.
4. Read the receiver's RTP multicast destination from status.
5. Launch the packaged `pcmrecord_to_virtualcard.sh` helper.
6. Stream decoded PCM into the selected audio sink.

The Hamlib server supports the small subset needed by applications such as JS8Call, WSJT-X and FLDigi: frequency, mode, VFO, PTT state, power state and lock-mode queries.

## KA9Q integration adapter

`src/ka9q_radio_rigctld/radio.py` is intentionally small. `RadioSession` adapts the reusable `ka9q-radio` request/response API to this application's long-running needs:

- maintain the latest status for one SSRC;
- apply frequency/preset changes;
- wait for initial receiver status;
- stop the listener thread cleanly.

Protocol changes belong in `ka9q-radio`; Hamlib and audio lifecycle changes belong here.

## Group orchestration

`ka9q-vfo-group` invokes the packaged group controller, which manages a named group of VFOs:

1. Load `~/.config/ka9q-radio/vfo_streamer/<group>/<group>.conf`.
2. Create one PulseAudio/PipeWire null sink per configured channel.
3. Start one installed `ka9q-vfo-streamer` process per channel.
4. Record process IDs and PulseAudio module IDs beside the active profile.
5. Stop only recognized VFO processes and unload the recorded sinks.

## Configuration boundary

Repository examples live in `examples/vfo-streamer/`. Active profiles and runtime state remain external:

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

## Configuration transition

The installed `ka9q-vfo-group` command owns the configuration contract. It
loads and validates YAML profiles, filters disabled channels, allocates SSRC and
rigctld ports deterministically, and translates the validated model into a
private compatibility profile for the existing shell lifecycle controller.

This intentionally separates configuration migration from lifecycle rewriting.
A later phase can replace the shell controller without changing the YAML schema.

## Process supervision boundary

The opt-in Python group backend separates generic process supervision from
radio-specific orchestration:

```text
ka9q-vfo-group
    |
    +-- YAML/profile and PulseAudio orchestration (ka9q_radio_rigctld)
    |
    +-- locking, process state and safe shutdown (common_process)
```

`common_process` contains no KA9Q, PulseAudio, APRS or HFDL concepts. The
package is intentionally kept inside this repository while its API is tested
against the VFO lifecycle. A later extraction should happen only after another
independent project adopts the same primitives without radio-specific changes.

The Python backend writes one group state document plus one identity document
per child process under:

```text
~/.local/state/ka9q-radio/vfo_streamer/<group>/
```

A process identity includes the PID, Linux `/proc` start-time ticks and the
observed command line. This prevents a stale state file from terminating an
unrelated process after PID reuse.
