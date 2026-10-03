#!/usr/bin/env python3
"""python tools/setpin.py 123456  -> sets the 6-digit presenter PIN (takes effect immediately)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import serve
if len(sys.argv) != 2:
    sys.exit(__doc__)
serve.set_pin(sys.argv[1]); print("PIN updated")
