# Adapted from hamlibserver.py by James C. Ahlstrom
# This software is Copyright (C) 2012 by James C. Ahlstrom, and is
# licensed for use under the GNU General Public License (GPL).
# See http://www.opensource.org.
# Note that there is NO WARRANTY AT ALL.  USE AT YOUR OWN RISK!!

import logging
import signal
import socket
import string
import sys
import threading
import time

from listener import Ka9qRadioStatusListener
from control import Ka9qRadioControl
from status  import StatusType
from typing import Any

DEFAULT_HAMLIB_HOST = 'localhost'
DEFAULT_HAMLIB_PORT = 4575

DEFAULT_SSRC_ID = 9999991
DEFAULT_MODE = 'usb'

# This module creates a Hamlib TCP server that implements the rigctl protocol.  To start the server,
# run "python hamlibserver.py" from a command line.  To exit the server, type control-C.  Connect a
# client to the server using localhost and port 4575.  The TCP server will imitate a software defined
# radio, and you can get and set the frequency, etc.

# Only the commands dump_state, freq, mode, ptt and vfo are implemented.
# This is not a real hardware server.  It is meant as sample code to show how to implement the protocol
# in SDR control software.  You can test it with "rigctl -m 2 -r localhost:4575".

# SoftRock "dump_state"
dump = """0
2
2
800000.000000 53700000.000000 0x4 -1 -1 0x1 0x0
0 0 0 0 0 0 0
0 0 0 0 0 0 0
0x4 1
0 0
0 0
0
0
0
0


0x0
0x0
0x0
0x0
0x0
0x0
"""

