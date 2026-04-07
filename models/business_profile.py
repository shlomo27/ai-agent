"""
Business Profile model - stores all information about the business
so the AI agent can make intelligent, targeted marketing decisions.
"""
from __future__ import annotations
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class TargetAudience(BaseModel):
    age_range: str = ""                    # "25-45"
    locations: List[str] = []             # ["Israel", "Tel Aviv"]
    languages: List[str] = ["Hebrew"]
    interests: List[str] = []             # ["tech", "startups", "AI"]
    pain_points: List[str] = []           # ["wasting time", "expensive tools"]
    income_level: str = ""                # "middle", "high"
    profession: List[str] = []            # ["entrepreneurs", "developers"]


class MarketingGoals(BaseModel):
    primary_goal: str = ""                # "brand_awareness" | "sales" | "leads" | "community"
    secondary_goals: List[str] = []
    monthly_budget_ils: float = 0
    target_monthly_visitors: int = 0
    target_followers_per_platform: int = 0
    kpis: List[str] = []                  # ["website clicks", "signups", "purchases"]


class CompetitorInfo(BaseModel):
    name: str = ""
    website: str = ""
    strengths: List[str] = []
    weaknesses: List[str] = []


class ContentStrategy(BaseModel):
    tone: str = "professional"            # "professional" | "casual" | "funny" | "inspirational"
    content_types: List[str] = []        # ["educational", "promotional", "behind_scenes"]
    posting_frequency: str = "daily"     # "daily" | "3x_week" | "weekly"
    preferred_platforms: List[str] = []
    hashtag_strategy: List[str] = []
    avoid_topics: List[str] = []
    brand_colors: List[str] = []
    brand_keywords: List[str] = []       # words always used in posts


class BusinessProfile(BaseModel):
    # Identity
    session_id: str
    business_name: str = ""
    website_url: str = ""
    logo_url: str = ""
    description: str = ""                 # short description
    full_description: str = ""            # detailed description
    product_service: str = ""             # what exactly is sold/offered
    unique_value: str = ""               # what makes it different
    pricing_model: str = ""              # "freemium" | "subscription" | "one_time"
    price_range: str = ""               # "free" | "29-99 ILS/month"

    # Audience & Goals
    target_audience: TargetAudience = Field(default_factory=TargetAudience)
    goals: MarketingGoals = Field(default_factory=MarketingGoals)
    competitors: List[CompetitorInfo] = []

    # Content
    content_strategy: ContentStrategy = Field(default_factory=ContentStrategy)

    # Status
    onboarding_complete: bool = False
    onboarding_step: int = 0             # which step of questionnaire
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    # Campaign history summary
    total_posts_published: int = 0
    best_performing_platform: str = ""
    last_campaign_summary: str = ""

    def to_agent_context(self) -> str:
        """Convert profile to a rich context string for the AI agent system prompt."""
        if not self.onboarding_complete:
            return ""

        ctx = f"""
## 📊 פרופיל עסקי של המשתמש:

**שם העסק:** {self.business_name}
**אתר:** {self.website_url}
**תיאור:** {self.full_description or self.description}
**מוצר/שירות:** {self.product_service}
**יתרון ייחודי:** {self.unique_value}
**מודל תמחור:** {self.pricing_model} ({self.price_range})

## 🎯 קהל היעד:
- **גילאים:** {self.target_audience.age_range}
- **מיקום:** {', '.join(self.target_audience.locations)}
- **שפות:** {', '.join(self.target_audience.languages)}
- **תחומי עניין:** {', '.join(self.target_audience.interests)}
- **כאבים/בעיות:** {', '.join(self.target_audience.pain_points)}
- **מקצועות:** {', '.join(self.target_audience.profession)}

## 🚀 מטרות שיווקיות:
- **מטרה עיקרית:** {self.goals.primary_goal}
- **מטרות משניות:** {', '.join(self.goals.secondary_goals)}
- **תקציב חודשי:** ₪{self.goals.monthly_budget_ils}
- **KPIs:** {', '.join(self.goals.kpis)}

## 📝 אסטרטגיית תוכן:
- **טון:** {self.content_strategy.tone}
- **סוגי תוכן:** {', '.join(self.content_strategy.content_types)}
- **תדירות:** {self.content_strategy.posting_frequency}
- **פלטפורמות מועדפות:** {', '.join(self.content_strategy.preferred_platforms)}
- **מילות מפתח של המותג:** {', '.join(self.content_strategy.brand_keywords)}
- **נושאים להימנע:** {', '.join(self.content_strategy.avoid_topics)}

## 🏆 מתחרים:
{chr(10).join([f"- {c.name}: חוזקות - {', '.join(c.strengths)}, חולשות - {', '.join(c.weaknesses)}" for c in self.competitors]) if self.competitors else "- לא הוגדרו מתחרים"}

## 📈 היסטוריה:
- **פוסטים שפורסמו:** {self.total_posts_published}
- **פלטפורמה מובילה:** {self.best_performing_platform or "טרם נקבעה"}
"""
        return ctx.strip()
