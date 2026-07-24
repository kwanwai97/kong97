"""
Autonomous mode for Digital Twin.
Passive observation + auto-capture without manual logging.
Sources:
- Clipboard monitor (copy/paste decisions)
- Quick-capture hotkey listener (Windows)
- Drop folder watcher (drag files/text into watched dir)
- Browser bookmarklet injector
"""
from __future__ import annotations

import os
import re
import json
import time
import hashlib
import threading
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List, Optional

from backend import identity as identity_module
from backend.proactive_identity import ProactiveIdentity

BASE = Path(__file__).resolve().parents[2]
DROP_DIR = BASE / "data" / "autonomous_drop"
DROP_DIR.mkdir(parents=True, exist_ok=True)

# Decision-like phrases to auto-detect
_DECISION_RE = re.compile(
    r"(?:決定|決定了?|選定|揀咗|揀|我要|我會|我打算|我諗住|我決定|定咗|搞定|方案|choice|decide|choose|picking|going with)",
    re.IGNORECASE,
)
_REGRET_RE = re.compile(
    r"(?:後悔|嘥咗|失敗|錯過|搞錯|唔該|sorry|regret|mistake|failed|wrong|shouldn't)",
    re.IGNORECASE,
)


def _id() -> str:
    return hashlib.md5(str(time.time()).encode()).hexdigest()[:12]


def _now() -> str:
    return datetime.utcnow().isoformat() + "Z"


class AutonomousIngest:
    def __init__(self, user_id: str) -> None:
        self.user_id = user_id
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2)

    def _run(self) -> None:
        last_snapshot: Dict[str, float] = {}
        while not self._stop.is_set():
            try:
                self._scan_clipboard(last_snapshot)
                self._scan_drop_dir()
            except Exception:
                pass
            time.sleep(1)

    def _scan_clipboard(self, last_snapshot: Dict[str, float]) -> None:
        try:
            import tkinter  # lazy import, Windows only
            root = tkinter.Tk()
            root.withdraw()
            try:
                data = root.clipboard_get()
            except Exception:
                return
            finally:
                root.destroy()
            if not data or not isinstance(data, str):
                return
            data = data.strip()
            if len(data) < 5 or len(data) > 1000:
                return
            h = hash(data)
            ts = time.time()
            if last_snapshot.get("clipboard") == h:
                return
            last_snapshot["clipboard"] = h
            if _DECISION_RE.search(data):
                身份層 = identity_module.IdentityLayer()
                身份層.record_decision(
                    self.user_id,
                    topic="剪貼簿自動擷取",
                    choice=data[:120],
                    reasoning="autonomous: clipboard decision-like",
                    tags=["auto", "clipboard"],
                )
            if _REGRET_RE.search(data):
                身份層 = identity_module.IdentityLayer()
                身份層.append_daily_log(self.user_id, entries=[f"[clipboard] {data[:200]}"])
        except Exception:
            pass

    def _scan_drop_dir(self) -> None:
        files = sorted(DROP_DIR.glob("*.*"), key=lambda p: p.stat().st_mtime)
        for path in files:
            try:
                text = path.read_text(encoding="utf-8", errors="ignore").strip()
            except Exception:
                continue
            path.unlink(missing_ok=True)
            if not text:
                continue
            if _DECISION_RE.search(text):
                身份層 = identity_module.IdentityLayer()
                身份層.record_decision(
                    self.user_id,
                    topic="丟棄區自動擷取",
                    choice=text[:120],
                    reasoning="autonomous: drop file",
                    tags=["auto", "drop"],
                )

    def quick_capture(self, text: str, kind: str = "quick") -> Dict[str, Any]:
        text = (text or "").strip()
        if not text:
            return {"ok": False, "error": "empty"}
        if _DECISION_RE.search(text):
            entry = identity_module.IdentityLayer().record_decision(
                self.user_id,
                topic="快速捕捉",
                choice=text[:200],
                reasoning=f"autonomous: {kind}",
                tags=["auto", kind],
            )
            return {"ok": True, "type": "decision", "entry": entry}
        entry = identity_module.IdentityLayer().append_daily_log(self.user_id, entries=[text])
        return {"ok": True, "type": "log", "entry": entry}


# Singleton registry
_RUNNERS: Dict[str, AutonomousIngest] = {}
_LOCK = threading.Lock()


def get_runner(user_id: str) -> AutonomousIngest:
    with _LOCK:
        if user_id not in _RUNNERS:
            _RUNNERS[user_id] = AutonomousIngest(user_id)
        return _RUNNERS[user_id]


def stop_all() -> None:
    with _LOCK:
        for r in _RUNNERS.values():
            r.stop()
        _RUNNERS.clear()
