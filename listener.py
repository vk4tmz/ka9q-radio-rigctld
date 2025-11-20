
import socket
import struct
import threading
import time

from resolver import resolve_name
from control import DEFAULT_MCAST_GROUP, DEFAULT_STAT_PORT
from status import parsePacket, StatusType;
from typing import Any

class Ka9qRadioStatusListener():
    
    statusListenerHandlerRunning: bool
    statusListenerHandlerThread: threading.Thread

    mcast_group: str
    mcast_group_ip: str

    s_in: socket.socket     # Inbound / Listner mcast socket

    ssrcFilter: list[int]
    status: dict[int, dict[StatusType, Any]]    # Key: SSRC - 

    def __init__(self, mcast_group:str=DEFAULT_MCAST_GROUP, ssrcFilter: list[int]=[]):
        self.mcast_group = mcast_group
        self.ssrcFilter = ssrcFilter
        self.status = {}

        names = resolve_name(mcast_group)
        if names and len(names) > 0:
            self.mcast_group_ip = names[0].compressed
        else:
            raise Exception(f"Failed to resolve multicast group name: [{mcast_group}].")

        self.s_in = self.listen_mcast(mcast_group)

    def listen_mcast(self, mcast_group_ip: str) -> socket.socket:
        
        # Recv
        server_address = ('', DEFAULT_STAT_PORT)

        # Create the socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

         # Allow multiple processes to bind to the same address/port
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Optional: Enable SO_REUSEPORT for potentially better load balancing
        try:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        except AttributeError:
            print("SO_REUSEPORT not available on this system.")

        # Bind to the server address
        sock.bind(server_address)

        # Tell the operating system to add the socket to the multicast group
        # on all interfaces.
        group = socket.inet_aton(self.mcast_group_ip)
        mreq = struct.pack('4sL', group, socket.INADDR_ANY)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
    

        return sock

    def statusListenerHandler(self):
        # Receive/respond loop
        while True:
            try:
                data, address = self.s_in.recvfrom(1024)
                
                # Only looking for potnetial status packets (~300-375bytes). Larger sizes are most likely
                # spectrum / IQ data related packets 
                if (len(data) > 300) and (len(data) < 500):
                    stat = parsePacket(data)

                    if (StatusType.OUTPUT_SSRC in stat):
                        # print(f"Packet: [{data.hex()}]")

                        ssrc = stat[StatusType.OUTPUT_SSRC]

                        if (len(self.ssrcFilter) == 0) or (ssrc and ssrc in self.ssrcFilter):
                            self.status[stat[StatusType.OUTPUT_SSRC]] = stat
                            # print(f"SSRC: [{ssrc}] Freq: [{stat[StatusType.RADIO_FREQUENCY]}]", flush=True)
                            # print(f"SSRC: [{ssrc}] Stat: [{stat}]")

                    else:
                        print(f"WARNING! - record did not contain valid OUTPUT_SSRC value.")

            except socket.timeout as e:
                pass
            except Exception as e:
                print(f"Ka9qRadioStatusListener() - An error occurred: {e}")

    def startHandler(self):
        self.statusListenerHandlerRunning = True
        self.statusListenerHandlerThread =  threading.Thread(target=self.statusListenerHandler, daemon=True)
        self.statusListenerHandlerThread.start()

    def stopHandler(self):
        self.statusListenerHandlerRunning = False
        self.statusListenerHandlerThread.join(2)

def main():
    rs = Ka9qRadioStatusListener(mcast_group='hf.local', ssrcFilter=[9999991])

    rs.startHandler()
    
    print(f"Ka9qRadioStatusListener() - Handler has been started, sleeping...")
    try:
        while (True):
            time.sleep(0.5)
            if (len(rs.status) > 0):
                print(rs.status[9999991])
            else:
                print("No Status Info....")
    finally:
        rs.stopHandler()


if __name__ == "__main__":
    main()