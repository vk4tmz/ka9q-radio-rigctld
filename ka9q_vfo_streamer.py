
import argparse
import logging
import os
import psutil
import pyaudio
import signal
import subprocess
import sys
import time

from hamlibserver import HamlibServer, DEFAULT_HAMLIB_HOST, DEFAULT_HAMLIB_PORT
from control import KA9Q_PRESETS
from status import StatusType

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

    log: logging.Logger

    mcast_group: str
    ssrc: int
    rtp_mcast_group_ip: str
    
    hls: HamlibServer

    audio_device: int
    audio_rate: int
    audioProcess: subprocess.Popen

    def __init__(self, mcast_group:str, ssrc: int, freq_hz:int, mode:str, 
                 audio_device:int, audio_rate:int, 
                 host:str=DEFAULT_HAMLIB_HOST, port:int=DEFAULT_HAMLIB_PORT) -> None:
        
        self.log = logging.getLogger("%s.%s" % (__name__, self.__class__.__name__))        

        self.mcast_group = mcast_group
        self.ssrc = ssrc
        self.audio_device = audio_device
        self.audio_rate = audio_rate

        #1. Start the HamlibServer, this will sset the initial Frequency, Mode for the specifed SSRC to ensure it exists before trying to start Audio Stream
        self.hls = HamlibServer(mcast_group=args.mcast_group, ssrc=args.ssrc, freq_hz=freq_hz, mode=mode, host=args.host, port=args.port)
        self.hls.start()

        # Register our handlers
        self.registerSignalHandlers()

        self.log.info("Waiting for VFO Status information...")
        while (len(self.hls.ka9q_rs.status) < 1):
            time.sleep(0.1)

        #2. Start the Audio Streaming form the RTP to select AudioDevice and sample rate
        sockinfo =  self.hls.getRtpMcastSocket()
        if (sockinfo):
            # self.rtp_mcast_group_ip = '239.206.102.211'
            self.rtp_mcast_group_ip = sockinfo['addr']
            self.log.info(f"SSRC: [{ssrc}]  RTP Multicast Address: [{self.rtp_mcast_group_ip}].")
            self.startAudioStream()
        else:
            self.log.error("Unable to determine audio streams RTP Address information.")
            sys.exit(-1)


        print("Main thread joining HLS and waiting!!!!!!!")
        self.hls.serverHandlerThread.join()

    def startAudioStream(self):

        # Example: Running a simple Python script in the background
        # Ensure 'background_script.py' exists with some print statements
        # pcmrecord -c -r -S 9999991 hf-pcm.local | sox -t raw -c 1 -r 12000 -b 16 -e sign - -t pulseaudio virtual_card_01
        # ./pcmrecord_to_virtualcard.sh 'hf-pcm.local' 9999991 12000 virtual_card_01
        # command = ["./pcmrecord_to_virtualcard.sh", self.rtp_mcast_group_ip, str(self.ssrc), str(self.audio_rate), "virtual_card_01"]
        # command = ["./pcmrecord_to_virtualcard.sh", 'hf-pcm.local', str(self.ssrc), str(self.audio_rate), "virtual_card_01"]
        command = ["./pcmrecord_to_virtualcard.sh", '239.206.102.211', str(self.ssrc), str(self.audio_rate), "virtual_card_01"]

        # Detach the process from the current terminal (Unix-like systems)
        # This creates a new session and process group for the child process.
        self.audioProcess = subprocess.Popen(command, preexec_fn=os.setsid)
        # self.audioProcess = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, preexec_fn=os.setsid)

        print(f"Background process started with PID: {self.audioProcess.pid}")
        # The main script can continue its work without waiting for the background process

    def stopAudioStream(self):
        self.log.info(f"Sending SIGKILL (signal 9) to audio stream process with PID: {self.audioProcess.pid}")
        # self.audioProcess.kill()
        # Currently running a shell script so need to whole kill process tree
        self.killProcessTree(self.audioProcess.pid)

    def killProcess(self, pid:int):
        try:
            os.kill(pid, 9)  # 9 is the signal number for SIGKILL
            self.log.debug(f"SIGKILL sent to process with PID: {pid}.")
        except ProcessLookupError:
            self.log.error(f"Process with PID {pid} not found.")

    def killProcessTree(self, pid:int, sig:int=9):
        
        try:
            parent = psutil.Process(pid)
        except psutil.NoSuchProcess:
            return

        children = parent.children(recursive=True)
        for child in children:
            try:
                os.kill(child.pid, sig)
            except OSError as e:
                self.log.error(f"Error killing child process {child.pid}: {e}")
        try:
            os.kill(pid, sig)
        except OSError as e:
            self.log.error(f"Error killing parent process {pid}: {e}")

    def registerSignalHandlers(self):
        signal.signal(signal.SIGINT, self.handle_signal)
        signal.signal(signal.SIGTERM, self.handle_signal)
        signal.signal(signal.SIGQUIT, self.handle_signal)

    def handle_signal(self, signum, frame):
        self.log.info(f"Signal: [{signum}] received. Requesting shutdown...")
        self.hls.stop()
        self.stopAudioStream()
        time.sleep(2)

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
                          audio_device=args.audio_device, audio_rate=args.audio_rate,
                          host=args.host, port=args.port)

