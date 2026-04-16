"""
FastAPI REST API for the AI Advertising Agent.
Allows external systems to integrate with the agent.
"""
from __future__ import annotations
import uuid
import os
import shutil
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from agent import AdvertisingAgent
from api.schemas import (
    ChatRequest, ChatResponse,
    PlatformConnectRequest, PlatformConnectResponse,
    CreatePostRequest, CreatePostResponse,
    CampaignCreateRequest,
    AnalyticsRequest,
    RecommendationsRequest,
)
from models.campaign import Campaign, TargetAudience, MarketingGoal
from models.business_profile import BusinessProfile
from storage.profile_manager import ProfileManager
from tools.job_runner import start_background_runner, stop_background_runner
from tools.rate_limiter import RateLimiter
from tools.notifications import NotificationManager

logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI Advertising Agent API",
    description="עוזר פרסום AI - API לניהול פרסום ברשתות חברתיות",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Media upload storage
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "/tmp/ai-agent-uploads"))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

ALLOWED_MEDIA_TYPES = {
    "image/jpeg", "image/png", "image/gif", "image/webp",
    "video/mp4", "video/quicktime", "video/webm",
}
MAX_UPLOAD_MB = 50

# Agent instances per session
_agents: Dict[str, AdvertisingAgent] = {}
_campaigns: Dict[str, Campaign] = {}


def _get_or_create_agent(session_id: str) -> AdvertisingAgent:
    if session_id not in _agents:
        _agents[session_id] = AdvertisingAgent(session_id=session_id)
    return _agents[session_id]


@app.get("/")
async def root():
    return {
        "name": "AI Advertising Agent",
        "name_he": "עוזר פרסום AI",
        "version": "2.0.0",
        "status": "running",
        "docs": "/docs",
    }


