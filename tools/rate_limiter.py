"""
Rate limiter - prevents excessive Claude API usage per session.
Limits are based on the user's marketing plan.
"""
from __future__ import annotations
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Tuple

logger = logging.getLogger(__name__)

LIMITS_FILE = Path("/tmp/ai-agent-rate-limits.json")

# Limits per plan (hourly, daily)
PLAN_LIMITS: Dict[str, Dict[str, int]] = {
    "free":           {"hourly": 5,  "daily": 10},
    "basic":          {"hourly": 15, "daily": 30},
    "pro":            {"hourly": 25, "daily": 100},
    "business":       {"hourly": 50, "daily": 200},
    "bundle_starter": {"hourly": 15, "daily": 20},
    "bundle_pro":     {"hourly": 25, "daily": 75},
    "bundle_business":{"hourly": 50, "daily": 200},
}

# Fallback defaults (free plan)
HOURLY_LIMIT = 5
DAILY_LIMIT = 10


def _get_limits(plan: str) -> Dict[str, int]:
    return PLAN_LIMITS.get(plan, PLAN_LIMITS["free"])


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
    def check(cls, session_id: str, plan: str = "free") -> Tuple[bool, str]:
        """
        Check if session is within rate limits for the given plan.
        Returns (allowed, reason_if_blocked).
        """
        limits = _get_limits(plan)
        hourly_limit = limits["hourly"]
        daily_limit = limits["daily"]

        data = cls._load()
        now = datetime.now()
        session = data.get(session_id, {"messages": []})

        messages = session.get("messages", [])
        messages = [
            m for m in messages
            if datetime.fromisoformat(m) > now - timedelta(days=1)
        ]

        if len(messages) >= daily_limit:
            return False, f"הגעת למגבלה היומית ({daily_limit} הודעות). שדרג תוכנית לקבלת יותר הודעות."

        last_hour = [m for m in messages if datetime.fromisoformat(m) > now - timedelta(hours=1)]
        if len(last_hour) >= hourly_limit:
            reset_in = 60 - (now - datetime.fromisoformat(last_hour[0])).seconds // 60
            return False, f"יותר מדי הודעות בשעה האחרונה ({hourly_limit} מקסימום). נסה שוב בעוד {reset_in} דקות."

        return True, ""

    @classmethod
    def record(cls, session_id: str):
        """Record a message for rate limiting."""
        data = cls._load()
        now = datetime.now()
        session = data.get(session_id, {"messages": []})
        messages = session.get("messages", [])

        messages = [
            m for m in messages
            if datetime.fromisoformat(m) > now - timedelta(days=1)
        ]
        messages.append(now.isoformat())
        data[session_id] = {"messages": messages}
        cls._save(data)

    @classmethod
    def get_usage(cls, session_id: str, plan: str = "free") -> Dict:
        """Get current usage stats for a session."""
        limits = _get_limits(plan)
        hourly_limit = limits["hourly"]
        daily_limit = limits["daily"]

        data = cls._load()
        now = datetime.now()
        session = data.get(session_id, {"messages": []})
        messages = session.get("messages", [])
        messages = [m for m in messages if datetime.fromisoformat(m) > now - timedelta(days=1)]
        last_hour = [m for m in messages if datetime.fromisoformat(m) > now - timedelta(hours=1)]

        return {
            "plan": plan,
            "hourly": {"used": len(last_hour), "limit": hourly_limit, "remaining": hourly_limit - len(last_hour)},
            "daily": {"used": len(messages), "limit": daily_limit, "remaining": daily_limit - len(messages)},
        }
