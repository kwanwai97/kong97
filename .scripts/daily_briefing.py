"""
Daily Briefing - 每日凌晨摘要產生器 (排程腳本入口)
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.explorer.briefing import build_briefing

OUT_DIR = ROOT / "data"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def main() -> None:
    briefing = build_briefing()
    today = datetime.utcnow().strftime("%Y%m%d")
    out = OUT_DIR / f"briefing_{today}.json"
    out.write_text(json.dumps(briefing, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"BRIEFING_OK {out}")


if __name__ == "__main__":
    main()
