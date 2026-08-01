# Operations

## Install

Both `ka9q-radio` and this project are installed into the shared environment:

```bash
source ~/tools/ka9q-radio/.venv/bin/activate

python -m pip install -e ~/tools/ka9q-radio
python -m pip install -e ~/tools/ka9q-radio-rigctld
```

Verify the installed commands:

```bash
command -v ka9q-radio
command -v ka9q-vfo-streamer
command -v ka9q-rigctld
command -v ka9q-vfo-group
```

## Install an example profile

```bash
mkdir -p ~/.config/ka9q-radio/vfo_streamer/hf_aprs
cp examples/vfo-streamer/hf_aprs.yaml.example \
  ~/.config/ka9q-radio/vfo_streamer/hf_aprs/hf_aprs.yaml
```

For VARA HF:

```bash
mkdir -p ~/.config/ka9q-radio/vfo_streamer/vara_hf
cp examples/vfo-streamer/vara_hf.yaml.example \
  ~/.config/ka9q-radio/vfo_streamer/vara_hf/vara_hf.yaml
```

## Group commands

Run from any directory after activating the environment:

```bash
ka9q-vfo-group list
ka9q-vfo-group hf_aprs start
ka9q-vfo-group hf_aprs status
ka9q-vfo-group hf_aprs restart
ka9q-vfo-group hf_aprs stop
```

Use a different profile root when required:

```bash
ka9q-vfo-group --config-dir /path/to/profiles hf_aprs status
```

The direct script remains available for source-tree debugging only:

```bash
scripts/virtual_vfo_streamer.sh hf_aprs status  # compatibility fallback; prefer ka9q-vfo-group
```

New tmux launchers and automation should call `ka9q-vfo-group`.

## Single VFO

```bash
ka9q-vfo-streamer \
  hf.local \
  9999991 \
  7074000 \
  usb \
  -ar 12000 \
  -ad virtual_card_01 \
  --host localhost \
  --port 4575
```

Run only the Hamlib-compatible endpoint with:

```bash
ka9q-rigctld hf.local 9999991 7074000 usb --port 4575
```

## Runtime checks

Inspect the VFO group:

```bash
ka9q-vfo-group hf_aprs status
```

Inspect virtual sinks and monitor sources:

```bash
pactl list sinks short | grep 'vc_hf_aprs_'
pactl list sources short | grep 'vc_hf_aprs_'
```

Inspect running processes:

```bash
pgrep -af 'ka9q-vfo-streamer|ka9q-rigctld|pcmrecord'
```

Check a configured receiver directly through the shared protocol package:

```bash
ka9q-radio status \
  --radio hf.local \
  --ssrc 9999991 \
  --seconds 3
```

For receiver output groups that publish status on a destination multicast group, supply that group and the correct interface instead.

## Validation before committing

```bash
bash -n scripts/virtual_vfo_streamer.sh
bash -n src/ka9q_radio_rigctld/resources/virtual_vfo_streamer.sh
bash -n src/ka9q_radio_rigctld/resources/pcmrecord_to_virtualcard.sh

python -m compileall -q src tests
python -m pytest
python -m build
```

The old local protocol files (`control.py`, `listener.py`, `status.py`, `resolver.py`, `discover.py` and the unfinished `multicast.py`) were removed in version 0.3.0. Their functionality is provided by `ka9q-radio`.

## YAML group profiles

YAML is now the preferred group configuration format. Profiles are stored at:

```text
~/.config/ka9q-radio/vfo_streamer/<group>/<group>.yaml
```

Validate before starting:

```bash
ka9q-vfo-group hf_aprs validate
ka9q-vfo-group vara_hf validate
```

The controller prefers `.yaml`, then `.yml`, and falls back to the legacy
`<group>.conf` only when no YAML profile exists. The current shell lifecycle
controller remains in place during this transition; the Python CLI validates
YAML and creates a private generated compatibility file in the group directory.

Install the supplied profiles:

```bash
mkdir -p ~/.config/ka9q-radio/vfo_streamer/hf_aprs
mkdir -p ~/.config/ka9q-radio/vfo_streamer/vara_hf

cp runtime-profiles/hf_aprs/hf_aprs.yaml \
  ~/.config/ka9q-radio/vfo_streamer/hf_aprs/hf_aprs.yaml

cp runtime-profiles/vara_hf/vara_hf.yaml \
  ~/.config/ka9q-radio/vfo_streamer/vara_hf/vara_hf.yaml
```

Keep the previous `.conf` files until each YAML profile has passed `validate`,
`start`, `status`, `restart`, and `stop`. YAML takes precedence automatically.

## Trialling the Python lifecycle backend

The shell backend remains the default in version 0.5.0. Perform the first trial
from a clean shell-managed state:

```bash
ka9q-vfo-group hf_aprs stop
ka9q-vfo-group --backend python hf_aprs start
ka9q-vfo-group --backend python hf_aprs status
```

Expected status columns include the process, sink, rigctld port and aggregate
state. Possible states are `RUNNING`, `DEGRADED`, `STOPPED`, `STALE` and
`DISABLED`.

Stop the Python-managed group with the same backend:

```bash
ka9q-vfo-group --backend python hf_aprs stop
```

To make the Python backend active for a tmux session:

```bash
export KA9Q_VFO_GROUP_BACKEND=python
ka9q-vfo-group hf_aprs start
```

Runtime state and logs are stored under:

```text
~/.local/state/ka9q-radio/vfo_streamer/hf_aprs/
```

During the migration period, do not start the same group concurrently with the
shell and Python backends. They use separate state formats by design.


## Backend policy

Production tmux launchers currently select the validated Python backend explicitly with `--backend python`. The shell backend remains available only as a temporary rollback path during the consolidation period.
