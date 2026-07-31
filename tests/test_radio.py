from ka9qradio import StatusType

from ka9q_radio_rigctld.radio import RadioSession


def test_latest_status_is_none_until_observed():
    session = RadioSession.__new__(RadioSession)
    session.ssrc = 9999405
    session.status = {}
    assert session.latest_status() is None


def test_latest_status_returns_selected_ssrc():
    session = RadioSession.__new__(RadioSession)
    session.ssrc = 9999405
    expected = {StatusType.OUTPUT_SSRC: 9999405}
    session.status = {9999405: expected}
    assert session.latest_status() == expected
