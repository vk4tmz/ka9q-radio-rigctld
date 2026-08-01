# Streaming Audio and Controlling KA9Q-Radio Channel Source as if it was its own Radio / VFO

## Overview

The purpose of this little project was to provide a minimally implemented 'Hamlib Rigctld' server to allow applications such as [WSJTX](https://wsjt.sourceforge.io/wsjtx.html), [JS8Call](https://github.com/js8call/js8call), [FLDigi](https://www.w1hkj.org/) etc to control a single KA9Q-Radio "**Channel**" / "**SSRC**". The script also will start a background "[pcmrecord](https://github.com/ka9q/ka9q-radio/blob/main/docs/utils/pcmrecord.md)" thread to stream the audio to the specified audio output device or in my case sink (ie Virtual Audio Card) to be used by the foremention digital mode decoding applications.

The minimally implemented Rigctrld implements the following:
  - dump_state
  - Get/Set Frequency
  - Get/Set Mode
  - Get/Set VFO - (But only one VFO tracked)
  - Few other required (get_lock_mode, chk_vfo, get_powerstat)

### Creating Virtual Audio Card / Sink

The following instructions utilise pulse-audio and its utilities to create virtual audio card / sinks. 

#### Pulse Audio Dependencies:

```
sudo apt update && sudo upgrade
sudo apt install pulseaudio pulseaudio-utils
```

#### Creating the sinks:

```
pactl load-module module-null-sink sink_name=virtual_card_01 sink_properties=device.description="Virtual-Card-1"
pactl list short sinks
```
Note: These newly created sinks are only temp and will not persist during reboot / shutdown. You need to research this yourself.

#### Removing Sink

When you ran the load module command above you would have been present with a module number of the newly created module / sink.  You can find this by running the list module command.

```
pactl list modules 
pactl unload-module NNNNNNNN
```

### Streaming audio from KA9Q-Radio to Audio Card

While my project will spin a thread up to handle this, it's good to explain how to do it manually and some consideration.

**NOTE** - if you're simply after a way to just simple listen to KA9Q-Radio channels / sources you can simply use the provide command line text based UI utility '[monitor](https://github.com/ka9q/ka9q-radio/blob/main/docs/utils/monitor.md)'

The following example is 40m FT8, which KA9Q-Radio has automatically assigned a SSRC ID of 7074. Depending on your channel settings you will need to alter the audio sample rate for the KA9Q-Radio stream.  In this example its 12 Khz, single channel and format of S16_LE.

To listen to your stream using default system audio you can utilise '[aplay](https://linux.die.net/man/1/aplay)':

```
pcmrecord -c -r -S 7074 ft8-pcm.local | aplay -f S16_LE -r 12000 -c 1
```

To stream this audio to a the newly created pulse virutal audio sink we utilise linux audio utility '[sox](https://linux.die.net/man/1/sox)' to convert from one format to another.  In our case from 12khz S16_LE to pulseaudio:

```
pcmrecord -c -r -S 7074 ft8-pcm.local | sox -t raw  -r 12000 -c 1 -b 16 -e signed -L - -t pulseaudio virtual_card_01
```

With this running you can now spin up your application of choice (eg WSTJX, JS8Call Fldigi etc) and select the appropriate audio device. 

**FLDigi Notes**: 
  - For Fldigi, you'll need to set the desired virtual audio card as the 'system default'. Unlike the other applications where we can select the specific audio card, FLDigi when selecting 'pulse-audio' doesn't seem to give you that choice.
  - You will need to alter the 'signal range (dB)' value from default 60 to around 77 to start seeing blueish waterfall. Until you do this you waterfall will appear black and you'll think its not working.

### Creating / Controlling KA9Q-Radio Channel / Source

You can predefine your channels / sources via the KA9Q-Radio configuration. When the application starts these channel sources will be available via their either manually or automatically assigned SSRC id.

You can utilise the KA9Q-Radio '[control](https://github.com/ka9q/ka9q-radio/blob/main/docs/utils/control.md)' command line text base UI utility to create and alter the channel / source settings  (ie frequency, mode, filters, audio output sample rate etc)

## Installation and commands

Install both projects into the shared virtual environment:

```bash
source ~/tools/ka9q-radio/.venv/bin/activate
python -m pip install -e ~/tools/ka9q-radio
python -m pip install -e ~/tools/ka9q-radio-rigctld
```

Installed commands:

```text
ka9q-vfo-streamer   Start one receiver, audio stream and Hamlib endpoint
ka9q-rigctld        Start the Hamlib-compatible endpoint only
ka9q-vfo-group      Manage configured groups of virtual VFOs
```

Examples:

```bash
ka9q-vfo-group hf_aprs start
ka9q-vfo-group hf_aprs status

ka9q-vfo-streamer \
  hf.local 9999991 7074000 usb \
  -ar 12000 -ad virtual_card_01 --port 4575
```

## Shared KA9Q protocol package

This application uses the separate `ka9q-radio` package for multicast control and status handling. It no longer carries local copies of the control encoder, status parser, resolver, discovery code or multicast implementation.

`ka9q-radio-rigctld` remains responsible for:

- the Hamlib TCP protocol adapter;
- long-running single-SSRC state;
- RTP-to-audio process lifecycle;
- PulseAudio/PipeWire sink orchestration;
- grouped VFO start, stop and status operations.

## Group profiles

Active profiles live outside Git under:

```text
~/.config/ka9q-radio/vfo_streamer/<GROUP_ID>/<GROUP_ID>.conf
```

Examples are provided in `examples/vfo-streamer/`. See `docs/ARCHITECTURE.md` and `docs/OPERATIONS.md` for the current design and commands.

## Optional audio-device listing dependency

The streaming runtime uses the packaged `pcmrecord`/SoX helper and does not require PyAudio. To enable `ka9q-vfo-streamer --list-audio-devices`, install the optional extra:

```bash
python -m pip install -e '~/tools/ka9q-radio-rigctld[audio-tools]'
```

## Validated YAML profiles

YAML is the preferred VFO group format:

```bash
ka9q-vfo-group hf_aprs validate
ka9q-vfo-group hf_aprs start
```

Examples are provided under `examples/vfo-streamer/`, and ready-to-copy active
profiles are under `runtime-profiles/`. Legacy `.conf` profiles remain supported
when no YAML profile exists.

## Experimental Python lifecycle backend

Version 0.5.0 adds an opt-in Python implementation of the VFO group lifecycle.
The existing shell controller remains the default while the new implementation
is exercised on real workloads.

```bash
ka9q-vfo-group --backend python hf_aprs start
ka9q-vfo-group --backend python hf_aprs status
ka9q-vfo-group --backend python hf_aprs stop
```

The backend may also be selected for a shell or tmux session:

```bash
export KA9Q_VFO_GROUP_BACKEND=python
```

The Python backend stores operational state under:

```text
~/.local/state/ka9q-radio/vfo_streamer/<group>/
```

Before the first Python-backend start, stop any group managed by the legacy
shell backend. The two backends intentionally do not trust or reuse each
other's PID/state files.

### Local reusable process package

The repository now contains `common_process`, a deliberately narrow package
providing advisory locks, atomic JSON state, process identity verification,
safe process-group shutdown and TCP readiness checks. It remains local to this
repository until its API has been proven by multiple real consumers.
