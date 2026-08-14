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


def test_radio_session_uses_configured_network_values_without_env(monkeypatch):
    captured = {}

    class FakeClient:
        def __init__(self, radio, *, interface=None):
            captured["client"] = (radio, interface)

    class FakeListener:
        def __init__(self, radio, *, interface=None, timeout=None):
            captured["listener"] = (radio, interface, timeout)

    monkeypatch.delenv("KA9Q_MULTICAST_INTERFACE", raising=False)
    monkeypatch.delenv("KA9Q_STATUS_HOSTIP", raising=False)
    monkeypatch.setattr("ka9q_radio_rigctld.radio.Ka9qRadioClient", FakeClient)
    monkeypatch.setattr("ka9q_radio_rigctld.radio.StatusListener", FakeListener)

    session = RadioSession(
        "hf.local", 9999991,
        multicast_interface="192.0.2.10",
        status_interface="192.0.2.11",
    )
    assert session.multicast_interface == "192.0.2.10"
    assert session.status_interface == "192.0.2.11"
    assert captured["client"] == ("hf.local", "192.0.2.10")
    assert captured["listener"][:2] == ("hf.local", "192.0.2.11")


def test_radio_session_env_overrides_configured_network_values(monkeypatch, caplog):
    captured = {}

    class FakeClient:
        def __init__(self, radio, *, interface=None):
            captured["client"] = interface

    class FakeListener:
        def __init__(self, radio, *, interface=None, timeout=None):
            captured["listener"] = interface

    monkeypatch.setenv("KA9Q_MULTICAST_INTERFACE", "192.0.2.20")
    monkeypatch.setenv("KA9Q_STATUS_HOSTIP", "192.0.2.21")
    monkeypatch.setattr("ka9q_radio_rigctld.radio.Ka9qRadioClient", FakeClient)
    monkeypatch.setattr("ka9q_radio_rigctld.radio.StatusListener", FakeListener)
    caplog.set_level("INFO")

    session = RadioSession(
        "hf.local", 9999991,
        multicast_interface="192.0.2.10",
        status_interface="192.0.2.11",
    )
    assert session.multicast_interface == "192.0.2.20"
    assert session.status_interface == "192.0.2.21"
    assert captured["client"] == "192.0.2.20"
    assert captured["listener"] == "192.0.2.21"
    assert "KA9Q_MULTICAST_INTERFACE override" in caplog.text
    assert "KA9Q_STATUS_HOSTIP override" in caplog.text


def test_radio_session_status_inherits_generic_multicast_env(monkeypatch):
    captured = {}

    class FakeClient:
        def __init__(self, radio, *, interface=None):
            captured["client"] = interface

    class FakeListener:
        def __init__(self, radio, *, interface=None, timeout=None):
            captured["listener"] = interface

    monkeypatch.setenv("KA9Q_MULTICAST_INTERFACE", "192.0.2.30")
    monkeypatch.delenv("KA9Q_STATUS_HOSTIP", raising=False)
    monkeypatch.setattr("ka9q_radio_rigctld.radio.Ka9qRadioClient", FakeClient)
    monkeypatch.setattr("ka9q_radio_rigctld.radio.StatusListener", FakeListener)

    RadioSession("hf.local", 9999991, status_interface="192.0.2.11")
    assert captured["client"] == "192.0.2.30"
    assert captured["listener"] == "192.0.2.30"
