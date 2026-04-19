"""
Scheduled posting engine - posts content at optimal times automatically.
Uses APScheduler for job management.
All times are stored in UTC internally; displayed in Israel time (Asia/Jerusalem).
"""
from __future__ import annotations
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional, Callable
from pathlib import Path
import uuid

try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo  # type: ignore

ISRAEL_TZ = ZoneInfo("Asia/Jerusalem")


def _now_utc() -> datetime:
    return datetime.now(tz=timezone.utc)


def _now_israel() -> datetime:
    return datetime.now(tz=ISRAEL_TZ)


def _parse_scheduled_for(scheduled_for: str) -> datetime:
    """
    Parse a scheduled_for string into an aware UTC datetime.
    Input may be ISO format with or without timezone.
    Assumed to be Israel time if no timezone info present.
    """
    try:
        dt = datetime.fromisoformat(scheduled_for)
        if dt.tzinfo is None:
            # Treat naive datetime as Israel local time
            dt = dt.replace(tzinfo=ISRAEL_TZ)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def _format_israel_time(dt: datetime) -> str:
    """Format a datetime as Israel local time string for display."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    israel_dt = dt.astimezone(ISRAEL_TZ)
    return israel_dt.strftime("%A %d/%m/%Y בשעה %H:%M")

logger = logging.getLogger(__name__)

JOBS_FILE = Path("/tmp/ai-agent-scheduled-jobs.json")

# Optimal posting times per platform (Israel timezone)
OPTIMAL_TIMES = {
    "facebook":  [{"day": "tue", "hour": 9}, {"day": "wed", "hour": 19}, {"day": "thu", "hour": 10}],
    "instagram": [{"day": "mon", "hour": 8}, {"day": "tue", "hour": 17}, {"day": "fri", "hour": 21}],
    "linkedin":  [{"day": "tue", "hour": 8}, {"day": "wed", "hour": 12}, {"day": "thu", "hour": 7}],
    "twitter":   [{"day": "mon", "hour": 9}, {"day": "wed", "hour": 15}, {"day": "fri", "hour": 10}],
    "tiktok":    [{"day": "tue", "hour": 19}, {"day": "thu", "hour": 21}, {"day": "sat", "hour": 20}],
    "youtube":   [{"day": "fri", "hour": 14}, {"day": "sat", "hour": 12}, {"day": "sun", "hour": 16}],
}

DAY_MAP = {"mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6}


class ScheduledPost:
    def __init__(
        self,
        platforms: List[str],
        content: str,
        scheduled_for: datetime,
        session_id: str,
        hashtags: List[str] = None,
        media_urls: List[str] = None,
        job_id: str = None,
    ):
        self.job_id = job_id or str(uuid.uuid4())[:8]
        self.platforms = platforms
        self.content = content
        self.scheduled_for = scheduled_for
        self.session_id = session_id
        self.hashtags = hashtags or []
        self.media_urls = media_urls or []
        self.status = "pending"  # pending | published | failed
        self.created_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "platforms": self.platforms,
            "content": self.content,
            "scheduled_for": self.scheduled_for.isoformat(),
            "session_id": self.session_id,
            "hashtags": self.hashtags,
            "media_urls": self.media_urls,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
        }


class PostScheduler:
    """Manages scheduled posts."""

    @classmethod
    def _load_jobs(cls) -> List[Dict]:
        if JOBS_FILE.exists():
            try:
                return json.loads(JOBS_FILE.read_text())
            except Exception:
                pass
        return []

    @classmethod
    def _save_jobs(cls, jobs: List[Dict]):
        JOBS_FILE.write_text(json.dumps(jobs, indent=2, default=str))

    @classmethod
    def add_job(cls, post: ScheduledPost) -> str:
        jobs = cls._load_jobs()
        jobs.append(post.to_dict())
        cls._save_jobs(jobs)
        logger.info(f"Scheduled post {post.job_id} for {post.scheduled_for}")
        return post.job_id

    @classmethod
    def get_pending_jobs(cls, session_id: str = None) -> List[Dict]:
        jobs = cls._load_jobs()
        now = datetime.now()
        pending = [j for j in jobs if j["status"] == "pending"]
        if session_id:
            pending = [j for j in pending if j["session_id"] == session_id]
        return pending

    @classmethod
    def get_due_jobs(cls) -> List[Dict]:
        """Get jobs that are due to be published now."""
        jobs = cls._load_jobs()
        now = _now_utc()
        due = []
        for j in jobs:
            if j["status"] != "pending":
                continue
            try:
                sched = datetime.fromisoformat(j["scheduled_for"])
                if sched.tzinfo is None:
                    sched = sched.replace(tzinfo=timezone.utc)
                if sched <= now:
                    due.append(j)
            except Exception:
                pass
        return due

    @classmethod
    def mark_published(cls, job_id: str):
        jobs = cls._load_jobs()
        for j in jobs:
            if j["job_id"] == job_id:
                j["status"] = "published"
                j["published_at"] = datetime.now().isoformat()
        cls._save_jobs(jobs)

    @classmethod
    def mark_failed(cls, job_id: str, error: str = ""):
        jobs = cls._load_jobs()
        for j in jobs:
            if j["job_id"] == job_id:
                j["status"] = "failed"
                j["error"] = error
                j["failed_at"] = datetime.now().isoformat()
        cls._save_jobs(jobs)

    @classmethod
    def cancel_job(cls, job_id: str) -> bool:
        jobs = cls._load_jobs()
        for j in jobs:
            if j["job_id"] == job_id and j["status"] == "pending":
                j["status"] = "cancelled"
                cls._save_jobs(jobs)
                return True
        return False

    @classmethod
    def get_next_optimal_time(cls, platform: str, days_ahead: int = 7) -> datetime:
        """Find the next optimal posting time for a platform (returned as UTC)."""
        times = OPTIMAL_TIMES.get(platform, [{"day": "mon", "hour": 9}])
        now_il = _now_israel()
        best = None

        for slot in times:
            target_weekday = DAY_MAP.get(slot["day"], 0)
            days_until = (target_weekday - now_il.weekday()) % 7
            if days_until == 0 and now_il.hour >= slot["hour"]:
                days_until = 7

            candidate_il = (now_il + timedelta(days=days_until)).replace(
                hour=slot["hour"], minute=0, second=0, microsecond=0,
                tzinfo=ISRAEL_TZ,
            )
            if best is None or candidate_il < best:
                best = candidate_il

        result = best or (now_il + timedelta(hours=24)).replace(tzinfo=ISRAEL_TZ)
        return result.astimezone(timezone.utc)

    @classmethod
    def get_all_jobs_summary(cls, session_id: str) -> Dict[str, Any]:
        jobs = cls._load_jobs()
        if session_id:
            jobs = [j for j in jobs if j.get("session_id") == session_id]

        # Convert scheduled_for to Israel time for display
        display_jobs = []
        for j in sorted(jobs, key=lambda x: x["scheduled_for"])[:20]:
            d = dict(j)
            try:
                dt = datetime.fromisoformat(d["scheduled_for"])
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                d["scheduled_for_display"] = _format_israel_time(dt)
            except Exception:
                d["scheduled_for_display"] = d["scheduled_for"]
            display_jobs.append(d)

        return {
            "total": len(jobs),
            "pending": len([j for j in jobs if j["status"] == "pending"]),
            "published": len([j for j in jobs if j["status"] == "published"]),
            "cancelled": len([j for j in jobs if j["status"] == "cancelled"]),
            "jobs": display_jobs,
        }


def schedule_post(
    platforms: List[str],
    content: str,
    session_id: str,
    scheduled_for: str = "optimal",
    hashtags: List[str] = None,
    media_urls: List[str] = None,
) -> Dict[str, Any]:
    """Schedule a post for future publishing."""
    results = {}

    for platform in platforms:
        if scheduled_for == "optimal":
            post_time = PostScheduler.get_next_optimal_time(platform)
        else:
            post_time = _parse_scheduled_for(scheduled_for)
            if post_time is None:
                post_time = PostScheduler.get_next_optimal_time(platform)

        post = ScheduledPost(
            platforms=[platform],
            content=content,
            scheduled_for=post_time,
            session_id=session_id,
            hashtags=hashtags or [],
            media_urls=media_urls or [],
        )
        job_id = PostScheduler.add_job(post)
        results[platform] = {
            "job_id": job_id,
            "scheduled_for": _format_israel_time(post_time),
            "status": "scheduled",
        }

    return {
        "success": True,
        "scheduled_posts": results,
        "total_scheduled": len(results),
        "message": f"תוזמנו {len(results)} פוסטים בזמנים האופטימליים",
    }


def list_scheduled_posts(session_id: str) -> Dict[str, Any]:
    """List all scheduled posts for a session."""
    summary = PostScheduler.get_all_jobs_summary(session_id)
    return summary


def cancel_scheduled_post(job_id: str) -> Dict[str, Any]:
    """Cancel a scheduled post."""
    success = PostScheduler.cancel_job(job_id)
    return {
        "success": success,
        "job_id": job_id,
        "message": "הפוסט בוטל בהצלחה" if success else "לא נמצא פוסט עם מזהה זה",
    }
