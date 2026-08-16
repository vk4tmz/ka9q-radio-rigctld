from pathlib import Path


def _scripts():
    root = Path(__file__).resolve().parents[1]
    return [
        root / 'scripts/virtual_vfo_streamer.sh',
        root / 'src/ka9q_radio_rigctld/resources/virtual_vfo_streamer.sh',
    ]


def test_stop_can_recover_live_streamer_by_configured_ssrc():
    for path in _scripts():
        text = path.read_text(encoding='utf-8')
        assert 'find_streamer_pid_by_ssrc()' in text
        assert 'Recovered live streamer VC=${VC} SSRC=${SSRC} PID=${recovered_pid}' in text
        assert 'CURRENT_SSRC=$BASE_SSRC' in text
        assert 'No live streamer found for VC=${VC} SSRC=${SSRC}' in text


def test_recovered_pid_is_validated_against_ssrc_before_kill():
    for path in _scripts():
        text = path.read_text(encoding='utf-8')
        assert 'does not match configured SSRC ${SSRC}, leaving process untouched' in text
        assert 'stop_streamer_pid "$VC" "$SSRC" "$recovered_pid"' in text
