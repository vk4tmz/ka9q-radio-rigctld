#!/usr/bin/bash

MCAST_GROUP=$1
SSRC=$2
AUDIO_RATE=$3
AUDIO_DEVICE=$4

#pcmrecord -c -r -S 9999991 hf-pcm.local | sox -t raw -c 1 -r 12000 -b 16 -e sign - -t pulseaudio virtual_card_01
pcmrecord -c -r -S ${SSRC} ${MCAST_GROUP} | sox -t raw -c 1 -r ${AUDIO_RATE} -b 16 -e sign - -t pulseaudio ${AUDIO_DEVICE}
