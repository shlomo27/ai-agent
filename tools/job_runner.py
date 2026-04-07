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
        except Exception as e:
            logger.error(f"❌ Failed to publish job {job['job_id']}: {e}")
            PostScheduler.mark_failed(job["job_id"], str(e))


async def _publish_job(job: Dict[str, Any]):
    """Publish a single scheduled job to its platforms."""
    import tools.social_tools as social_tools

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
    loop = asyncio.get_event_loop()
    task = loop.create_task(background_loop())
    logger.info("Background job runner task created")
    return task


def stop_background_runner():
    global _running
    _running = False
    logger.info("Background job runner stopped")
