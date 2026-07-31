from ka9q_radio_rigctld.hamlibserver import build_parser as rig_parser
from ka9q_radio_rigctld.ka9q_vfo_streamer import build_parser as vfo_parser


def test_vfo_parser_preserves_existing_arguments():
    args = vfo_parser().parse_args(["hf.local", "9999405", "5590000", "iq", "-ar", "12000", "-ad", "sink", "--port", "4591"])
    assert args.ssrc == 9999405
    assert args.freq_hz == 5590000
    assert args.audio_device == "sink"
    assert args.port == 4591


def test_rigctld_parser_defaults():
    args = rig_parser().parse_args([])
    assert args.mcast_group == "hf.local"
    assert args.port == 4575
