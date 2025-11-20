

import math
import socket
import struct

from collections import deque
from enum import Enum
from typing import Dict, Any


def dB2power(x:float) -> float:
    return math.pow(10.0,x/10.0)

def power2dB(x:float) -> float:
    return  (10.0 * math.log10(x))

def dB2voltage(x:float) -> float:
    return math.pow(10.0, x/20.0)

def voltage2dB(x:float) -> float:
    return (20.0 * math.log10(x))


class StatusType(Enum):
    EOL = 0 
    COMMAND_TAG = 1           # Echoes tag from requester
    CMD_CNT = 2               # Count of input commands
    GPS_TIME = 3              # Nanoseconds since GPS epoch (remember to update the leap second tables!)
    DESCRIPTION = 4           # Free form text describing source
    #
    STATUS_DEST_SOCKET = 5 
    SETOPTS = 6 
    CLEAROPTS = 7 
    RTP_TIMESNAP = 8          # snapshot of current real-time-protocol timestamp  for linking RTP timestamps to clock time via GPS_TIME
    UNUSED4 = 9 
    INPUT_SAMPRATE = 10       # Nominal sample rate (integer)
    UNUSED6 = 11 
    UNUSED7 = 12 
    INPUT_SAMPLES = 13 
    UNUSED8 = 14 
    UNUSED9 = 15 
    #
    OUTPUT_DATA_SOURCE_SOCKET = 16 
    OUTPUT_DATA_DEST_SOCKET = 17 
    OUTPUT_SSRC = 18 
    OUTPUT_TTL = 19 
    OUTPUT_SAMPRATE = 20 
    OUTPUT_METADATA_PACKETS = 21 
    OUTPUT_DATA_PACKETS = 22 
    OUTPUT_ERRORS = 23 
    #
    # Hardware
    CALIBRATE = 24 
    # Hardware-specific analog gains
    LNA_GAIN = 25 
    MIXER_GAIN = 26 
    IF_GAIN = 27 
    #
    DC_I_OFFSET = 28 
    DC_Q_OFFSET = 29 
    IQ_IMBALANCE = 30 
    IQ_PHASE = 31 
    DIRECT_CONVERSION = 32    # Boolean indicating SDR is direct conversion -- should avoid DC
    #
    # Tuning
    RADIO_FREQUENCY = 33 
    FIRST_LO_FREQUENCY = 34 
    SECOND_LO_FREQUENCY = 35 
    SHIFT_FREQUENCY = 36 
    DOPPLER_FREQUENCY = 37 
    DOPPLER_FREQUENCY_RATE = 38 
    #
    # Filtering
    LOW_EDGE = 39 
    HIGH_EDGE = 40 
    KAISER_BETA = 41 
    FILTER_BLOCKSIZE = 42 
    FILTER_FIR_LENGTH = 43 
    FILTER2 = 44 
    #
    # Signals
    IF_POWER = 45 
    BASEBAND_POWER = 46 
    NOISE_DENSITY = 47 
    #
    # Demodulation configuration
    DEMOD_TYPE = 48               # 0 = linear (default)  1 = FM  2 = WFM/Stereo  3 = spectrum
    OUTPUT_CHANNELS = 49          # 1 or 2 in Linear  otherwise 1
    INDEPENDENT_SIDEBAND = 50     # Linear only
    PLL_ENABLE = 51 
    PLL_LOCK = 52        # Linear PLL
    PLL_SQUARE = 53      # Linear PLL
    PLL_PHASE = 54       # Linear PLL
    PLL_BW = 55          # PLL loop bandwidth
    ENVELOPE = 56        # Envelope detection in linear mode
    SNR_SQUELCH = 57     # Enable SNR squelch  all modes
    #
    # Demodulation status
    PLL_SNR = 58         # FM  PLL linear
    FREQ_OFFSET = 59     # FM  PLL linear
    PEAK_DEVIATION = 60  # FM only
    PL_TONE = 61         # PL tone squelch frequency (FM only)
    #
    # Settable gain parameters
    AGC_ENABLE = 62           # boolean  linear modes only
    HEADROOM = 63             # Audio level headroom  stored as amplitude ratio  exchanged as dB
    AGC_HANGTIME = 64         # AGC hang time  stored as samples  exchanged as sec
    AGC_RECOVERY_RATE = 65    # stored as amplitude ratio/sample  exchanged as dB/sec
    FM_SNR = 66               # selected FM SNR (variance or signal snr)
    AGC_THRESHOLD = 67        # stored as amplitude ratio  exchanged as dB
    #
    GAIN = 68                 # AM  Linear only  stored as amplitude ratio  exchanged as dB
    OUTPUT_LEVEL = 69         # All modes
    OUTPUT_SAMPLES = 70 
    #
    OPUS_BIT_RATE = 71 
    MINPACKET = 72            # Minimum number of full blocks in an output packet  unless already full (0-3)
    FILTER2_BLOCKSIZE = 73 
    FILTER2_FIR_LENGTH = 74 
    FILTER2_KAISER_BETA = 75 
    UNUSED16 = 76 
    #
    FILTER_DROPS = 77 
    LOCK = 78      # Tuner is locked  will ignore retune commands (boolean)
    #
    TP1 = 79  # General purpose test points (floating point)
    TP2 = 80 
    #
    GAINSTEP = 81 
    AD_BITS_PER_SAMPLE = 82   # Front end A/D width  used for gain scaling
    SQUELCH_OPEN = 83         # Squelch opening threshold SNR
    SQUELCH_CLOSE = 84        # and closing
    PRESET = 85               # char string containing mode presets
    DEEMPH_TC = 86            # De-emphasis time constant (FM only)
    DEEMPH_GAIN = 87          # De-emphasis gain (FM only)
    CONVERTER_OFFSET = 88     # Frequency converter shift (if present)
    PL_DEVIATION = 89         # Measured PL tone deviation  Hz (FM only)
    THRESH_EXTEND = 90        # threshold extension enable (FM only)
    #
    # Spectral analysis
    UNUSED20 = 91 
    COHERENT_BIN_SPACING = 92 # (1-overlap) * block rate = (1 - ((M-1)/(L+M-1))) * block rate
    NONCOHERENT_BIN_BW = 93   # Bandwidth (Hz) of noncoherent integration bin  some multiple of COHERENT_BIN_SPACING
    BIN_COUNT = 94            # Integer number of bins accumulating energy noncoherently
    CROSSOVER = 95            # Frequency in Hz where spectrum algorithm changes
    BIN_DATA = 96             # Vector of relative bin energies  real (I^2 + Q^2)
    #
    RF_ATTEN = 97             # Front end attenuation (introduced with rx888)
    RF_GAIN = 98              # Front end gain (introduced with rx888)
    RF_AGC = 99               # Front end AGC on/off
    FE_LOW_EDGE = 100         # edges of front end filter
    FE_HIGH_EDGE = 101 
    FE_ISREAL = 102           # Boolean  true -> front end uses real sampling  false -> front end uses complex
    BLOCKS_SINCE_POLL = 103   # Blocks since last poll
    AD_OVER = 104             # A/D full scale samples  proxy for overranges
    RTP_PT = 105              # Real Time Protocol Payload Type
    STATUS_INTERVAL = 106     # Automatically send channel status over *data* channel every STATUS_INTERVAL frames
    OUTPUT_ENCODING = 107     # Output data encoding (see enum encoding in multicast.h)
    SAMPLES_SINCE_OVER = 108  # Samples since last A/D overrange
    PLL_WRAPS = 109           # Count of complete linear mode PLL rotations
    RF_LEVEL_CAL = 110        # Adjustment relating dBm to dBFS