class HamlibHandler:

    log: logging.Logger
    
    """This class is created for each connection to the server.  It services requests from each client"""
    SingleLetters = {		# convert single-letter commands to long commands
        'f': 'freq',
        'm': 'mode',
        't': 'ptt',
        'v': 'vfo',
    }

    def __init__(self, app, sock, address):
        self.log = logging.getLogger("%s.%s" % (__name__, self.__class__.__name__))

        self.app = app		# Reference back to the "hardware"
        self.sock = sock
        sock.settimeout(0.0)
        self.address = address
        self.received = ''
        h = self.Handlers = {}
        h[''] = self.ErrProtocol
        h['dump_state'] = self.DumpState
        h['get_freq'] = self.GetFreq
        h['set_freq'] = self.SetFreq
        h['get_mode'] = self.GetMode
        h['set_mode'] = self.SetMode
        h['get_vfo'] = self.GetVfo
        h['get_ptt'] = self.GetPtt
        h['set_ptt'] = self.SetPtt

        h['chk_vfo'] = self.ChkVfo
        h['get_powerstat'] = self.GetPowerStatus

    def close(self):
        if (self.sock):
            try:
                self.sock.close()
            finally:
                self.sock = None


    def Send(self, text):
        """Send text back to the client. Convert string to bytes"""
        try:
            enc_txt = text.encode()
            self.log.debug(f'Send(): [{enc_txt}]')
            self.sock.sendall(enc_txt)
        except socket.error:
            self.close()

    def Reply(self, *args):  # args is name, value, name, value, ..., int
        """Create a string reply of name, value pairs, and an ending integer code."""
        if len(args) > 1:		# Use simple format
            t = ''
            for i in range(1, len(args) - 1, 2):
                t = "%s%s\n" % (t, args[i])
        else:		# No names; just the required integer code
            t = "RPRT %d\n" % args[0]
        self.Send(t)

    def ErrParam(self):		# Invalid parameter
        self.Reply(-1)

    def UnImplemented(self):  # Command not implemented
        self.Reply(-4)

    def ErrProtocol(self):  # Protocol error
        self.Reply(-8)

    def Process(self):
        """This is the main processing loop, and is called frequently.  It reads and satisfies requests."""
        if not self.sock:
            return 0
        try:  # Read any data from the socket, convert bytes to string
            text = self.sock.recv(1024).decode()
        except socket.timeout:  # This does not work
            pass
        except socket.error:  # Nothing to read
            pass
        else:					# We got some characters
            self.received += text
        if '\n' in self.received:  # A complete command ending with newline is available
            # Split off the command, save any further characters
            cmd, self.received = self.received.split('\n', 1)
        else:
            return 1
        cmd = cmd.strip()		# Here is our command
        # print('Get', cmd)
        if not cmd:			# ??? Indicates a closed connection?
            self.log.warning('empty command')
            self.sock.close()
            self.sock = None
            return 0
        if cmd[0:1] == '\\':		# long form command starting with backslash
            args = cmd[1:].split()
            self.cmd = args[0]
            self.params = args[1:]
            self.log.debug(f"CMD: [{self.cmd}] Params: [{self.params}]")
            self.Handlers.get(self.cmd, self.UnImplemented)()
        else:						# single-letter command
            self.params = cmd[1:].strip()
            cmd = cmd[0:1]
            if cmd in 'Qq':	# Quit command
                return 0
            try:
                t = self.SingleLetters[cmd.lower()]
            except KeyError:
                self.UnImplemented()
            else:
                if cmd in string.ascii_uppercase:
                    self.cmd = 'set_' + t
                else:
                    self.cmd = 'get_' + t
                self.Handlers.get(self.cmd, self.UnImplemented)()
        return 1

    # These are the handlers for each request

    def DumpState(self):
        self.Send(dump)

    def GetFreq(self):
        self.Reply('Frequency', self.app.getFreq(), 0)

    def SetFreq(self):
        try:
            x = float(self.params)
            self.Reply(0)
        except:
            self.ErrParam()
        else:
            self.app.setFreq(x)

    def GetMode(self):
        self.Reply('Mode', self.app.getMode(), 'Passband', self.app.bandwidth, 0)

    def SetMode(self):
        try:
            mode, bw = self.params.split()
            bw = int(float(bw) + 0.5)
            self.Reply(0)
        except:
            self.ErrParam()
        else:
            self.app.setMode(mode, bw)
        

    def ChkVfo(self):
        self.Reply('CHKVFO', self.app.enableVfoMode, 0)

    def GetPowerStatus(self):
        # self.Reply('Power Status', str(self.app.powerStatus), 0)
        # self.Reply('get_powerstat', self.app.powerStatus, 0)
        self.Reply(self.app.powerStatus, 0)
        # self.Reply(0)

    def GetVfo(self):
        self.Reply('VFO', self.app.vfo, 0)

    def GetPtt(self):
        self.Reply('PTT', self.app.ptt, 0)

    def SetPtt(self):
        try:
            x = int(self.params)
            self.Reply(0)
        except:
            self.ErrParam()
        else:
            if x:
                self.app.ptt = 1
            else:
                self.app.ptt = 0

