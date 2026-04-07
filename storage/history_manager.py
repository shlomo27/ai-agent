"""
Conversation history manager - persists chat history per session to disk.
Survives server restarts.
"""
from __future__ import annotations
import json
import logging
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

HISTORY_DIR = Path("/tmp/ai-agent-history")
HISTORY_DIR.mkdir(parents=True, exist_ok=True)
MAX_HISTORY_MESSAGES = 40  # keep last 40 messages to avoid token overflow


class HistoryManager:

    @classmethod
    def _path(cls, session_id: str) -> Path:
        safe = session_id.replace("/", "_").replace("\\", "_")[:64]
        return HISTORY_DIR / f"{safe}.json"

    @classmethod
    def load(cls, session_id: str) -> List[Dict[str, Any]]:
        path = cls._path(session_id)
        if path.exists():
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except Exception as e:
                logger.error(f"Failed to load history {session_id}: {e}")
        return []

    @classmethod
    def save(cls, session_id: str, history: List[Dict[str, Any]]):
        try:
            # Keep only last N messages to avoid token overflow
            trimmed = history[-MAX_HISTORY_MESSAGES:]
            # Only save text messages (not thinking blocks) for persistence
            saveable = [
                msg for msg in trimmed
                if isinstance(msg.get("content"), str)
            ]
            cls._path(session_id).write_text(
                json.dumps(saveable, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
        except Exception as e:
            logger.error(f"Failed to save history {session_id}: {e}")

    @classmethod
    def clear(cls, session_id: str):
        path = cls._path(session_id)
        if path.exists():
            path.unlink()
