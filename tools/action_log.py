"""
Action audit log — records every significant agent action per session.
Used for compliance, debugging, and user transparency.
"""
from __future__ import annotations
import json
import logging
import os
from datetime import datetime
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

LOG_DIR = os.environ.get("ACTION_LOG_DIR", os.path.join(os.getenv("DATA_DIR", "/tmp"), "ai-agent-action-logs"))
MAX_ENTRIES = 500


def _ensure_dir() -> None:
    os.makedirs(LOG_DIR, exist_ok=True)


def _log_path(session_id: str) -> str:
    return os.path.join(LOG_DIR, f"{session_id}.json")


def log_action(
    session_id: str,
    action_type: str,
    description: str,
    details: Optional[Dict[str, Any]] = None,
    status: str = "success",
) -> Dict[str, Any]:
    """
    Record a single action in the session audit log.

    action_type examples:
      post_published, post_scheduled, post_cancelled,
      profile_saved, campaign_created, report_generated,
      follower_added, comment_posted, approval_requested
    """
    _ensure_dir()
    path = _log_path(session_id)

    entry = {
        "timestamp": datetime.now().isoformat(),
        "action_type": action_type,
        "description": description,
        "details": details or {},
        "status": status,
    }

    try:
        existing: List[Dict] = []
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                existing = json.load(f)

        existing.append(entry)
        # Keep only the most recent MAX_ENTRIES
        if len(existing) > MAX_ENTRIES:
            existing = existing[-MAX_ENTRIES:]

        with open(path, "w", encoding="utf-8") as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)

        logger.info(f"[audit][{session_id}] {action_type}: {description}")
    except Exception as e:
        logger.error(f"Failed to write action log: {e}")

    return {
        "logged": True,
        "timestamp": entry["timestamp"],
        "action_type": action_type,
        "status": status,
    }


def get_action_log(session_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Return the most recent `limit` actions for a session."""
    path = _log_path(session_id)
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            actions: List[Dict] = json.load(f)
        return actions[-limit:]
    except Exception:
        return []
