
import argparse
import logging
import os
import pyaudio
import signal
import subprocess
import sys
import time

from hamlibserver import HamlibServer, DEFAULT_HAMLIB_HOST, DEFAULT_HAMLIB_PORT
from control import KA9Q_PRESETS

# Configure basic logging to a file and the console
logging.basicConfig(
    level=logging.INFO,  # Set the minimum logging level to INFO
    # level=logging.DEBUG,  # Set the minimum logging level to INFO    
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

    audio_device: str
    audio_rate: int
    audioProcess: subprocess.Popen | None

    def __init__(self, mcast_group:str, ssrc: int, freq_hz:int, mode:str, 
                 audio_device:str, audio_rate:int, 
                 host:str=DEFAULT_HAMLIB_HOST, port:int=DEFAULT_HAMLIB_PORT) -> None:
        
        self.log = logging.getLogger("%s.%s" % (__name__, self.__class__.__name__))        

        self.mcast_group = mcast_group
        self.ssrc = ssrc
        self.audio_device = audio_device
        self.audio_rate = audio_rate
        self.audioProcess = None

        #1. Start the HamlibServer, this will sset the initial Frequency, Mode for the specifed SSRC to ensure it exists before trying to start Audio Stream
        self.hls = HamlibServer(mcast_group=args.mcast_group, ssrc=args.ssrc, freq_hz=freq_hz, mode=mode, host=args.host, port=args.port)

        # Register our handlers
        self.registerSignalHandlers()

        self.hls.start()

        # allow a bit of time for thread to start
        time.sleep(0.250)
        if (not self.hls.serverHandlerRunning):
            raise Exception("Hamlib Server Failed to start.")

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


        self.log.info("Ready....")
        while self.hls.serverHandlerThread.is_alive():
            time.sleep(0.5)

    def startAudioStream(self):

        # command = ["./pcmrecord_to_virtualcard.sh", 'hf-pcm.local', str(self.ssrc), str(self.audio_rate), "virtual_card_01"]
        # command = ["./pcmrecord_to_virtualcard.sh", '239.206.102.211', str(self.ssrc), str(self.audio_rate), "virtual_card_01"]
        command = ["./pcmrecord_to_virtualcard.sh", self.rtp_mcast_group_ip, str(self.ssrc), str(self.audio_rate), self.audio_device]

        self.audioProcess = subprocess.Popen(command, start_new_session=True)
        # self.audioProcess = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, preexec_fn=os.setsid)

        self.log.info(f"Audio streaming process started with PID: {self.audioProcess.pid}")
        

    def stopAudioStream(self):
        if self.audioProcess is None:
            self.log.info("No audio process to stop.")
            return

        if self.audioProcess.poll() is not None:
            self.log.info("Audio process already stopped.")
            self.audioProcess = None
            return

        pid = self.audioProcess.pid

        try:
            pgid = os.getpgid(pid)

            self.log.info(
                f"Sending SIGTERM to audio process group {pgid}"
            )

            os.killpg(
                pgid,
                signal.SIGTERM
            )

            time.sleep(2)

            if self.audioProcess.poll() is None:
                self.log.warning(
                    "Audio process group still running, sending SIGKILL."
                )

                os.killpg(
                    pgid,
                    signal.SIGKILL
                )

        except ProcessLookupError:
            self.log.info(
                "Audio process group already terminated."
            )

        except OSError as e:
            self.log.error(
                f"Error stopping audio process group: {e}"
            )

        finally:
            self.audioProcess = None


    def registerSignalHandlers(self):
        signal.signal(signal.SIGINT, self.handle_signal)
        signal.signal(signal.SIGTERM, self.handle_signal)
        signal.signal(signal.SIGQUIT, self.handle_signal)

    def handle_signal(self, signum, frame):
        self.log.info(
            f"Signal: [{signum}] received. Requesting shutdown..."
        )

        try:
            self.stopAudioStream()
        except Exception as e:
            self.log.error(
                f"Error stopping audio stream: {e}"
            )

        try:
            self.hls.stop()
        except Exception as e:
            self.log.error(
                f"Error stopping Hamlib server: {e}"
            )

        self.log.info("Shutdown complete.")

        os._exit(0)

# ================ Main routine ================================================

def listAudioDevices():
    PA = pyaudio.PyAudio()
    try:
        ndev = PA.get_device_count()

        n = 0
        ai = ""
        ao = ""
        while n < ndev:
            s = PA.get_device_info_by_index(n)
            # print n, s
            if int(s['maxInputChannels']) > 0:
                ai += f"{s['index']}: [{s['name']}]\n"
            if int(s['maxOutputChannels']) > 0:
                ao += f"{s['index']}: [{s['name']}]\nALL:[{s}]\n"
            n = n + 1

        print(f"Located {n} audio output devices:\n{ao}")
    finally:
        PA.terminate()

def processArgs(parser):

    parser = argparse.ArgumentParser(description=APPTitle)
    parser.add_argument("mcast_group", type=str, nargs='?', default='hf.local', help="Multicast group name/ip for VFO control.")
    parser.add_argument("ssrc", type=int, nargs='?', default=9999991, help="SSRC is to create / reuse for VFO control.")
    parser.add_argument("freq_hz", type=int, nargs='?', default=70740000, help="Initial frequency (Hz) which vfo will be set to.")
    parser.add_argument("mode", type=str, nargs='?', default='usb', choices=KA9Q_PRESETS, help="Initial mode which vfo will be set to.")
    parser.add_argument("-L", "--list_audio_devices", action='store_true', help="List available audio devices.")
    parser.add_argument("-ad", "--audio_device", type=str, help="Audio device name to stream vfo RTP to. ")
    parser.add_argument("-ar", "--audio-rate", type=int, default=12000, choices=[11025, 12000, 22050, 44100, 48000], help="Audio sampling rate.")
    parser.add_argument("--host", type=str, default=DEFAULT_HAMLIB_HOST, help="Host name/ip to bind Hamlib Rigctld to.")
    parser.add_argument("--port", type=int, default=DEFAULT_HAMLIB_PORT, help="Port to bind use for Hamlib Rigctld.")
    
    args = parser.parse_args()

    return args        


if __name__ == "__main__":
    # python ka9q_vfo_streamer.py hf.local 9999991 7078000 usb 1000 -ar 12000 --host localhost --port 4575
    parser = argparse.ArgumentParser(description=APPTitle)
    args = processArgs(parser)

    if (args.list_audio_devices):
        listAudioDevices()
    else:
        vfo = Ka9qVfoStreamer(mcast_group=args.mcast_group, ssrc=args.ssrc, freq_hz=args.freq_hz, mode=args.mode,
                            audio_device=args.audio_device, audio_rate=args.audio_rate,
                            host=args.host, port=args.port)

