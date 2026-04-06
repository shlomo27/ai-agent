"""
Campaign and marketing goal data models.
"""
from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import uuid


class MarketingGoal(str, Enum):
    NEW_USERS = "new_users"              # גיוס משתמשים חדשים
    BRAND_AWARENESS = "brand_awareness"  # מודעות למותג
    LEAD_GENERATION = "lead_generation"  # לידים
    SALES = "sales"                      # מכירות
    ENGAGEMENT = "engagement"            # מעורבות
    TRAFFIC = "traffic"                  # תנועה לאתר
    COMMUNITY = "community"              # בניית קהילה
    RETENTION = "retention"              # שימור לקוחות


GOAL_LABELS_HE = {
    MarketingGoal.NEW_USERS: "גיוס משתמשים / לקוחות חדשים",
    MarketingGoal.BRAND_AWARENESS: "מודעות למותג",
    MarketingGoal.LEAD_GENERATION: "יצירת לידים",
    MarketingGoal.SALES: "הגדלת מכירות",
    MarketingGoal.ENGAGEMENT: "הגדלת מעורבות",
    MarketingGoal.TRAFFIC: "הגברת תנועה לאתר",
    MarketingGoal.COMMUNITY: "בניית קהילה",
    MarketingGoal.RETENTION: "שימור לקוחות",
}


class Gender(str, Enum):
    ALL = "all"
    MALE = "male"
    FEMALE = "female"


class CampaignStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"


class TargetAudience(BaseModel):
    age_min: int = Field(default=18, ge=13, le=100)
    age_max: int = Field(default=65, ge=13, le=100)
    gender: Gender = Gender.ALL
    locations: List[str] = Field(default_factory=list)
    languages: List[str] = Field(default_factory=list)
    interests: List[str] = Field(default_factory=list)
    industries: List[str] = Field(default_factory=list)
    job_titles: List[str] = Field(default_factory=list)
    custom_description: str = ""


class Campaign(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str = ""
    goals: List[MarketingGoal]
    target_audience: TargetAudience
    platforms: List[str] = Field(default_factory=list)
    content_themes: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    competitors: List[str] = Field(default_factory=list)
    budget_monthly: Optional[float] = None
    has_videos: bool = False
    has_images: bool = False
    posting_frequency: str = "daily"  # daily, weekly, multiple_daily
    status: CampaignStatus = CampaignStatus.DRAFT
    created_at: datetime = Field(default_factory=datetime.now)
    business_description: str = ""
    website_url: str = ""
    tone: str = "professional"  # professional, casual, funny, inspirational


class PostContent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    platform: str
    text: str
    media_urls: List[str] = Field(default_factory=list)
    hashtags: List[str] = Field(default_factory=list)
    target_group_ids: List[str] = Field(default_factory=list)
    scheduled_time: Optional[datetime] = None
    campaign_id: Optional[str] = None
    is_posted: bool = False
    post_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)


class EngagementAction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    action_type: str  # like, comment, share, follow, connect, reply
    platform: str
    target_id: str
    target_type: str  # post, user, group, page
    content: Optional[str] = None  # for comments/replies
    campaign_id: Optional[str] = None
    executed_at: Optional[datetime] = None
    success: bool = False
    error_message: Optional[str] = None


class PlatformRecommendation(BaseModel):
    platform: str
    reason: str
    reason_he: str
    estimated_monthly_reach: int
    estimated_setup_time_hours: int
    difficulty: str  # easy, medium, hard
    priority: int  # 1=highest
    setup_steps: List[str] = Field(default_factory=list)
    estimated_cost_monthly: Optional[float] = None
    ad_platform_guide: Optional[str] = None


class ContentCalendarEntry(BaseModel):
    date: datetime
    platform: str
    content_idea: str
    content_type: str  # post, story, reel, video, article
    hashtags: List[str] = Field(default_factory=list)
    goal: MarketingGoal
    notes: str = ""
