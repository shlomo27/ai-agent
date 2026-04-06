"""
FastAPI REST API for the AI Advertising Agent.
Allows external systems to integrate with the agent.
"""
from __future__ import annotations
import uuid
import logging
from typing import Dict, Any, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

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

logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI Advertising Agent API",
    description="עוזר פרסום AI - API לניהול פרסום ברשתות חברתיות",
    version="1.0.0",
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

# Agent instances per session
_agents: Dict[str, AdvertisingAgent] = {}
_campaigns: Dict[str, Campaign] = {}


def _get_or_create_agent(session_id: str) -> AdvertisingAgent:
    if session_id not in _agents:
        _agents[session_id] = AdvertisingAgent()
    return _agents[session_id]


@app.get("/")
async def root():
    """API health check and info."""
    return {
        "name": "AI Advertising Agent",
        "name_he": "עוזר פרסום AI",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
    }


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat with the AI advertising agent.
    The agent can perform social media actions based on the conversation.
    """
    session_id = request.session_id or str(uuid.uuid4())
    agent = _get_or_create_agent(session_id)

    try:
        response = await agent.chat(request.message)
        return ChatResponse(response=response, session_id=session_id)
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


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
    """Get campaign details."""
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
        insights = await get_audience_insights(platform)
        return insights
    else:
        comparison = await compare_platforms_performance(days=days)
        return comparison


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

    recommendations = agent._get_platform_recommendations(
        connected_platforms=connected,
        goals=goals_list,
    )
    return recommendations


@app.delete("/api/chat/{session_id}")
async def clear_chat_history(session_id: str):
    """Clear conversation history for a session."""
    if session_id in _agents:
        _agents[session_id].clear_history()
    return {"message": "History cleared", "session_id": session_id}


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown."""
    for agent in _agents.values():
        await agent.close()
