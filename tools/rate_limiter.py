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

_HE_DAYS = ["שני", "שלישי", "רביעי", "חמישי", "שישי", "שבת", "ראשון"]


def _format_reset_time(reset_at: datetime, now: datetime, language: str) -> str:
    """Return a human-friendly reset time string like 'tomorrow at 07:54' or 'מחר ב-07:54'."""
    reset_date = reset_at.date()
    today = now.date()
    time_str = reset_at.strftime("%H:%M")
    if reset_date == today:
        return f"today at {time_str}" if language == "en" else f"היום ב-{time_str}"
    if reset_date == today + timedelta(days=1):
        return f"tomorrow at {time_str}" if language == "en" else f"מחר ב-{time_str}"
    if language == "en":
        return f"on {reset_at.strftime('%A')} at {time_str}"
    return f"ביום {_HE_DAYS[reset_at.weekday()]} ב-{time_str}"

logger = logging.getLogger(__name__)

LIMITS_FILE = Path("/tmp/ai-agent-rate-limits.json")

# Limits per plan (hourly, daily)
PLAN_LIMITS: Dict[str, Dict[str, int]] = {
    "free":           {"hourly": 10, "daily": 10},
    "basic":          {"hourly": 30, "daily": 30},
    "pro":            {"hourly": 50, "daily": 100},
    "business":       {"hourly": 100,"daily": 200},
    "bundle_starter": {"hourly": 20, "daily": 20},
    "bundle_pro":     {"hourly": 50, "daily": 75},
    "bundle_business":{"hourly": 100,"daily": 200},
    "max":            {"hourly": 500,"daily": 1000},  # APPIFY admin/max plan
    "starter":        {"hourly": 20, "daily": 20},    # AIBuilder Starter
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
    def check(cls, session_id: str, plan: str = "free", language: str = "he") -> Tuple[bool, str]:
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
            oldest = datetime.fromisoformat(messages[0])
            reset_at = oldest + timedelta(days=1)
            when = _format_reset_time(reset_at, now, language)
            if language == "en":
                return False, f"You've reached the daily limit ({daily_limit} messages). Quota resets {when}."
            return False, f"הגעת למגבלה היומית ({daily_limit} הודעות). המכסה תתחדש {when}."

        last_hour = [m for m in messages if datetime.fromisoformat(m) > now - timedelta(hours=1)]
        if len(last_hour) >= hourly_limit:
            oldest_hour = datetime.fromisoformat(last_hour[0])
            reset_at = oldest_hour + timedelta(hours=1)
            time_str = reset_at.strftime("%H:%M")
            if language == "en":
                return False, f"Too many messages in the last hour ({hourly_limit} max). Quota resets at {time_str}."
            return False, f"יותר מדי הודעות בשעה האחרונה ({hourly_limit} מקסימום). המכסה תתחדש ב-{time_str}."

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
