"""
Notification system - stores in-app notifications per session.
Frontend polls /api/notifications/{session_id} to show them.
"""
from __future__ import annotations
import os
import json
import uuid
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict

logger = logging.getLogger(__name__)

NOTIF_DIR = Path(os.getenv("DATA_DIR", "/tmp")) / "ai-agent-notifications"
NOTIF_DIR.mkdir(parents=True, exist_ok=True)


class NotificationManager:

    @classmethod
    def _path(cls, session_id: str) -> Path:
        safe = session_id.replace("/", "_")[:64]
        return NOTIF_DIR / f"{safe}.json"

    @classmethod
    def _load(cls, session_id: str) -> List[Dict]:
        path = cls._path(session_id)
        if path.exists():
            try:
                return json.loads(path.read_text())
            except Exception:
                pass
        return []

    @classmethod
    def _save(cls, session_id: str, notifs: List[Dict]):
        cls._path(session_id).write_text(json.dumps(notifs[-50:], default=str))  # keep last 50

    @classmethod
    def add(cls, session_id: str, title: str, message: str, type: str = "info"):
        """Add a notification. type: info | success | warning | error"""
        notifs = cls._load(session_id)
        notifs.append({
            "id": str(uuid.uuid4())[:8],
            "title": title,
            "message": message,
            "type": type,
            "read": False,
            "created_at": datetime.now().isoformat(),
        })
        cls._save(session_id, notifs)
        logger.info(f"Notification for {session_id}: {title}")

    @classmethod
    def get_unread(cls, session_id: str) -> List[Dict]:
        return [n for n in cls._load(session_id) if not n["read"]]

    @classmethod
    def mark_all_read(cls, session_id: str):
        notifs = cls._load(session_id)
        for n in notifs:
            n["read"] = True
        cls._save(session_id, notifs)

    @classmethod
    def get_all(cls, session_id: str) -> List[Dict]:
        return sorted(cls._load(session_id), key=lambda x: x["created_at"], reverse=True)