# Translated from ka9q-radio -> decode_status.c && dump.c
StatusTypeEncoding = [
    [StatusType.EOL, 0, 'b', None, None],
    [StatusType.COMMAND_TAG, 0, 'i', None, None],
    [StatusType.CMD_CNT, 1, 'i', None, None],
    [StatusType.GPS_TIME, 0, 'i', None, None], 
    [StatusType.DESCRIPTION, 0, 's', None, None],
    #
    [StatusType.STATUS_DEST_SOCKET, 0, 'ns', None, None],
    [StatusType.SETOPTS, 0, 'i', None, None],
    [StatusType.CLEAROPTS, 0, 'i', None, None],
    [StatusType.RTP_TIMESNAP, 0, 'i', None, None],
    [StatusType.UNUSED4, 0, 'b', None, None],
    [StatusType.INPUT_SAMPRATE, 0, 'i', None, None],
    [StatusType.UNUSED6, 0, 'b', None, None],
    [StatusType.UNUSED7, 0, 'b', None, None],
    [StatusType.INPUT_SAMPLES, 0, 'i', None, None],
    [StatusType.UNUSED8, 0, 'b', None, None],
    [StatusType.UNUSED9, 0, 'b', None, None],
    #
    [StatusType.OUTPUT_DATA_SOURCE_SOCKET, 0, 'ns', None, None],
    [StatusType.OUTPUT_DATA_DEST_SOCKET, 0, 'ns', None, None],
    [StatusType.OUTPUT_SSRC, 0, 'i', None, None],
    [StatusType.OUTPUT_TTL, 0, 'i', None, None],
    [StatusType.OUTPUT_SAMPRATE, 0, 'i', None, None],
    [StatusType.OUTPUT_METADATA_PACKETS, 0, 'i', None, None],
    [StatusType.OUTPUT_DATA_PACKETS, 0, 'i', None, None],
    [StatusType.OUTPUT_ERRORS, 0, 'i', None, None],
    #
    # Hardware
    [StatusType.CALIBRATE, 0, 'd', None, None],
    # Hardware-specific analog gains
    [StatusType.LNA_GAIN, 0, 'i', None, None],
    [StatusType.MIXER_GAIN, 0, 'i', None, None],
    [StatusType.IF_GAIN, 0, 'i', None, None],
    #
    [StatusType.DC_I_OFFSET, 0, 'f', None, None],
    [StatusType.DC_Q_OFFSET, 0, 'f', None, None],
    [StatusType.IQ_IMBALANCE, 0, 'f', None, None],
    [StatusType.IQ_PHASE, 0, 'f', None, None],
    [StatusType.DIRECT_CONVERSION, 0, 'B', None, None],
    #
    # Tuning
    [StatusType.RADIO_FREQUENCY, 0, 'd', None, None],
    [StatusType.FIRST_LO_FREQUENCY, 0, 'd', None, None],
    [StatusType.SECOND_LO_FREQUENCY, 0, 'd', None, None],
    [StatusType.SHIFT_FREQUENCY, 0, 'd', None, None],
    [StatusType.DOPPLER_FREQUENCY, 0, 'd', None, None],
    [StatusType.DOPPLER_FREQUENCY_RATE, 0, 'd', None, None],
    #
    # Filtering
    [StatusType.LOW_EDGE, 0, 'f', None, None],
    [StatusType.HIGH_EDGE, 0, 'f', None, None],
    [StatusType.KAISER_BETA, 0, 'f', None, None],
    [StatusType.FILTER_BLOCKSIZE, 0, 'i', None, None],
    [StatusType.FILTER_FIR_LENGTH, 0, 'i', None, None],
    [StatusType.FILTER2, 0, 'i', None, None],
    #
    # Signals
    [StatusType.IF_POWER, 0, 'f', None, None],
    [StatusType.BASEBAND_POWER, 0, 'f', None, None],
    [StatusType.NOISE_DENSITY, 0, 'f', None, None],
    #
    # Demodulation configuration
    [StatusType.DEMOD_TYPE, 0, 'i', None, None],
    [StatusType.OUTPUT_CHANNELS, 0, 'i', None, None],
    [StatusType.INDEPENDENT_SIDEBAND, 0, 'B', None, None],
    [StatusType.PLL_ENABLE, 0, 'B', None, None],
    [StatusType.PLL_LOCK, 0, 'B', None, None],
    [StatusType.PLL_SQUARE, 0, 'B', None, None],
    [StatusType.PLL_PHASE, 0, 'f', None, None],
    [StatusType.PLL_BW, 0, 'f', None, None],
    [StatusType.ENVELOPE, 0, 'B', None, None],
    [StatusType.SNR_SQUELCH, 0, 'B', None, None],
    #
    # Demodulation status
    [StatusType.PLL_SNR, 0, 'f', None, None],
    [StatusType.FREQ_OFFSET, 0, 'f', None, None],
    [StatusType.PEAK_DEVIATION, 0, 'f', None, None],
    [StatusType.PL_TONE, 0, 'f', None, None],
    #
    # Settable gain parameters
    [StatusType.AGC_ENABLE, 0, 'B', None, None],
    [StatusType.HEADROOM, 0, 'f', None, None],
    [StatusType.AGC_HANGTIME, 0, 'f', None, None],
    [StatusType.AGC_RECOVERY_RATE, 0, 'f', None, None],
    [StatusType.FM_SNR, 0, 'f', None, None],
    [StatusType.AGC_THRESHOLD, 0, 'f', None, None],
    #
    [StatusType.GAIN, 0, 'f', None, None],
    [StatusType.OUTPUT_LEVEL, 0, 'f', None, None],
    [StatusType.OUTPUT_SAMPLES, 0, 'i', None, None],
    #
    [StatusType.OPUS_BIT_RATE, 0, 'i', None, None],
    [StatusType.MINPACKET, 0, 'i', None, None],
    [StatusType.FILTER2_BLOCKSIZE, 0, 'i', None, None],
    [StatusType.FILTER2_FIR_LENGTH, 0, 'i', None, None],
    [StatusType.FILTER2_KAISER_BETA, 0, 'f', None, None],
    [StatusType.UNUSED16, 0, 'b', None, None],
    #
    [StatusType.FILTER_DROPS, 0, 'i', None, None],
    [StatusType.LOCK, 0, 'i', None, None],
    #
    [StatusType.TP1, 0, 'f', None, None],
    [StatusType.TP2, 0, 'f', None, None],
    #
    [StatusType.GAINSTEP, 0, 'i', None, None],
    [StatusType.AD_BITS_PER_SAMPLE, 0, 'i', None, None],
    [StatusType.SQUELCH_OPEN, 0, 'f', None, None],
    [StatusType.SQUELCH_CLOSE, 0, 'f', None, None],
    [StatusType.PRESET, 0, 's', None, None],
    [StatusType.DEEMPH_TC, 0, 'f', None, None],
    [StatusType.DEEMPH_GAIN, 0, 'f', None, None],
    [StatusType.CONVERTER_OFFSET, 0, 'f', None, None],
    [StatusType.PL_DEVIATION, 0, 'f', None, None],
    [StatusType.THRESH_EXTEND, 0, 'B', None, None],
    #
    # Spectral analysis
    [StatusType.UNUSED20, 0, 'b', None, None],
    [StatusType.COHERENT_BIN_SPACING, 0, 'i', None, None],
    [StatusType.NONCOHERENT_BIN_BW, 0, 'f', None, None],
    [StatusType.BIN_COUNT , 0, 'i', None, None],
    [StatusType.CROSSOVER, 0, 'f', None, None],
    [StatusType.BIN_DATA, 0, 'b', None, None],
    #
    [StatusType.RF_ATTEN, 0, 'f', None, None],
    [StatusType.RF_GAIN, 0, 'f', None, None],
    [StatusType.RF_AGC, 0, 'i', None, None],
    [StatusType.FE_LOW_EDGE, 0, 'f', None, None],
    [StatusType.FE_HIGH_EDGE, 0, 'f', None, None],
    [StatusType.FE_ISREAL, 0, 'B', None, None],
    [StatusType.BLOCKS_SINCE_POLL, 0, 'i', None, None],
    [StatusType.AD_OVER, 0, 'i', None, None],
    [StatusType.RTP_PT, 0, 'i', None, None],
    [StatusType.STATUS_INTERVAL, 0, 'i', None, None],
    [StatusType.OUTPUT_ENCODING, 0, 'i', None, None],
    [StatusType.SAMPLES_SINCE_OVER, 0, 'i', None, None],
    [StatusType.PLL_WRAPS, 0, 'i', None, None],
    [StatusType.RF_LEVEL_CAL, 0, 'f', None, None],
]

