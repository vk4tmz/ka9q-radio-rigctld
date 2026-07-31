#!/usr/bin/bash

set -o pipefail

MCAST_GROUP=$1
SSRC=$2
AUDIO_RATE=$3
AUDIO_DEVICE=$4

# Silence the progress meter from sox while leaving stdout/stderr handling to the caller.
pcmrecord -c -r -S "${SSRC}" "${MCAST_GROUP}" | \
sox -q -t raw -c 1 -r "${AUDIO_RATE}" -b 16 -e sign - -t pulseaudio "${AUDIO_DEVICE}"