@app.post("/api/upload")
async def upload_media(file: UploadFile = File(...)):
    """Upload an image or video file and return its public URL."""
    if file.content_type not in ALLOWED_MEDIA_TYPES:
        raise HTTPException(status_code=400, detail=f"File type not allowed: {file.content_type}")

    # Read and check size
    data = await file.read()
    if len(data) > MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"File too large (max {MAX_UPLOAD_MB}MB)")

    ext = Path(file.filename or "file").suffix.lower() or ".bin"
    filename = f"{uuid.uuid4().hex}{ext}"
    dest = UPLOAD_DIR / filename
    dest.write_bytes(data)

    base_url = os.getenv("PUBLIC_API_URL", "").rstrip("/")
    return {"url": f"{base_url}/uploads/{filename}", "filename": filename}


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat with the AI advertising agent."""
    session_id = request.session_id or str(uuid.uuid4())
    plan = request.plan or "free"
    language = request.language or "he"
    agent = _get_or_create_agent(session_id)

    # Rate limiting check (plan-aware)
    allowed, reason = RateLimiter.check(session_id, plan=plan)
    if not allowed:
        raise HTTPException(status_code=429, detail=reason)

    # Update platform tokens if provided (per-user OAuth tokens)
    if request.social_tokens:
        agent.set_platform_tokens(request.social_tokens, request.social_page_ids or {})

    try:
        message = request.message
        parts = []

        # Language instruction (invisible to user display — injected server-side)
        if language == "en":
            parts.append("[system: respond in English, write posts in English]")
        else:
            parts.append("[system: respond in Hebrew, write posts in Hebrew]")

        # App context from AIBuilder — prepend structured info
        if request.app_context and request.app_context.get("app_name"):
            ctx = request.app_context
            parts.append(
                f"[ILMARIAI AIBuilder handoff — skip general onboarding]\n"
                f"App name: {ctx.get('app_name','')}\n"
                f"Website: {ctx.get('app_url','')}\n"
                f"Description: {ctx.get('app_desc','')}"
            )

        parts.append(message)
        full_message = "\n".join(parts)

        response = await agent.chat(full_message)
        RateLimiter.record(session_id)
        profile = ProfileManager.get_or_create(session_id)
        usage = RateLimiter.get_usage(session_id, plan=plan)
        return ChatResponse(
            response=response,
            session_id=session_id,
            onboarding_complete=profile.onboarding_complete,
            business_name=profile.business_name or None,
            usage=usage,
        )
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/profile/{session_id}")
async def get_profile(session_id: str):
    """Get the business profile for a session."""
    profile = ProfileManager.get(session_id)
    if not profile:
        return {"exists": False, "onboarding_complete": False}
    return {
        "exists": True,
        "onboarding_complete": profile.onboarding_complete,
        "business_name": profile.business_name,
        "website_url": profile.website_url,
        "description": profile.description,
        "product_service": profile.product_service,
        "unique_value": profile.unique_value,
        "target_audience": {
            "age_range": profile.target_audience.age_range,
            "locations": profile.target_audience.locations,
            "interests": profile.target_audience.interests,
        },
        "goals": {
            "primary": profile.goals.primary_goal,
            "budget_ils": profile.goals.monthly_budget_ils,
        },
        "content_strategy": {
            "tone": profile.content_strategy.tone,
            "platforms": profile.content_strategy.preferred_platforms,
            "frequency": profile.content_strategy.posting_frequency,
            "brand_keywords": profile.content_strategy.brand_keywords,
        },
        "stats": {
            "total_posts": profile.total_posts_published,
            "best_platform": profile.best_performing_platform,
        },
    }


@app.delete("/api/profile/{session_id}")
async def reset_profile(session_id: str):
    """Reset/delete the business profile (restart onboarding)."""
    ProfileManager.delete(session_id)
    if session_id in _agents:
        del _agents[session_id]
    return {"message": "Profile reset. Onboarding will restart.", "session_id": session_id}


@app.post("/api/platforms/connect", response_model=PlatformConnectResponse)
async def connect_platform(request: PlatformConnectRequest, session_id: Optional[str] = None):
    """Connect a social media platform."""
    session_id = session_id or "default"
    agent = _get_or_create_agent(session_id)

    account = await agent.connect_platform(request.platform)
    if account:
        return PlatformConnectResponse(
            platform=request.platform,
            connected=True,
            account_info={
                "username": account.username,
                "display_name": account.display_name,
                "followers": account.followers_count,
            },
        )
    return PlatformConnectResponse(
        platform=request.platform,
        connected=False,
        error="Failed to connect",
    )


@app.get("/api/platforms")
async def list_platforms(session_id: Optional[str] = "default"):
    """List all available platforms and their connection status."""
    from config import SUPPORTED_PLATFORMS
    return {
        "platforms": [
            {
                "name": name,
                "name_he": info["name_he"],
                "icon": info["icon"],
                "features": info["features"],
                "best_for": info["best_for"],
            }
            for name, info in SUPPORTED_PLATFORMS.items()
        ]
    }


@app.post("/api/posts", response_model=CreatePostResponse)
async def create_post(request: CreatePostRequest, session_id: Optional[str] = "default"):
    """Create and publish a post to social media platforms."""
    agent = _get_or_create_agent(session_id)

    from tools.social_tools import post_content
    result = await post_content(
        platforms=request.platforms,
        content=request.content,
        media_urls=request.media_urls,
        groups=request.groups,
        hashtags=request.hashtags,
    )

    # Update stats
    profile = ProfileManager.get_or_create(session_id)
    profile.total_posts_published += len(request.platforms)
    ProfileManager.save(profile)

    return CreatePostResponse(**result)


@app.post("/api/campaigns")
async def create_campaign(request: CampaignCreateRequest):
    """Create a new advertising campaign."""
    try:
        goals = [MarketingGoal(g) for g in request.goals if g in MarketingGoal.__members__.values()]
        if not goals:
            goals = [MarketingGoal.BRAND_AWARENESS]

        audience_data = request.target_audience or {}
        audience = TargetAudience(
            age_min=audience_data.get("age_min", 18),
            age_max=audience_data.get("age_max", 65),
            locations=audience_data.get("locations", ["Israel"]),
            interests=audience_data.get("interests", []),
        )

        campaign = Campaign(
            name=request.name,
            description=request.description or "",
            goals=goals,
            platforms=request.platforms,
            target_audience=audience,
            budget_monthly=request.budget_monthly,
            business_description=request.business_description or "",
            website_url=request.website_url or "",
        )

        _campaigns[campaign.id] = campaign
        return {"campaign_id": campaign.id, "campaign": campaign.model_dump()}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/campaigns/{campaign_id}")
async def get_campaign(campaign_id: str):
    campaign = _campaigns.get(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign.model_dump()


@app.get("/api/analytics")
async def get_analytics(platform: Optional[str] = None, days: int = 30, session_id: str = "default"):
    """Get analytics for connected platforms."""
    from tools.analytics_tools import get_campaign_performance, compare_platforms_performance

    if platform:
        from tools.analytics_tools import get_audience_insights
        return await get_audience_insights(platform)
    else:
        return await compare_platforms_performance(days=days)


@app.get("/api/recommendations")
async def get_recommendations(
    platforms: str = "",
    goals: str = "new_users",
    session_id: str = "default",
):
    """Get platform and strategy recommendations."""
    agent = _get_or_create_agent(session_id)
    connected = [p.strip() for p in platforms.split(",") if p.strip()]
    goals_list = [g.strip() for g in goals.split(",") if g.strip()]

    return agent._get_platform_recommendations(
        connected_platforms=connected,
        goals=goals_list,
    )


@app.get("/api/scheduled/{session_id}")
async def get_scheduled_posts(session_id: str):
    """Get all scheduled posts for a session."""
    from tools.scheduler import list_scheduled_posts
    return list_scheduled_posts(session_id=session_id)


@app.delete("/api/scheduled/{session_id}/{job_id}")
async def cancel_post(session_id: str, job_id: str):
    """Cancel a scheduled post."""
    from tools.scheduler import cancel_scheduled_post
    return cancel_scheduled_post(job_id=job_id)


@app.get("/api/notifications/{session_id}")
async def get_notifications(session_id: str):
    """Get unread notifications for a session."""
    return {
        "notifications": NotificationManager.get_unread(session_id),
        "total_unread": len(NotificationManager.get_unread(session_id)),
    }


@app.post("/api/notifications/{session_id}/read")
async def mark_notifications_read(session_id: str):
    """Mark all notifications as read."""
    NotificationManager.mark_all_read(session_id)
    return {"message": "All notifications marked as read"}


@app.get("/api/usage/{session_id}")
async def get_usage(session_id: str, plan: str = "free"):
    """Get API usage stats for a session."""
    return RateLimiter.get_usage(session_id, plan=plan)


@app.get("/api/report/{session_id}")
async def get_weekly_report(session_id: str):
    """Generate a weekly report for a session."""
    from tools.advanced_tools import generate_weekly_report
    from tools.scheduler import list_scheduled_posts
    profile = ProfileManager.get_or_create(session_id)
    scheduled = list_scheduled_posts(session_id=session_id)
    return generate_weekly_report(
        session_id=session_id,
        business_name=profile.business_name,
        website_url=profile.website_url,
        posts_this_week=profile.total_posts_published,
        platforms_active=profile.content_strategy.preferred_platforms,
    )


@app.get("/api/chat/{session_id}/history")
async def get_chat_history(session_id: str):
    """Get conversation history for a session."""
    from storage.history_manager import HistoryManager
    history = HistoryManager.load(session_id)
    return {"history": history, "count": len(history)}


@app.delete("/api/chat/{session_id}")
async def clear_chat_history(session_id: str):
    """Clear conversation history for a session."""
    if session_id in _agents:
        _agents[session_id].clear_history()
    return {"message": "History cleared", "session_id": session_id}


@app.get("/api/crm/{session_id}")
async def get_crm_leads(session_id: str):
    """Get all CRM leads/contacts for a session."""
    from tools.action_log import get_action_log
    import os, json
    crm_path = os.path.join(os.environ.get("CRM_DIR", "/tmp/ai-agent-crm"), f"{session_id}.json")
    if not os.path.exists(crm_path):
        return {"leads": [], "total": 0}
    try:
        with open(crm_path, "r", encoding="utf-8") as f:
            leads = json.load(f)
        return {"leads": leads, "total": len(leads)}
    except Exception:
        return {"leads": [], "total": 0}


@app.get("/api/audit/{session_id}")
async def get_audit_log(session_id: str, limit: int = 50):
    """Get audit action log for a session."""
    from tools.action_log import get_action_log
    return {"actions": get_action_log(session_id, limit=limit)}


@app.post("/api/weekly-email/{session_id}")
async def generate_weekly_email_data(session_id: str):
    """
    Generate weekly email report data for a session.
    Called by appify backend cron to get data before sending via Resend.
    """
    from tools.advanced_tools import generate_weekly_report
    from tools.scheduler import list_scheduled_posts
    profile = ProfileManager.get_or_create(session_id)
    scheduled = list_scheduled_posts(session_id=session_id)
    report = generate_weekly_report(
        session_id=session_id,
        business_name=profile.business_name,
        website_url=profile.website_url,
        posts_this_week=profile.total_posts_published,
        platforms_active=profile.content_strategy.preferred_platforms,
    )
    return {
        "session_id": session_id,
        "email_subject": f"סיכום שבועי — {profile.business_name or 'העסק שלך'} | ilmariai.com",
        "business_name": profile.business_name,
        "report": report,
        "scheduled_upcoming": scheduled.get("scheduled_posts", [])[:3],
    }


@app.on_event("startup")
async def startup_event():
    """Start background job runner on server start."""
    start_background_runner()
    logger.info("✅ Background job runner started")


@app.on_event("shutdown")
async def shutdown_event():
    stop_background_runner()
    for agent in _agents.values():
        await agent.close()