#####################################################################
## Status Decoding Routines
#####################################################################

def decodeVal(p: bytes):
    vt = p[0]

    if (vt == 0):
        return 0, bytes(), p[1:]

    dl = 1     # vl < 128 only 1 byte needed for data length value
    ds = 2     # offset for start of data
    vl = p[1]
    if vl > 0:    
        if (vl >= 128):
            dl = (vl - 0x80)  # 82->2, 83->3 and 84->4
            ds = 2+dl
            vl = decodeInt64(p[2:ds])
            vb = p[ds:ds+vl]

        vb = p[ds:ds+vl]
    else:
        vb = bytes()
    
    # Remove processed bytes
    np = p[ds+vl:]

    return vt, vb, np

def decodeDouble(vb: bytes):
    vbl = len(vb)
    if vbl < 8:
        vb = bytes([0]*(8-vbl)) + vb
    v = struct.unpack('>d', vb[0:8])[0]
    return v


def decodeFloat(vb: bytes):
    vbl = len(vb)
    if vbl < 4:
        vb = bytes([0]*(4-vbl)) + vb
    v = struct.unpack('>f', vb[0:4])[0]
    return v

def decodeInt64(vb: bytes):
    vbl = len(vb)
    if (vbl < 8):
        vb = bytes([0]*(8-vbl)) + vb

    v = struct.unpack('>Q', vb[0:8])[0]
    return v