class HamlibServer:

    log: logging.Logger

    ssrc: int 
    ka9q_rc: Ka9qRadioControl
    ka9q_rs: Ka9qRadioStatusListener
    
    host: str
    port: int
    hamlib_clients: list[HamlibHandler]
    hamlib_socket: socket.socket
    serverHandlerRunning: bool

    def __init__(self, mcast_group:str, ssrc: int, freq_hz:int, mode:str, 
                 host:str=DEFAULT_HAMLIB_HOST, port:int=DEFAULT_HAMLIB_PORT):
        self.log = logging.getLogger("%s.%s" % (__name__, self.__class__.__name__))

        self.host = host
        self.port = port

        self.registerSignalHandlers()

        self.ssrc = ssrc
        self.ka9q_rc = Ka9qRadioControl(mcast_group)
        self.ka9q_rs = Ka9qRadioStatusListener(mcast_group, [ssrc])
        self.ka9q_rs.startHandler()
        self.log.info("KA9Q Radio Controller & Status Listener processes started.")

        # This is the init state of the "hardware", but should be quickly updated by by
        # direct values read from radio.
        self.freq = freq_hz
        self.mode = mode
        self.bandwidth = 2400
        self.vfo = "VFO"
        self.ptt = 0
        self.enableVfoMode = 0
        self.powerStatus = 1    # TODO: always on for now, but possible monitor MCAST for data
        
        # update the VFO with the specified initial Freq and Mode
        self.ka9q_rc.control_set_frequency(self.freq, self.mode, self.ssrc)

    def registerSignalHandlers(self):
        signal.signal(signal.SIGINT, self.handle_signal)
        signal.signal(signal.SIGTERM, self.handle_signal)
        signal.signal(signal.SIGQUIT, self.handle_signal)

    def getStatus(self) -> dict[StatusType, Any] | None:
        if (len(self.ka9q_rs.status) > 0) and (self.ssrc in self.ka9q_rs.status):
            return self.ka9q_rs.status[self.ssrc]
        
        return None

    def getRtpMcastSocket(self):
        s = self.getStatus()
        if (s and (StatusType.OUTPUT_DATA_DEST_SOCKET in s)):
            return s[StatusType.OUTPUT_DATA_DEST_SOCKET]
        
        return None

    def getFreq(self) -> float:
        # TODO: Do we move this to be updated using Events ?
        # TODO: Need to handle if SSRC not available 
        self.freq = self.ka9q_rs.status[DEFAULT_SSRC_ID][StatusType.RADIO_FREQUENCY]
        self.log.debug(f"GetFreq(): [{self.freq}]")
        return self.freq

    def setFreq(self, x: float):
        self.freq = x

        self.ka9q_rc.control_set_frequency(self.freq, self.mode, DEFAULT_SSRC_ID)
        self.log.debug(f"SetFreq: [{x}]")

    def getMode(self) -> str:
        # TODO: Do we move this to be updated using Events ?
        # TODO: Need to handle if SSRC not available 
        self.mode = self.ka9q_rs.status[DEFAULT_SSRC_ID][StatusType.PRESET].upper()
        self.log.debug(f"GetMode(): [{self.mode}]")
        return self.mode

    def setMode(self, mode:str, bw: int):
        self.mode = mode
        self.bandwidth = bw

        self.ka9q_rc.control_set_frequency(self.freq, self.mode, DEFAULT_SSRC_ID)
        self.log.debug(f"SetMode: [{self.mode}]  Bw: [{self.bandwidth}]")

    def bind(self):
        self.hamlib_clients = []
        self.hamlib_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.hamlib_socket.bind((self.host, self.port))
        self.hamlib_socket.settimeout(0.0)
        self.hamlib_socket.listen(0)
        
    def listen(self):
        self.bind()
        self.serverHandlerRunning = True
        try:
            while self.serverHandlerRunning:
                time.sleep(0.1)
                try:
                    conn, address = self.hamlib_socket.accept()
                except socket.error:
                    pass
                else:
                    self.log.info(f"Connection from: {address}")
                    self.hamlib_clients.append(HamlibHandler(self, conn, address))
                for client in self.hamlib_clients:
                    ret = client.Process()
                    if not ret:		# False return indicates a closed connection; remove the server
                        self.hamlib_clients.remove(client)
                        self.log.info(f"Removed Client: {client.address}")
                        break
        finally:
            self.log.info("Closing client connections and exiting...")
            self.close()
            
    def close(self):
        # Stop our Radio Listener/Controller
        self.ka9q_rs.stopHandler()
        self.ka9q_rc.close()

        for client in self.hamlib_clients:
            # Try ensuring all remaining client connections are closed
            try:
                client.close()
            except Exception as ex:
                pass
        
        try:
            if (self.hamlib_socket):
                self.hamlib_socket.close()
        except Exception as ex:
            pass

    def start(self):
        self.serverHandlerThread = threading.Thread(target=self.listen, args=(), daemon=True)
        self.serverHandlerThread.start()

    def stop(self):
        self.serverHandlerRunning = False
        self.serverHandlerThread.join(2)

    def handle_signal(self, signum, frame):
        self.log.info(f"Signal: [{signum}] received. Requesting shutdown...")
        self.serverHandlerRunning = False
        time.sleep(2)
        self.close()



if __name__ == "__main__":
    try:
        HamlibServer(mcast_group='hf.local', ssrc=9999991, freq_hz=7078000, mode='usb', host='localhost',port=DEFAULT_HAMLIB_PORT).listen()
    except KeyboardInterrupt:
        sys.exit(0)
