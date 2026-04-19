import os
"""
Feature gating per subscription plan.
All paid features are enforced here — not just in the system prompt.
"""
from __future__ import annotations
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Tuple

logger = logging.getLogger(__name__)

QUOTA_FILE = Path(os.getenv("DATA_DIR", "/tmp")) / "ai-agent-feature-quotas.json"

# What each plan is allowed to do
PLAN_FEATURES: Dict[str, Dict] = {
    "free": {
        "max_platforms": 2,
        "scheduling": False,
        "scheduled_posts_per_month": 0,
        "ab_testing": False,
        "competitor_analysis": False,
        "weekly_report": False,
        "smart_reply": False,
        "max_translation_languages": 0,  # no translation on Free
        "ai_content_quality": "basic",   # shorter, simpler posts
    },
    "basic": {
        "max_platforms": 2,
        "scheduling": False,
        "scheduled_posts_per_month": 0,
        "ab_testing": False,
        "competitor_analysis": False,
        "weekly_report": False,
        "smart_reply": False,
        "max_translation_languages": 0,  # no translation on Basic
        "ai_content_quality": "standard",
    },
    "pro": {
        "max_platforms": 4,
        "scheduling": True,
        "scheduled_posts_per_month": 20,
        "ab_testing": True,
        "competitor_analysis": False,
        "weekly_report": True,
        "smart_reply": True,
        "max_translation_languages": 3,
        "ai_content_quality": "standard",
    },
    "business": {
        "max_platforms": 6,
        "scheduling": True,
        "scheduled_posts_per_month": -1,  # unlimited
        "ab_testing": True,
        "competitor_analysis": True,
        "weekly_report": True,
        "smart_reply": True,
        "max_translation_languages": 6,
        "ai_content_quality": "standard",
    },
    # Bundle plans mirror their equivalent tiers
    "bundle_starter": {
        "max_platforms": 2,
        "scheduling": False,
        "scheduled_posts_per_month": 0,
        "ab_testing": False,
        "competitor_analysis": False,
        "weekly_report": False,
        "smart_reply": False,
        "max_translation_languages": 0,
        "ai_content_quality": "basic",
    },
    "bundle_pro": {
        "max_platforms": 4,
        "scheduling": True,
        "scheduled_posts_per_month": 20,
        "ab_testing": True,
        "competitor_analysis": False,
        "weekly_report": True,
        "smart_reply": True,
        "max_translation_languages": 3,
        "ai_content_quality": "standard",
    },
    "bundle_business": {
        "max_platforms": 6,
        "scheduling": True,
        "scheduled_posts_per_month": -1,
        "ab_testing": True,
        "competitor_analysis": True,
        "weekly_report": True,
        "smart_reply": True,
        "max_translation_languages": 6,
        "ai_content_quality": "standard",
    },
    # APPIFY internal admin/max plan — treated as Business (highest tier)
    "max": {
        "max_platforms": 10,
        "scheduling": True,
        "scheduled_posts_per_month": -1,
        "ab_testing": True,
        "competitor_analysis": True,
        "weekly_report": True,
        "smart_reply": True,
        "max_translation_languages": 10,
        "ai_content_quality": "standard",
    },
    # AIBuilder plan names that may be forwarded alongside advertising plan
    "starter": {
        "max_platforms": 2,
        "scheduling": False,
        "scheduled_posts_per_month": 0,
        "ab_testing": False,
        "competitor_analysis": False,
        "weekly_report": False,
        "smart_reply": False,
        "max_translation_languages": 0,
        "ai_content_quality": "basic",
    },
}

