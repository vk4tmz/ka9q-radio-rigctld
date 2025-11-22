
import logging
import random
import socket
import struct

from resolver import resolve_name
from status import StatusType, encode_double, encode_eol, encode_int, encode_str


DEFAULT_MCAST_PORT=5004
DEFAULT_RTP_PORT=5004
DEFAULT_RTCP_PORT=5005
DEFAULT_STAT_PORT=5006

DEFAULT_MCAST_GROUP = 'hf.local'

KA9Q_PRESETS = ['lsb', 'usb', 'cwl', 'cwu', 
                'am', 'sam', 'dsb', 'amsq', 
                'fm', 'nfm', 'wfm', 'pm', 'npm', 'wpm', 
                'iq', 'ame', 'wspr', 'spectrum']

class Ka9qRadioControl():

    log: logging.Logger

    mcast_group: str
    mcast_group_ip: str

    s_out: socket.socket    # Outbound mcast Socket

    def __init__(self, mcast_group:str=DEFAULT_MCAST_GROUP):
        self.log = logging.getLogger("%s.%s" % (__name__, self.__class__.__name__))

        self.mcast_group = mcast_group

        names = resolve_name(mcast_group)
        if names and len(names) > 0:
            self.mcast_group_ip = names[0].compressed
        else:
            raise Exception(f"Failed to resolve multicast group name: [{mcast_group}].")

        self.s_out = self.connect_mcast()


    def connect_mcast(self) -> socket.socket:
        
        # Create the socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # Set a timeout so the socket does not block indefinitely when trying
        # to receive data.
        sock.settimeout(0.2)

        # Set the time-to-live for messages to 1 so they do not go past the
        # local network segment.
        ttl = struct.pack('b', 1)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)

        return sock

    def send(self, buf: bytes):
        server_address = (self.mcast_group_ip, DEFAULT_STAT_PORT)
        self.s_out.sendto(buf, server_address)
    

    def control_set_frequency(self, f: float, m:str, ssrc:int):
        buf = bytes()
        
        # 00 - Status Update / 01 - Control update
        buf = bytes([1])
        buf = encode_double(buf, StatusType.RADIO_FREQUENCY, f)
        buf = encode_str(buf, StatusType.PRESET, m)                           # Mode Preset
        buf = encode_int(buf, StatusType.OUTPUT_SSRC, ssrc)                   # Specific SSRC
        buf = encode_int(buf, StatusType.COMMAND_TAG, random.getrandbits(32)) # Append a command tag
        buf = encode_eol(buf)

        self.log.debug(f"Encoded: [{len(buf)}] bytes, sending to server... [{buf.hex()}]")
        self.send(buf)

    def close(self):
        if (self.s_out):
            self.s_out.close()
            self.s_out = None

def main():
    rc = Ka9qRadioControl(mcast_group='hf.local')

    # rc.control_set_frequency(1116000.0, 1000)
    # rc.control_set_frequency(612000.0, 'am', 9999991)    
    # rc.control_set_frequency(7093000.0, 'lsb', 9999991)
    # time.sleep(5)
    rc.control_set_frequency(1116000.0, 'am', 9999991)



if __name__ == "__main__":
    main()