from __future__ import annotations

import os
from pathlib import Path
import sys


def main() -> int:
    script = Path(__file__).resolve().parent / "resources" / "virtual_vfo_streamer.sh"
    if not script.is_file():
        print(f"ERROR: bundled group controller not found: {script}", file=sys.stderr)
        return 1
    os.execv("/usr/bin/env", ["env", "bash", str(script), *sys.argv[1:]])
    return 0