# Hebrew error messages returned to the agent when a feature is blocked
_UPGRADE_MSG = {
    "scheduling":           "פרסום מתוזמן זמין בתוכנית Pro ומעלה. [שדרג תוכנית]",
    "ab_testing":           "A/B Testing זמין בתוכנית Pro ומעלה. [שדרג תוכנית]",
    "competitor_analysis":  "ניתוח מתחרים זמין בתוכנית Business בלבד. [שדרג תוכנית]",
    "weekly_report":        "דוח שבועי זמין בתוכנית Pro ומעלה. [שדרג תוכנית]",
    "smart_reply":          "Smart Reply זמין בתוכנית Pro ומעלה. [שדרג תוכנית]",
    "max_platforms":        "הגעת למגבלת הפלטפורמות בתוכנית שלך. שדרג כדי לחבר יותר פלטפורמות.",
    "scheduled_quota":      "הגעת למכסת הפרסומים המתוזמנים החודשית ({used}/{limit}). שדרג לתוכנית Business לתזמון ללא הגבלה.",
    "translation_limit":    "תרגום ל-{count} שפות זמין בתוכנית גבוהה יותר. [שדרג תוכנית]",
}


def _get_features(plan: str) -> Dict:
    return PLAN_FEATURES.get(plan, PLAN_FEATURES["free"])


def _load_quotas() -> Dict:
    if QUOTA_FILE.exists():
        try:
            return json.loads(QUOTA_FILE.read_text())
        except Exception:
            pass
    return {}


def _save_quotas(data: Dict):
    QUOTA_FILE.write_text(json.dumps(data, default=str))


class FeatureGate:

    @classmethod
    def check(cls, plan: str, feature: str) -> Tuple[bool, str]:
        """
        Check if a boolean feature is available for this plan.
        Returns (allowed, error_message).
        """
        features = _get_features(plan)
        if features.get(feature, False):
            return True, ""
        return False, _UPGRADE_MSG.get(feature, f"פיצ'ר זה אינו זמין בתוכנית {plan}.")

    @classmethod
    def check_platform_limit(cls, plan: str, current_connected: int) -> Tuple[bool, str]:
        """Check if the user can connect another platform."""
        limit = _get_features(plan)["max_platforms"]
        if current_connected < limit:
            return True, ""
        return False, _UPGRADE_MSG["max_platforms"] + f" (מחוברות כעת: {current_connected}/{limit})"

    @classmethod
    def check_scheduling_quota(cls, session_id: str, plan: str) -> Tuple[bool, str]:
        """Check monthly scheduled post quota."""
        allowed, msg = cls.check(plan, "scheduling")
        if not allowed:
            return False, msg

        limit = _get_features(plan)["scheduled_posts_per_month"]
        if limit == -1:  # unlimited
            return True, ""

        data = _load_quotas()
        month_key = datetime.now().strftime("%Y-%m")
        used = data.get(session_id, {}).get("scheduled", {}).get(month_key, 0)

        if used >= limit:
            return False, _UPGRADE_MSG["scheduled_quota"].format(used=used, limit=limit)
        return True, ""

    @classmethod
    def record_scheduled_post(cls, session_id: str):
        """Increment the monthly scheduled post counter."""
        data = _load_quotas()
        month_key = datetime.now().strftime("%Y-%m")
        session = data.setdefault(session_id, {})
        scheduled = session.setdefault("scheduled", {})
        scheduled[month_key] = scheduled.get(month_key, 0) + 1
        _save_quotas(data)

    @classmethod
    def check_translation_languages(cls, plan: str, language_count: int) -> Tuple[bool, str]:
        """Check if the user can translate to this many languages."""
        limit = _get_features(plan)["max_translation_languages"]
        if language_count <= limit:
            return True, ""
        return False, _UPGRADE_MSG["translation_limit"].format(count=language_count)

    @classmethod
    def get_plan_summary(cls, plan: str) -> Dict:
        """Return a human-readable summary of what the plan includes."""
        f = _get_features(plan)
        sched = "ללא תזמון" if not f["scheduling"] else (
            "ללא הגבלה" if f["scheduled_posts_per_month"] == -1
            else f"{f['scheduled_posts_per_month']} פרסומים מתוזמנים/חודש"
        )
        return {
            "plan": plan,
            "max_platforms": f["max_platforms"],
            "scheduling": sched,
            "ab_testing": f["ab_testing"],
            "competitor_analysis": f["competitor_analysis"],
            "weekly_report": f["weekly_report"],
            "smart_reply": f["smart_reply"],
            "translation_languages": f["max_translation_languages"],
        }
