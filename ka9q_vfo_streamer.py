
import argparse
import logging
import pyaudio
import sys

from hamlibserver import HamlibServer, DEFAULT_HAMLIB_HOST, DEFAULT_HAMLIB_PORT
from control import KA9Q_PRESETS

# Configure basic logging to a file and the console
logging.basicConfig(
    # level=logging.INFO,  # Set the minimum logging level to INFO
    level=logging.DEBUG,  # Set the minimum logging level to INFO    
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    handlers=[
        logging.FileHandler("ka9q-vfo-streamer.log"),  # Log to a file
        logging.StreamHandler()  # Log to the console (standard output)
    ]
)


APPTitle = "KA9Q Radio VFO Streamer (with Hamlib Server)"

class Ka9qVfoStreamer():

    def __init__(self, mcast_group:str, ssrc: int, freq_hz:int, mode:str, 
                 audio_device:int, audioRate:int, 
                 host:str=DEFAULT_HAMLIB_HOST, port:int=DEFAULT_HAMLIB_PORT) -> None:
        
        #1. Start the HamlibServer, this will sset the initial Frequency, Mode for the specifed SSRC to ensure it exists before trying to start Audio Stream
        hls = HamlibServer(mcast_group=args.mcast_group, ssrc=args.ssrc, freq_hz=freq_hz, mode=mode, host=args.host, port=args.port)
        hls.start()

        #2. Start the Audio Streaming form the RTP to select AudioDevice and sample rate
        # pcmrecord -c -r -S 9999991 hf-pcm.local | sox -t raw -c 1 -r 12000 -b 16 -e sign - -t pulseaudio virtual_card_01
        # TODO

        print("Main thread joining HLS and waiting!!!!!!!")
        hls.serverHandlerThread.join()



# ================ Main routine ================================================

def processArgs(parser):

    parser = argparse.ArgumentParser(description=APPTitle)
    parser.add_argument("mcast_group", type=str, default='hf.local', help="Multicast group name/ip for VFO control.")
    parser.add_argument("ssrc", type=int, default=9999991, help="SSRC is to create / reuse for VFO control.")
    parser.add_argument("freq_hz", type=int, default=70740000, help="Initial frequency (Hz) which vfo will be set to.")
    parser.add_argument("mode", type=str, default='usb', choices=KA9Q_PRESETS, help="Initial mode which vfo will be set to.")
    parser.add_argument("audio_device", type=int, help="Alsa device number to stream vfo RTP to. Will display list of available auido devices if value not provided and/or not a valid device number.")
    parser.add_argument("-ar", "--audio-rate", type=int, default=12000, choices=[11025, 12000, 22050, 44100, 48000], help="Audio sampling rate.")
    parser.add_argument("--host", type=str, default=DEFAULT_HAMLIB_HOST, help="Host name/ip to bind Hamlib Rigctld to.")
    parser.add_argument("--port", type=int, default=DEFAULT_HAMLIB_PORT, help="Port to bind use for Hamlib Rigctld.")
    
    args = parser.parse_args()

    return args        


if __name__ == "__main__":
    # python ka9q_vfo_streamer.py hf.local 9999991 7078000 usb 1000 -ar 12000 --host localhost --port 4575
    parser = argparse.ArgumentParser(description=APPTitle)
    args = processArgs(parser)

    vfo = Ka9qVfoStreamer(mcast_group=args.mcast_group, ssrc=args.ssrc, freq_hz=args.freq_hz, mode=args.mode,
                          audio_device=args.audio_device, audioRate=args.audio_rate,
                          host=args.host, port=args.port)