def decodeByte(vb: bytes):
    vbl = len(vb)
    if (vbl == 0):
        v = 0
    else:
        v = struct.unpack('>B', vb[0:1])[0]
    
    return v

def decodeBool(vb):
    v = decodeInt64(vb)
    return not (v == 0)

def decodeNetworkSocket(vb:bytes):
    vbl = len(vb)
    if (vbl == 6):   # IPv4 Addr & Port
        if vbl < 6:
            vb = bytes([0]*(6-vbl)) + vb
        ns = {'addr_b': vb[0:4], 'port': decodeInt64(vb[4:6]) }
    elif (vbl == 10): # IPv6 Addr & Port
        if vbl < 10:
            vb = bytes([0]*(10-vbl)) + vb
        ns = {'addr_b': vb[0:8], 'port': decodeInt64(vb[8:10]) }

    if (ns['addr_b']):
        ipstr=socket.inet_ntoa(ns['addr_b'])
        ns['addr']=ipstr

    return ns


def parsePacket(p:bytes) -> dict[StatusType, Any]:
    res: dict[StatusType, Any] = {}
    while (len(p) >= 2):
        vt, vb, p = decodeVal(p)

        if (vt == 0):   # Encountered EOL move on
            if len(res) > 0:
                break;
            
            continue

        if (vt > 110):
            print(f"ERROR!! Unhandled StatusType: [{vt}],  vb: [{vb}] - Skipped....")
            continue

        ste = StatusTypeEncoding[vt]
        t = ste[0];     # StatusType
        ml = ste[1];    # min length
        te = ste[2];    # typeEncoding

        encConvFunc = ste[3];    # function to perform on value before enoding
        decConvFunc = ste[4];    # function to perform on value after decoding

        vbl = len(vb)

        match (te):
            case 'ns':  # Network Socket Address
                v = decodeNetworkSocket(vb)
            case 's':   # Convert bytes to string
                v = ""
                if vbl > 0:
                    v = vb.decode('utf-8')
            case 'd':   # double precision float - min/max 8 bytes
                v = decodeDouble(vb)
            case 'f':   # single precision float - min/max 4 bytes
                v = decodeFloat(vb)
            case 'i':   # if ml == 1 unsigned byte, else int64 else assume int upt to 64 bits
                if (ml == 1):
                    v = decodeByte(vb)
                else:
                    v = decodeInt64(vb)
            case 'B':    # Boolean
                v = decodeBool(vb)
            case 'b':    # Treat as byte data no further decoding needed
                v = vb

        if (decConvFunc):
            v = decConvFunc(v)

        res[t] = v
        # print(f"Type: [{vt}:{t}] Val: [{v}]")

    return res


#####################################################################
## Status Encoding Routines
#####################################################################

def encode_str(buf:bytes, type: StatusType, vs: str) -> bytes:
    vb = vs.encode("utf-8");
    vt_len = len(vb)
    buf += type.value.to_bytes(1, byteorder='big')
    buf += vt_len.to_bytes(1, byteorder='big')
    buf += vb

    return buf

def encode_val(buf:bytes, type: StatusType, vb: bytes) -> bytes:
    # Compute len to trim assuming vb is 'big endian' find first 0 byte
    vt_len = len(vb)
    for x in vb:
        if (x != 0):
            break
        vt_len -= 1

    buf += type.value.to_bytes(1, byteorder='big')
    buf += vt_len.to_bytes(1, byteorder='big')
    buf += vb[len(vb)-vt_len:]
    # print(f"Encoded:  Type: {type} vt_len: {vt_len}")

    return buf

def encode_double(buf:bytes, type: StatusType, x: float) -> bytes:
    #   Simply returning 0 means if not checked will continue with next encoding in wrong spot ?
    if (math.isnan(x)):
        return buf; # Never encode a NAN, return orig buf

    return encode_val(buf, type, struct.pack('>d', x))

def encode_int64(buf:bytes, type: StatusType, x: int) -> bytes:
    # buf += x.to_bytes(8, 'big')
    return encode_val(buf, type, struct.pack('>Q', x))
    
def encode_int(buf:bytes, type: StatusType, x: int) -> bytes:
    return encode_int64(buf, type, x)

def encode_eol(buf:bytes) -> bytes:
   b = StatusType.EOL.value.to_bytes(1, byteorder='big')
   return buf + b


#####################################################################
## Main
#####################################################################


