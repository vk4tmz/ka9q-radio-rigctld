from pathlib import Path


def test_virtualcard_pcmrecord_stream_opts_into_reacquisition():
    helper = (Path(__file__).resolve().parents[1] / "src" / "ka9q_radio_rigctld" / "resources" / "pcmrecord_to_virtualcard.sh").read_text(encoding="utf-8")
    assert 'pcmrecord -c -r --reacquire -S "${SSRC}" "${MCAST_GROUP}"' in helper
