"""
Social media platform data models.
"""
from __future__ import annotations
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import uuid


class PlatformCredentials(BaseModel):
    platform: str
    access_token: str = ""
    refresh_token: str = ""
    app_id: str = ""
    app_secret: str = ""
    account_id: str = ""
    extra_data: Dict[str, Any] = Field(default_factory=dict)
    expires_at: Optional[datetime] = None


class PlatformAccount(BaseModel):
    platform: str
    account_id: str
    username: str
    display_name: str = ""
    bio: str = ""
    profile_url: str = ""
    followers_count: int = 0
    following_count: int = 0
    posts_count: int = 0
    is_connected: bool = False
    is_business_account: bool = False
    connected_at: Optional[datetime] = None
    last_synced: Optional[datetime] = None


class SocialPost(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    platform_post_id: str = ""
    platform: str
    content: str
    media_urls: List[str] = Field(default_factory=list)
    post_url: str = ""
    likes_count: int = 0
    comments_count: int = 0
    shares_count: int = 0
    views_count: int = 0
    reach: int = 0
    posted_at: Optional[datetime] = None
    is_own_post: bool = True
    author_username: str = ""
    hashtags: List[str] = Field(default_factory=list)


class DiscoveredUser(BaseModel):
    platform: str
    user_id: str
    username: str
    display_name: str = ""
    bio: str = ""
    profile_url: str = ""
    followers_count: int = 0
    following_count: int = 0
    posts_count: int = 0
    relevance_score: float = Field(ge=0.0, le=1.0, default=0.0)
    topics: List[str] = Field(default_factory=list)
    location: str = ""
    is_followed: bool = False
    connection_requested: bool = False
    discovered_at: datetime = Field(default_factory=datetime.now)


class DiscoveredGroup(BaseModel):
    platform: str
    group_id: str
    name: str
    description: str = ""
    group_url: str = ""
    members_count: int = 0
    posts_per_day: int = 0
    topics: List[str] = Field(default_factory=list)
    relevance_score: float = Field(ge=0.0, le=1.0, default=0.0)
    is_joined: bool = False
    is_public: bool = True
    discovered_at: datetime = Field(default_factory=datetime.now)


class PlatformMetrics(BaseModel):
    platform: str
    period_days: int = 30
    followers_gained: int = 0
    posts_published: int = 0
    total_reach: int = 0
    total_impressions: int = 0
    total_likes: int = 0
    total_comments: int = 0
    total_shares: int = 0
    engagement_rate: float = 0.0
    top_performing_content: List[str] = Field(default_factory=list)
    best_posting_times: List[str] = Field(default_factory=list)
    audience_demographics: Dict[str, Any] = Field(default_factory=dict)
    measured_at: datetime = Field(default_factory=datetime.now)


class AdCampaign(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    platform: str  # facebook, google
    name: str
    goal: str
    daily_budget: float
    total_budget: float
    target_audience: Dict[str, Any] = Field(default_factory=dict)
    ad_content: str = ""
    status: str = "draft"
    impressions: int = 0
    clicks: int = 0
    conversions: int = 0
    spend: float = 0.0
    cpc: float = 0.0  # cost per click
    cpa: float = 0.0  # cost per acquisition
    created_at: datetime = Field(default_factory=datetime.now)