def main():
    # spectrum data seen when using ka9q-web
    # p1 = bytes.fromhex("00120203e9010477e877d30201040416766b34746d7a2034306d20454648572040206b61397108000506ef872678138e030814168627eaf9c8eb0d0589941800000a0403dcc4ff660101180062043fbbb29861006e04bfb33333630019001a001b006404466a600065044be85c605201102108416312d00000000022002308c16312d0000000002a0313c6802b0304f1a14d002d04c1390fd16801b96c051733ea68962f04ff8000003001035d04447a00005e0206545f04422000006082195030d381df2f0321922f9ae6ea2f7f4a492f47ffb22f67c0d42f3728d52efdac222f22866c2f654eca2eedf9b42f475af72f14c20b2f2173912f36e4cb2f0d9aa02ece35552f00afde2f2a60072ee265b42ef2df1e2f312f132f6ec9a02f34331b2f0428482f88e5192f6fd0c32f4ceafc2eefac252ec7e8ab2f4d33bc2f03b9552f26dcf82f47fffa2f32a0cd2f087dc32f125bbc2f01733d2f47b5332f26a22d2eff7e3c2f3ef9aa2f14dcce2f362ef22f598d472ef5db552f0f73022f071ff32efd7d2e2f0c6abc2f393cde2ef619d72f0269ae2f2309322f024d222f8c62d32f3d9ea52f03a7992f19c2b32f2ae0122f2bcb732efb65a12f3dc7542f4055ef2f4807142f4791532f14c54e2f4b464a2f6eb6212f659c5f2f4d964f2f31ddd22f1f5c452f1152732f1698032f05a1ee2f375c002ee729282f4af1722eec41b82f249eee2f20fa002f1b96bb2f80712c32216aa632e2e5bc31d423c32f694a112f5259122f4728232f2981622f3061552f47c0972f34db862f291c092f15fe0f2f24cf772f14a4392f1bd6ae2f1921642ef745282f4c09d92f0d094c2f48ae1c2f6069042f25b3492f230dce2f0ce5b22f5604522f653f822f1c6b502f08d91d2f623f632f5a40692f08db702f3449d42f2882052edb85532f47822a2f0ce3e82f4d6f1d2f0a4fb62f19b9bf2f69a2982f0b22152f2bbea12f2eaefb2f58e6012f0c6e032f2894dd2f49292e2f41abd02f0a65072f4fcd342eedae302f0465dc2f2ee9072f7999ea2f25d4982f4ae81b2f6f28482f8b7ada2f2b01622f0010482f1bb5d62f1a942f2f26ac832ec8841f2f28d0232f015f312f04028b2f7ff61b2f22ac402f1f3b2d2fc050992f13db942f3b5a1b2f3431f92eec20002f4611392f73c02e2f4de4e72f15a7b22ef289b32f36a6722f6dfaf22f3b52732f24d2ed2f7035082f6540f12f12a3ed2f0b9f6a2ef6e5522f277a032f0ca35b2f0c16112f8bcb8e2f6ef2162f2f66dd2f2e9c372f4e6a582f4fae402f0811f12f41fc6d2ee7b5cc2f0517312f1c1e742f311b082f3f496d2f4f21822f59868b2f4eda9b2f5f8f152f3bbd9a2f26632e2f1779902eecd56d2f2db00f2f4ca0ba2f1b3f8f2f3c55bd2f409c942f2d619b2f3574122f5188cf2f5e1ee22f0b8f552f2f49b12f1e9be02f1718532f00db0d2f4ac6622f247e742f2b525c2f3c28b92f33074d2f5c9cdf2f44c9a62f2a339b2f4a3c742f2208082f2cadee2f38a4432f654c272f35ab5c2f2970422f62a08c2f39084d2f37036e2f0eff1b2f40fd7d2f05d5612f493ae92f30da7b2f24a8732f64caee2f743a782f32fd332f563bf12f4efbbb2f2a0c012f7dbb732f38d4c72efd5cfe2f9bb9e32f255cc12f5b9e3a2f236ac42eb1d5822f80d16c2f2d8c9330143dc12f4a15992f3066182f5f12b22f2117a62f8902072f47f1d12fb0f2362f2fd2c92f3d12222f78c7922f42dbb52f356a3e2f8ad21f2f6f554c2f1268f42f03802f2f0d5c882f48499d2f5cfe6a2f2650a52f7e8f8d2f3b4e482f65555a2f4b061d2f25182a2f3440242f2bedeb2f51ff202f748b2b2f56b9f62f3520632f0a61d92f38c25a2f5648542f4eda4f2f3bd4e12f8b31602f2f6ab02f3433e42f1d3eea2f46a8012f4e579a2f4f3ec62f6c006f2f1705d82f36201b2efb59152f4def952f51c2c22f8284152f1717af2f30a6f12f46c64c2f5d2a702f4e0b212f3e14bd2f4be5ac2f60b0422f80bd142f553ee52f2ab3bd2f51ea322f198b7a2f4f8e532f33bb9e2f4eeb682f3ebfb42f7dfa092f412e022ee6c2cd2f68d8e02f2450d12ee22f202f62ec4b2f48fcfa2f4e63572f9939a62f7d21232f8afe7c2f2abf4b2f8f3ef42f3d563c2f5460402f82965b2f11ff302f30737c2f244ba42f76b1ce2f0058562f1e05652f3db5e42f463a662f2b6cd62f4db2882f68abff2f3aa74b2f74bc9a2f44b67a2f27031f2f4f781e2f3a3a102f6628db2f4632fa2f52355b2f4adb992f2bcd402f4bd06b2f2f77f62f893f4b2efae1432f777e042f89ac672f4679642f8281d32f528faa2f7bd9682f493b342f4b06f42f79c70a2f27ef7f2f68e66a2f5326cb2f5871542f431aa42f2931a32f2fe1952f3ceaa82fc3ea462f20b2702f5abc9c2eb5e6f52f298b762f32eaeb2f8be8472f33aad52f53d0422f147d372f30f0172f7d48932f66609b2f4a28fa2fa3f0072f2f41cc2f1f82562f8ab5c92f4b9d772f17d8da2f616c8d2ef54b282f4dc80f2f81c6f92f3bf8f32f204deb2f5c192a2f370d5b2f8b351d2f54e7812f3cabba2f76d15c2f27fe2a2f0f7a902f38a9342edd6e982f36870d2f1797e72f1aeda52f3a17eb2f1ae9022f0bf2e62f2c449c2f49c9de2f3d8d4f2f64a1152f4d9c4b2f804dbd2f3a660e2f804b8c2f81e7552f49b5c72f4a4d9c2f396fbf2f12843a2ee5f0632f2b40a32f0e131b2f4759d42f45401e2f0831352f4810632f2013b42f57b0bd2ef551c52ebcc87b2f533bc52f5db4192f22784d2f1a3d082f61b5832f1323af2f2dc59f2f9753582f399c4f2f315beb2f0c13e92f3efc362f0d4ac32f1858b72f63df322ee1a14b2f37f0692f4a288b2f4926192f6510552f3d1ce72f496dfd2f1b9df22ee930cc2f21e7562f22bf632f2d120f2f5280cc2f36c5752f68fac12f1e6d992f101fed2f02e76c2f1adbe52edda5402f06957f2f2cec272f0e2c942f52c9a12f111ca62f2307d82f1b799b2f1587312f17b1482f197af82f185f6d2f3450ef2f32dee52ee83d0f2f0f187f2ec3158a2f59c4462f4e79fd2f0e99a12f4d1ae62f2497ed2f2aa2d72f5d86512f22693b2eb649fb2f17ef422f39ceb42eee44732f3ca8092f2946102f1772632f5dff3b2f26a7702effe4df2f228bd12f15de5d2f02d95b2f4eb78b2f34d9da2f267eed2f19254a2f384a912f1a53572ef4a49c2f0869fe2eef0c592f12c4da2f082b9a2f55160f2f322b9d2f2220c32f01d8992edd43bf2f02c5692f04a50a2eef03442f2203e02ef435462f3787032eef13202f13bf8c2f15a3512f96e0862f03984d2f8353de2f27ba102f4148072f6db4532f09ac552f26b2522f207dc42eb6d0cb2ee538712f1ba9e62f06c53a2fac650e2f90ff8c2f2901e22f1722642f0e2b7d2f11551d2f362bed2f6f8dc62f04ad522ee7b13d2f03e1fd2f1e3bb32f1dc2a62f0acc0d2ee1e33f2f2dbfc22ec6a37b2f0b17072f158e5c2f0ed9882ee425e52f31e0752f4c53bf2f18a6852edf57972f0eddb32f4d0aa62f0e3ae62f5578e02f1c12022ed6a7cd2ee26afb2f267f732f1b2a7c2f2f18762efea39e2f06c53c2f2e8cc12f1131e62f30b2db2f86fbca2ecbaaaf2f0c69342f1380232f1594542ecbbb042f548c8e2f09d2052f12a98a2f0c92682f0222c32f706db72f0165632f2abc572f6c958d2f5349b52f08cb442eed38442f2083802f1760ac2f23904d2f2fdb692f0e35912f2321592f2b65102f333db32f43ef1a2f1214132f11fe932ef5b9be2f88df302f4a11b32f0f0d362efdbc122f6057a52f1fa6992f15356c2f010a3d2f1d894d2f0bb2c62f1541cb2f0760ce2f2b4f102f742a682f1880c82f6d2df72f08f6c52f1d58bb2f1bfaa62f2d8dab2f0dfe402ef4f1d92f57ea372f2273372fb37f772f2dd1ca2f22f6242f434ab42f30f7592ef29bb42f4fb3742f9b52732f09d8962f4c4f202f508e802f4884c82f1edeff2f3469342fa69b1b2f3ce1b42ed615762f1a22022ed54ee52f38765c2f352fa62ef3ac1c2f42f6f82f0b75fe2f19f4c22f52bb7c2f1e3ead2f0914832fad17e82f1149352f10eb152f1847012f58c6582f2175262f2980f32f37a8ec2f73721b2f473a3d2ef4032c2f5659ae2f0a3a442f34ee052ef305c02f342e4a2f0836ed2f4302ad2f48187c2f4404d82f4d86b62f39e5882f0d2e642f27a3612eee27e72f0274452f1ce6e02f53d6072f125b5c2f0213f82f4225fb2f478ad82f3e5e2f2f949c1d2f4512172f359ca22ef5db662f19c42a2f0ccf6e2f12e5a72f5bf6622f4a54312f3026662f05a36d2eecba652f5d0cea2f5161882f5e9b102f08e4732efedfba2f8fff5c2eec6d722f5efd9e2f2474cd2f31e3e22f0d24342f704c272f569c662eefc67e2f13b0fa2f2b9f8e2f329ded2f27c6242f326d2b2f4a01702f04406b2f0aaeea2f1eb9cd2f1ee1d92f202db52f2856582f39f3662f0760272f483e142f5c08232f4e604a2f5d659d2f2d9c752f6414c02f5429042f33f7e62f334d372f6fcd492f3c0ddd2f1c95cb2f46256b2f4cf3b82f8262a22f8120562f62dfb82f6589c02f79c7952f2a6c722f6df9d92f127c9a2f44ebb02f3932192f3290f92f2a068c2f39f5332f224f8e2f65c2932f3d2b0e2f3b73cb2f2fcd3d2f39278f2f0fc4142f856e302f2c73422f685b032f7a238f2f30b5c72f1f4a8a2f50313c2f6adb752f3101542f3a8cee2f491f062f6584092f450c862f1538592f78e0712f3e2f722f2240832f1530a02f2a074c2f9d91ea2f41bc782f4cfa732f5bd4a12f6f6fda2f39b5632f2f0e4d2f43abac2f16361d2f2472772f3a64da2f48ac922f2ae9d82f1b75fe2f4470e82f82c3a42f4eeeae2f2937cb2f9275622f38a0b72f0184b92ef915232f51c0b62f40011d2f3fd92b2f2672cb2f23a5f92f238fb22f093c17311b8c092f11a88d3036c81f2f620dee2f5ee8842f213bd02f4093a32f1e2b7f2f3bcbb32f37c74a2f4834fe2f53e58d2f00e72b2f1fdb702f2bef6f2f273ddc2eee190a2f4e9c112f19d4732f3ba02b2f1795bf2edb49dc2f1b2c8f2f17f1d72f0f6b8a2f1275742f44059c2f61d1792f8264ab2f7349e92fc6c5652f82d14d2f4622ab2f41a68d2f5780212f0016cb2f638ff12f4218592f4a0b982f3194542f4abea02f37f8362f235ac42f31cea22f3f72b92f422f122f3040d92f310ac82f467be52f0f2f532efd42c52f3dd18e2f1ca9f72f10c5472f241af12f0376b62f204e912f009a282f626cb62f0764a42f25ddd92eb697932f1389e22f1bbd9a2f3458ad2f25cd0d2f1e960c2f8946313093ad1c2f4939632f4279822f0401be2f0510072f1f588b2f5c84752f47bfa52f58cdc02ec193fe2f3e7cd42ef66f2f2f0d422e2f06dfcf2edcbf192f34ca0a2f67669c2f186fd42f3157152f16a3542f1f8de82f34f0472f038aa12f43000c2f2bb6de2f1571ac2f2118742f5667472f3d58942f37605e2f374bf72f3c436f2f317fcd2f44b02a2f301e3a2f4794362eb8fe792f36447d2f242e4e2f6085472ec7c3712f0613682f12332f2f27993d2f25853a2f406c832f5dddfe2fa9ad252fd0430931fd049a32cc71a12f698fc22f6264f92f4587db2ef46aab2f698edb2f49e23e2f122d372f1595da2f63c3fd2f09fb032f252f822eea6e412f3b76172f26f9db2f0e45c72f2c29692ef20eaf2f23673c2fa862a32f995cd52f9786452f5790b62f3e3ed02f0af0682ed839f82f36acf82f5746522f0ec5982f2988b12f2f4a622f5266972ec26c772f19ba022f1a7ca12f50f1fa2f642ea82f2f74f72f566fcd2f27671f2fc2bea12f1414de2f5509612f70636d2f2f47a12f8a69662f1d601d2f62800f300d468332187db13497904630511a512fac72952f6398942f4825c72f63d69b2f61c7b52f369a992f3ee1292f44d0332f8266b52f5fb45a2f57f7c62f6cc2bd2f5d172d2fbe11852fc252493005bbc63051385d330ec2e1341240f330453c592fb3dbc42ff9376c2f43281d2f059c782f3745b22f232bba2f1e9bd12f34807f2eca87002ed3d1152f11d0d0304e9bb23151123d333d86602fb7c56b2f23a8b22f6bc7802f31a9ef2f5bf9302f6e80322f3afd032f1195712ef114112f6bf2fc2f5df6ef2f5403172f1656f72f9f969c2f8b1f252f98e48a2fb2e1bb2f76d44a2f86e08d2f08af062f93affc2f7fd16a2f8a8ff9313ab02832a1c8142f6aee1f2f3c3cee2f926ed42f295f7c2ee360c62edce2172f380e472f9da2772f35be852f005c302f23decc2f1f85882f0cb6732f25823e2f1ebdfa2f87b91b2f3f9f712f49127030554f20326510e22f72265b2f44f29c2f35c11c2f5e0ccc2f14531f2ee3534f2f3c4e802f3e6a2d2f4be95a2f44228f2f616d662f1ab8552f1cd3b42ed5364c2f2961052f2535b22f15dc742f3d252b2f31a6f92f21d9b72f2ca0bc2edcca372f35aa7e2f292f322f4454e62ee173a92efaadc42ed3c6252f2796db2eee18ba2f51a4222f53d2232f3973cb2f4bedbf2f57a0792f2a1fa02f1f6eb62f4bc31a31a6bafe336092b32f19d31b2f01946e2f51e6c62ef40cda2f44560c2f1fc80e2f117e0f2f1a8e56302a4e303226af4f30922f8f2fce673d303f4732333afb9c3492509d30494faa2fd7228b3033750c313676723106479e2f93c33c2f4d85ab2f42f8362f2845752f59ea522f07ca2f2ed8fa332f1a6a572f1e25692f3db2382f6ca91f2f0d20d12f25d6c32f2c544a2f22ee7e2f2f4dfa2ef82b962f1cded82ef251a52ee1b3732ef6ec112ee874402f1f6adc2f16e4612f3072092f3a8dfe2f48f2372f36a7c82f2fc6302ef69ebc2f50fc312f2b53252f1347fc2ef4f2232f1494cd2ebfb76d2f15ee652f296cb32f0c7c1d2f8334cb2f5e315d2f57ba532f5487a52f7d2e362fd76176308cd3b1304b58ed30c66493333b6ef234db68473109c4e12fddbd5630a708592f7d26d82fe9dac12fad0c842f08545b2f9c11ad2f2511c42f4a313a2f3ee2742f29faa72fb267202ef208d52f109e992f24de102f6636232f44a3ae2f0c19482f9216372f2851592f43b6732f1864ad3081450f32008c6c2f34559d2f8e7be02f48dff62f81e0812f0d4d0a2f2784b32f1b87ad2ef442092f2b99c02ee7570b2f1262842f2d04b62f21f8c52f57c8e52f10329d2f81d2ac2f663cb32f471c6930510db831dcf963316446a9320c6e2030776fd13346f6f135011def31280ae3316bbb4030db8d2a316dff9930485b782f69d1a02f3a9ea72f2138332f4b62182f4dc1542f2bbd242f6a89182f20d3742fa35a423037bc132f3678d72f0b1d202f1c43232f22ab5b2f5aaf242f178bb72f2611622f2355562f40bc3f2f8860cf2f4811192f38b9552f25f6f62f44a6ba2f73645e2f7e811b2f4a54442f68c6c02f50cadb2eefcee22f3676372f5c66d52f1de5462f41c1152f1cbb942f21d0942ef8ab662f350fdb2f0f69b92fda6a3b2f26f5032f1e550c2f4cb59b2f1ae8cf2f3f63932f1f6e182f23d0822efcbc483020058531837e552f5cae2c2f6d94422f5df1642fc3930e3085a2873072413230979ef63091c85f3366f53f34cca06930ed616830261fae306226f4300c9c5f2fbadddc2f49e82a2f4008f22f5c6f632ee6fc782f3512032f0485412f0a68152f5cb00b2f7c40852f9466592f5ae8482f4336632f2e83ce2f96f7b02f51e2cc2f870ce72f1e4c1a2f7554ea2f0e00542f0f70112f25f92d2f32d48b2f53d8a72f1561ca2f48c8832f4a848d2f6922112fa0e5182f96754a310ccc7d2f0d23402f01db722f113fa52f2d94a12f53fb562f843ab52f4d264c2ec516f52f1a94e82f3bb3e42f3e6a132f9746312edacc302f1f95ee2f30d14c2f568cfe2f66c1af2f3174bb2f48db492f78c0c92f61f87c2f2923912e9c1c292f077bbf2f1be4582f6c91922f3345432f36990e2f87cd7d2f41502c2f0afd6a2f3a4aea2f5730542f119ed32f8a171a2f2a51092f4227802f2e24592f8955652f213d0f2f3bbafb2f28b1b72f8db5ee2f3e2e952f707c212f3abc582f10b0612f5b295c30af400f32beae842f55ed512f22aeac2f21e6a330052788316c0aef2f6768932f05b26d2f4edd052f676c7c2f07594f2f3e4d952f2f3e1a2f5ad4912f98715e2f7d3a8e2ef977952f2aa63f2f2e3d542f300e612f3244002f3e17f82efdb21d2f1f5d052f62bdf82f23f08d2f13d9662f3740692f304b392f02f23a2f4cfef82f3d78e82f7eba192fa8211e2f2f78692fca99d32f7629e02f606ff12f56b6dc311c3626325bd0392f7302f82f5d687e2f810c2a2fe596102f88ffc92f1abec22f7d42852f5f42762fa4995c30fa132b2f5031362f5818332f0adbc92f3f59e12f6df6302f49dc6a2f3a719a2f344b9c2fcd137731069a182f0f4c6c2f3099682f56b2c22f4b4ac32f405cd22f0db9502f2f1c532f2f89442f4f2a482f34598a2f21cdc52f1a98632f893ca82f3629682f23b37d2f179cb42f2a33d82f437b962f15a1372ff4b2792f11da772f1707202fa5984c2f1cf7382f2bed622f1884112f72233b2f3f10c92ef314bb2f25ec932f5ea5392f021c692f1e4fcd2f1dcc972f6cb34e2f1a6a722f646dfd2f65ff642f269e652f90e6df2f687ec32f38a4142f3260942f89a38d307ef54c3087b9fb2fa2a4ab300a7a7f325a9d2d33d17aab2fde55752fa2301a308b3b79309d85ef2f7b91b32f2c4d102f39fc942f3c7b082f34b1b32f4d1f712f5b359b2f3ab79c2f4788ec2f3cf7eb2f417f592f4717122f57b3192f2fdac52f306f212f3dea062f2386722ed9dd962f3a8a022f1b3d142eeec2b92f7c01442ef620332f29ecb32f3e80892f17413b2fdcca0e30e3962130a3af9a2f3785c82f2fb9ea2f30ccd92f17f5622f0cd7a52f651c862f0bd84b2f3d27af2f0636352f8fab1d2f7326a52f494be82f27cc5e2f22b6af2f1f47722f1ff99f2efc01722efb64292f46df982edacb512f1c3afb2f5c955a2f3d3ed72f28d3572f3a8e3d2f2d613a2f0caf552f539ee92eb56af02ef344882f1b65bc2f1a95702f3dc88e2f05685e2f454feb2f8598762ef004ad2f1249d32f6403072f34e40a2f1619f82f5bc9412f0c98812f2e5fb02f1307f02f1222442f10a31d2f0d53972f71ed7c2f4364c931530dd933026dad2f77db792f87c2e72f37854c2f40edd92f72b4a12f2d1ea02f189bfb2f235a762facf3282efdd2532f636abd2f0c209a2f033ba72f1449e72edaf9072f1ed10230842fa12f98bf582f42a9172fe2a6fa2f8534302f5f81072f4b6d222f1f64702f5520b62f333e252f47f5f32f332f442f37d3062f0a60d02f1acdc02f45dbac2f0123393019fc892704c945c10028044945c1004f044874240050043e1e06526701050600170000")

    # standard status packet
    p1 = bytes.fromhex("0012020f05010002000416766b34746d7a2034306d20454648572040206b6139710804ab891dc80506ef872678138e03081417480b804c216d0d0607b5a26000000a0403dcc4ff660101180062043fbbb29861006e04bfb33333630019001a001b006404466a600065044be85c605201102108414d55c40000000022002308c14d55c4000000002a0313c6802b0304f1a14d002d04c1387f3c68020b306c0506be762ed32f04c2f6dc743000550375736239003300530441000000540440e00000380024003e010140043f8ccccd4304c1700000410441a0000032002704424800002804453b8000140255f0160363cd6f2904413000002c002e04c2af3d954504c1e697764404426aee024604ab8916c847003f04c170000025002600310101100600000000a26d1106efcdcd2f138c1300150303fdff6901626a01196b010248004f0447bbbe8050043d730abf6701190600170000")
    # p1 = bytes.fromhex("00120246b9010002000416766b34746d7a2034306d20454648572040206b61397108045d909be00506ef872678138e03081417480b804c2b180d0607b5a26000000a0403dcc4ff660101180062043fbbb29861006e04bfb33333630019001a001b006404466a600065044be85c605201102108417144118000000022002308c1714411800000002a0313c6802b0304f1a14d002d04c1387f3c68020b306c0506be762ed32f04c2ff09f03000550375736239003300530441000000540440e00000380024003e003200270442c800002804459c400014022ee0160363cd6f2904413000002c002e04c2b239d84504c21c6c3844044248000046045d90981047003f04c170000025002600310101100600000000a26d1106ef6b8bc9138c1300150303fdff69017a6a01196b010248004f0448dd00e050043e8f0c776701190600170000")

    res = parsePacket(p1)
    print(f"Res: [{str(res).replace(',',",\n")}]")


if __name__ == "__main__":
    main()
