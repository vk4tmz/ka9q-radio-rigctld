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


## Using ka9q_vfo_streamer

### Environment and Dependencies

```
https://github.com/vk4tmz/ka9q-radio-rigctld.git
cd ka9q-radio-rigctld

python3 -m venv env 
source ./env/bin/activate

pip install zeroconf psutil pyaudio

```

### Usage
```
usage: ka9q_vfo_streamer.py [-h] [-L] [-ad AUDIO_DEVICE] [-ar {11025,12000,22050,44100,48000}] [--host HOST] [--port PORT]
                            [mcast_group] [ssrc] [freq_hz] [{lsb,usb,cwl,cwu,am,sam,dsb,amsq,fm,nfm,wfm,pm,npm,wpm,iq,ame,wspr,spectrum}]

KA9Q Radio VFO Streamer (with Hamlib Server)

positional arguments:
  mcast_group           Multicast group name/ip for VFO control.
  ssrc                  SSRC is to create / reuse for VFO control.
  freq_hz               Initial frequency (Hz) which vfo will be set to.
  {lsb,usb,cwl,cwu,am,sam,dsb,amsq,fm,nfm,wfm,pm,npm,wpm,iq,ame,wspr,spectrum}
                        Initial mode which vfo will be set to.

options:
  -h, --help            show this help message and exit
  -L, --list_audio_devices
                        List available audio devices.
  -ad AUDIO_DEVICE, --audio_device AUDIO_DEVICE
                        Audio device name to stream vfo RTP to.
  -ar {11025,12000,22050,44100,48000}, --audio-rate {11025,12000,22050,44100,48000}
                        Audio sampling rate.
  --host HOST           Host name/ip to bind Hamlib Rigctld to.
  --port PORT           Port to bind use for Hamlib Rigctld.
```

The following is simple example of setting up a Stream and VFO for the intended purpose of using it with WSJT-X:

```
python ka9q_vfo_streamer.py hf.local 9999991 7074000 usb -ar 12000 -ad 'virtual_card_01' --host localhost --port 4575
```

The above options are:
  1. Selected hopefully an unused SSRCID "9999991"
  2. Provided a initial frequecy and mode (7074khz USB)
  3. Configured the audio output sample rate of 12khz
  4. Specified the pulse-audio sink name 'virtual_card_01'
  5. Interface IP/name and port to bind the Hamlib Server to.

Obviously you can spin multiple instance of this command, but please ensure to change at minimum '**SSRCID**' and the '**Hamlib Server Port**'.

### Back ground Audio Stream

I did not want to reimplement the audio streaming / sync handling logic that the existing command line utilised provided with KA9Q-Radio perfect take cares of called '[pcmrecord](https://github.com/ka9q/ka9q-radio/blob/main/docs/utils/pcmrecord.md)'.  But it does mean my script needs to launch this application with appropriate parameters and when application closes ensure this thread and any child process are terminated and cleaned up.

### KA9Q-Radio Multicast

KA9Q-Radio transmits audio and status data packet as well as controls each channel source via multicast protocol.

I've implemented a couple of little helper classes to help out with this that hopefully will help others:
  - **status.py** - Encoding and Decoding of the values recieved via status packets and or sent via control packets.
  - **control.py** - Handles the encoding of command to set the frequency and mode for the specified SSRC ID and Multicast Group Name
  - **resolver.py** - using Zeroconf library will resolve multicase group name to a multicase ip via discover means
  - **discover.py** - using Zeroconf library will monitor multicase packets to build a list of ServiceInfo.

## Final Note

I hope this project helps others out. For me I wanted to monitor WEFAX while utiling FLDigi and was getting annoying having to ensure I manually started the audio stream, and changing the frequency via 'control'. My previous experience with how usefuly Hamlib RigCtl is, it was a no brainer, so here we are.

I can now use FLDigi UI to change the frequency and or even quicker via the Hamlib command line utility called '[rigctl](https://manpages.ubuntu.com/manpages/xenial/man1/rigctl.1.html)'

```
 rigctl -m 2 -r localhost:4575
```

I can frequency and mode change commands such as change to 10Mhz WWV:

```
F 10000000
M AM 3000
```

Well that's all folks! 
