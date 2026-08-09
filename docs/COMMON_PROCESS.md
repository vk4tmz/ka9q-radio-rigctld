# Shared process infrastructure

The generic process-supervision implementation previously hosted in this
repository as `common_process` has moved to the sibling `ka9q-common` project.

`ka9q-radio-rigctld` now imports:

- `ka9q_common.process.FileLock` / `LockUnavailable` for non-blocking advisory locks.
- `ka9q_common.process.ProcessSpec` / `ManagedProcess` and process identity models.
- `ka9q_common.process.wait_for_tcp` for generic TCP readiness polling.
- `ka9q_common.io.atomic_write_json` / `read_json` for runtime state.

The shared implementation remains deliberately independent of KA9Q,
PulseAudio, APRS, HFDL and project-specific configuration. Radio- and
audio-specific lifecycle behaviour remains in `ka9q_radio_rigctld`.

For editable development checkouts, install `ka9q-common` before this project:

```bash
pip install -e ~/tools/ka9q-common
pip install -e ~/tools/ka9q-radio-rigctld
```
