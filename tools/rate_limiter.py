"""
Rate limiter - prevents excessive Claude API usage per session.
Limits: 20 messages/hour, 100 messages/day per session.
"""
from __future__ import annotations
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Tuple

logger = logging.getLogger(__name__)

LIMITS_FILE = Path("/tmp/ai-agent-rate-limits.json")

# Limits per session
HOURLY_LIMIT = 20   # max messages per hour
DAILY_LIMIT = 100   # max messages per day


class RateLimiter:

    @classmethod
    def _load(cls) -> Dict:
        if LIMITS_FILE.exists():
            try:
                return json.loads(LIMITS_FILE.read_text())
            except Exception:
                pass
        return {}

    @classmethod
    def _save(cls, data: Dict):
        LIMITS_FILE.write_text(json.dumps(data, default=str))

    @classmethod
    def check(cls, session_id: str) -> Tuple[bool, str]:
        """
        Check if session is within rate limits.
        Returns (allowed, reason_if_blocked).
        """
        data = cls._load()
        now = datetime.now()
        session = data.get(session_id, {"messages": []})

        # Clean old entries
        messages = session.get("messages", [])
        messages = [
            m for m in messages
            if datetime.fromisoformat(m) > now - timedelta(days=1)
        ]

        # Check daily limit
        if len(messages) >= DAILY_LIMIT:
            return False, f"הגעת למגבלה היומית ({DAILY_LIMIT} הודעות). נסה מחר."

        # Check hourly limit
        last_hour = [m for m in messages if datetime.fromisoformat(m) > now - timedelta(hours=1)]
        if len(last_hour) >= HOURLY_LIMIT:
            reset_in = 60 - (now - datetime.fromisoformat(last_hour[0])).seconds // 60
            return False, f"יותר מדי הודעות בשעה האחרונה ({HOURLY_LIMIT} מקסימום). נסה שוב בעוד {reset_in} דקות."

        return True, ""

    @classmethod
    def record(cls, session_id: str):
        """Record a message for rate limiting."""
        data = cls._load()
        now = datetime.now()
        session = data.get(session_id, {"messages": []})
        messages = session.get("messages", [])

        # Clean old (keep last 24h only)
        messages = [
            m for m in messages
            if datetime.fromisoformat(m) > now - timedelta(days=1)
        ]
        messages.append(now.isoformat())
        data[session_id] = {"messages": messages}
        cls._save(data)

    @classmethod
    def get_usage(cls, session_id: str) -> Dict:
        """Get current usage stats for a session."""
        data = cls._load()
        now = datetime.now()
        session = data.get(session_id, {"messages": []})
        messages = session.get("messages", [])
        messages = [m for m in messages if datetime.fromisoformat(m) > now - timedelta(days=1)]
        last_hour = [m for m in messages if datetime.fromisoformat(m) > now - timedelta(hours=1)]

        return {
            "hourly": {"used": len(last_hour), "limit": HOURLY_LIMIT, "remaining": HOURLY_LIMIT - len(last_hour)},
            "daily": {"used": len(messages), "limit": DAILY_LIMIT, "remaining": DAILY_LIMIT - len(messages)},
        }
