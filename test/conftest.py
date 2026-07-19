from __future__ import annotations

import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]

for source_dir in (ROOT_DIR / "Backend", ROOT_DIR / "Frontend"):
    source_path = str(source_dir)
    if source_path not in sys.path:
        sys.path.insert(0, source_path)
