import os
"""
Persistent token store — saves OAuth tokens per session to disk
so the background job runner can publish scheduled posts even
when no active chat session is running.
"""
from __future__ import annotations
import json
import logging
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)

TOKEN_DIR = Path(os.getenv("DATA_DIR", "/tmp")) / "ai-agent-session-tokens"
TOKEN_DIR.mkdir(parents=True, exist_ok=True)


def save_tokens(session_id: str, tokens: Dict[str, str], page_ids: Dict[str, str] = None):
    """Persist OAuth tokens for a session to disk."""
    path = TOKEN_DIR / f"{session_id}.json"
    data = {
        "session_id": session_id,
        "tokens": tokens,
        "page_ids": page_ids or {},
    }
    path.write_text(json.dumps(data))


def load_tokens(session_id: str) -> Optional[Dict]:
    """Load persisted tokens for a session. Returns None if not found."""
    path = TOKEN_DIR / f"{session_id}.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except Exception as e:
        logger.error(f"Failed to load tokens for session {session_id}: {e}")
        return None
