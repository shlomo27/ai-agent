"""
Pydantic schemas for the REST API request and response models.
"""
from __future__ import annotations
from typing import List, Optional, Dict, Any
from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    plan: Optional[str] = "free"   # marketing plan: free / basic / pro / business / bundle_*
    language: Optional[str] = "he" # "he" = Hebrew, "en" = English


class ChatResponse(BaseModel):
    response: str
    session_id: str
    onboarding_complete: Optional[bool] = None
    business_name: Optional[str] = None
    usage: Optional[Dict[str, Any]] = None


class PlatformConnectRequest(BaseModel):
    platform: str


class PlatformConnectResponse(BaseModel):
    platform: str
    connected: bool
    account_info: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class CreatePostRequest(BaseModel):
    platforms: List[str]
    content: str
    media_urls: Optional[List[str]] = None
    hashtags: Optional[List[str]] = None
    groups: Optional[List[str]] = None


class CreatePostResponse(BaseModel):
    results: Dict[str, Any]
    total_platforms: int
    successful: int


class CampaignCreateRequest(BaseModel):
    name: str
    description: Optional[str] = ""
    goals: List[str]
    platforms: List[str]
    target_audience: Optional[Dict[str, Any]] = None
    budget_monthly: Optional[float] = None
    business_description: Optional[str] = ""
    website_url: Optional[str] = ""


class AnalyticsRequest(BaseModel):
    platform: Optional[str] = None
    days: int = 30


class RecommendationsRequest(BaseModel):
    connected_platforms: List[str]
    goals: List[str]
    business_type: Optional[str] = "general"


class QuestionnaireStartResponse(BaseModel):
    session_id: str
    first_question: str
    question_number: int
    total_questions: int


class QuestionnaireAnswerRequest(BaseModel):
    session_id: str
    answer: str


class QuestionnaireAnswerResponse(BaseModel):
    next_question: Optional[str] = None
    question_number: Optional[int] = None
    total_questions: Optional[int] = None
    completed: bool = False
    campaign_id: Optional[str] = None
