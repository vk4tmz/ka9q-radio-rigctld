# Operations

## Install an example profile

```bash
mkdir -p ~/.config/ka9q-radio/vfo_streamer/hf_aprs
cp examples/vfo-streamer/hf_aprs.conf.example \
  ~/.config/ka9q-radio/vfo_streamer/hf_aprs/hf_aprs.conf
```

For VARA HF:

```bash
mkdir -p ~/.config/ka9q-radio/vfo_streamer/vara_hf
cp examples/vfo-streamer/vara_hf.conf.example \
  ~/.config/ka9q-radio/vfo_streamer/vara_hf/vara_hf.conf
```

## Commands

Run from any directory:

```bash
~/tools/ka9q-radio-rigctld/scripts/virtual_vfo_streamer.sh list
~/tools/ka9q-radio-rigctld/scripts/virtual_vfo_streamer.sh hf_aprs start
~/tools/ka9q-radio-rigctld/scripts/virtual_vfo_streamer.sh hf_aprs status
~/tools/ka9q-radio-rigctld/scripts/virtual_vfo_streamer.sh hf_aprs stop
```

To use another configuration root:

```bash
scripts/virtual_vfo_streamer.sh --config-dir /path/to/profiles hf_aprs status
```

## Shared virtual environment

The controller uses whichever `python` is active. In the current installation, activate:

```bash
source ~/tools/ka9q-radio/.venv/bin/activate
```

## tmux migration

Replace the old controller directory:

```text
~/tools/ka9q-radio-misc/virtual_vfo_streamer
```

with:

```text
~/tools/ka9q-radio-rigctld/scripts
```

The command remains:

```bash
./virtual_vfo_streamer.sh <group> start
```

## Validation

```bash
bash -n scripts/virtual_vfo_streamer.sh
python -m py_compile ka9q_vfo_streamer.py hamlibserver.py control.py listener.py resolver.py status.py
python -m pytest
```


## Known pre-existing issue

`multicast.py` is an unfinished experimental file and currently contains invalid Python syntax. Phase 1 does not modify or depend on it. It should be removed or repaired during the later Python refactor.
