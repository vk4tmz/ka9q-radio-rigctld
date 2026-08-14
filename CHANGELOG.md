## Unreleased

- Hardened VFO audio lifecycle: `ka9q-vfo-streamer` now restarts a failed audio helper with bounded backoff, and shell `ka9q-vfo-group status` reports `DEGRADED` when the helper is dead or missing instead of trusting only the parent PID.

# Changelog

## 0.5.1 - 2026-08-09

- Moved generic `common_process` implementation to the shared `ka9q-common` project.
- Updated the Python VFO lifecycle to consume `ka9q_common.process` and `ka9q_common.io`.
- Reused `ka9q_common.time.utc_timestamp` for group runtime timestamps.
- Removed the embedded `src/common_process` package and documented the new dependency boundary.

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

## 0.5.0 - 2026-08-01

- Added the local `common_process` package for reusable Linux process supervision.
- Added advisory file locks, atomic JSON state, PID/start-time identity checks,
  safe process-group termination, and TCP readiness helpers.
- Added an opt-in Python VFO group lifecycle backend.
- Added structured group runtime state under `~/.local/state/ka9q-radio/vfo_streamer`.
- Added richer RUNNING, DEGRADED, STOPPED, STALE and DISABLED status reporting.
- Kept the existing shell backend as the default during migration.
