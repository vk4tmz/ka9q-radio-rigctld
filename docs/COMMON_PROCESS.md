# common_process

`common_process` is a small Linux process-supervision package currently hosted
inside `ka9q-radio-rigctld` while its API is proven in production.

## Included primitives

- `FileLock`: non-blocking advisory file locks using `flock(2)`.
- `atomic_write_json` / `read_json`: durable JSON state replacement.
- `ProcessSpec`: immutable launch configuration.
- `ManagedProcess`: start, inspect and safely stop a process group.
- `ProcessIdentity`: PID, `/proc` start ticks, command line and process group.
- `wait_for_tcp`: generic TCP readiness polling.

## Safety properties

A PID alone is never treated as sufficient process identity. Runtime state also
records Linux process start ticks and the observed command line. This prevents
stale state from signalling a different process after PID reuse.

Managed children start in their own process group. Shutdown sends `SIGTERM` to
the group, waits for a bounded period, then escalates to `SIGKILL` if required.

## Extraction rule

Do not extract this package solely because it looks reusable. Extract it only
after at least one additional project uses the API without adding radio-,
audio- or decoder-specific concepts.
