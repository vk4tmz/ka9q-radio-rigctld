# Changelog

## 0.3.0 - 2026-08-01

- Replaced duplicated KA9Q control, status, resolver and listener implementations with the shared `ka9q-radio` package.
- Added `RadioSession`, a narrow long-running adapter for one SSRC.
- Removed legacy `control.py`, `listener.py`, `status.py`, `resolver.py`, `discover.py` and unfinished `multicast.py` files.
- Normalized the shared package's `address` socket field for the existing audio-streaming interface.
- Added a bounded initial-status wait instead of waiting forever.
- Made PyAudio optional and lazy-loaded for `--list-audio-devices` only.
- Removed unused direct `psutil` and `zeroconf` dependencies.
- Updated architecture, operations and repository-agent documentation.
- Removed stale migration paths and committed runtime/build artifacts.

## 0.4.0 - 2026-08-01

- Added validated YAML VFO group profiles.
- Added `ka9q-vfo-group <group> validate`.
- Added enabled/disabled channel support.
- Retained legacy `.conf` fallback during migration.
- Added current HF APRS and VARA HF YAML examples and ready-to-copy runtime profiles.
