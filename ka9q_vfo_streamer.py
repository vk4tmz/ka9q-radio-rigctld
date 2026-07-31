"""Compatibility wrapper for :mod:`ka9q_radio_rigctld.ka9q_vfo_streamer`."""
from ka9q_radio_rigctld.ka9q_vfo_streamer import *  # noqa: F401,F403

if __name__ == "__main__":
    from ka9q_radio_rigctld.ka9q_vfo_streamer import main
    raise SystemExit(main())
