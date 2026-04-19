"""
Background job runner - checks scheduled posts every minute and publishes them.
Runs as a background asyncio task alongside the FastAPI server.
"""
from __future__ import annotations
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any

from tools.scheduler import PostScheduler
from tools.notifications import NotificationManager

logger = logging.getLogger(__name__)

_running = False


async def run_scheduled_posts():
    """
    Check for due scheduled posts and publish them.
    Called every 60 seconds by the background loop.
    """
    due_jobs = PostScheduler.get_due_jobs()
    if not due_jobs:
        return

    logger.info(f"Job runner: found {len(due_jobs)} due posts")

    for job in due_jobs:
        try:
            await _publish_job(job)
            PostScheduler.mark_published(job["job_id"])
            logger.info(f"✅ Published scheduled post {job['job_id']} to {job['platforms']}")
            # Send success notification
            platforms_str = ", ".join(job["platforms"])
            NotificationManager.add(
                session_id=job["session_id"],
                title="✅ פוסט פורסם בהצלחה!",
                message=f"הפוסט שתוזמן פורסם ל: {platforms_str}",
                type="success",
            )
        except Exception as e:
            logger.error(f"❌ Failed to publish job {job['job_id']}: {e}")
            PostScheduler.mark_failed(job["job_id"], str(e))
            NotificationManager.add(
                session_id=job["session_id"],
                title="❌ פרסום נכשל",
                message=f"הפוסט המתוזמן לא הצליח לפרסם: {str(e)[:100]}",
                type="error",
            )


async def _publish_job(job: Dict[str, Any]):
    """Publish a single scheduled job to its platforms."""
    import tools.social_tools as social_tools
    from tools.token_store import load_tokens
    from platforms.facebook import FacebookPlatform
    from platforms.instagram import InstagramPlatform
    from platforms.twitter import TwitterPlatform
    from platforms.linkedin import LinkedInPlatform
    from platforms.youtube import YoutubePlatform
    from platforms.tiktok import TikTokPlatform
    from platforms.reddit import RedditPlatform

    # Re-register platforms with stored tokens so job fires even without active session
    session_id = job.get("session_id", "")
    stored = load_tokens(session_id) if session_id else None
    if stored:
        tokens = stored.get("tokens", {})
        page_ids = stored.get("page_ids", {})
        _cls = {
            "facebook": lambda t, p: FacebookPlatform(access_token=t, page_id=p),
            "instagram": lambda t, _: InstagramPlatform(access_token=t),
            "twitter": lambda t, _: TwitterPlatform(access_token=t),
            "linkedin": lambda t, _: LinkedInPlatform(access_token=t),
            "youtube": lambda t, _: YoutubePlatform(access_token=t),
            "tiktok": lambda t, _: TikTokPlatform(access_token=t),
            "reddit": lambda t, _: RedditPlatform(access_token=t),
        }
        for platform_name in job["platforms"]:
            token = tokens.get(platform_name)
            if token and platform_name in _cls:
                platform = _cls[platform_name](token, page_ids.get(platform_name))
                social_tools.register_platform(platform_name, platform)
                logger.info(f"Job runner: re-registered {platform_name} for session {session_id}")
    else:
        logger.warning(f"Job runner: no stored tokens for session {session_id}")

    result = await social_tools.post_content(
        platforms=job["platforms"],
        content=job["content"],
        hashtags=job.get("hashtags", []),
        media_urls=job.get("media_urls", []),
    )
    return result


async def background_loop():
    """Main background loop - runs every 60 seconds."""
    global _running
    _running = True
    logger.info("🔄 Background job runner started")

    while _running:
        try:
            await run_scheduled_posts()
        except Exception as e:
            logger.error(f"Job runner error: {e}")
        await asyncio.sleep(60)


def start_background_runner():
    """Start the background runner as an asyncio task."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.get_event_loop()
    task = loop.create_task(background_loop())
    logger.info("Background job runner task created")
    return task


def stop_background_runner():
    global _running
    _running = False
    logger.info("Background job runner stopped")
