"""Compatibility wrapper for :mod:`ka9q_radio_rigctld.hamlibserver`."""
from ka9q_radio_rigctld.hamlibserver import *  # noqa: F401,F403

if __name__ == "__main__":
    from ka9q_radio_rigctld.hamlibserver import main
    raise SystemExit(main())
