"""
Analytics and performance tracking tools.
"""
from __future__ import annotations
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# Platform registry for analytics
_platform_registry: Dict[str, Any] = {}
_campaign_store: Dict[str, Any] = {}


def register_platform(name: str, platform_instance: Any):
    _platform_registry[name] = platform_instance


def store_campaign(campaign_id: str, campaign_data: Dict[str, Any]):
    _campaign_store[campaign_id] = campaign_data


async def get_campaign_performance(
    campaign_id: Optional[str] = None,
    platforms: Optional[List[str]] = None,
    days: int = 30,
) -> Dict[str, Any]:
    """
    Get overall campaign performance metrics across platforms.

    Args:
        campaign_id: Optional campaign ID to filter by
        platforms: List of platforms to include (defaults to all connected)
        days: Number of days to analyze
    """
    if not platforms:
        platforms = list(_platform_registry.keys())

    results = {}
    totals = {
        "total_reach": 0,
        "total_impressions": 0,
        "total_likes": 0,
        "total_comments": 0,
        "total_shares": 0,
        "total_followers_gained": 0,
        "total_posts": 0,
    }

    for platform_name in platforms:
        p = _platform_registry.get(platform_name)
        if not p:
            continue
        try:
            metrics = await p.get_metrics(days)
            results[platform_name] = {
                "followers_gained": metrics.followers_gained,
                "posts_published": metrics.posts_published,
                "reach": metrics.total_reach,
                "impressions": metrics.total_impressions,
                "likes": metrics.total_likes,
                "comments": metrics.total_comments,
                "shares": metrics.total_shares,
                "engagement_rate": metrics.engagement_rate,
                "best_times": metrics.best_posting_times,
            }
            totals["total_reach"] += metrics.total_reach
            totals["total_impressions"] += metrics.total_impressions
            totals["total_likes"] += metrics.total_likes
            totals["total_comments"] += metrics.total_comments
            totals["total_shares"] += metrics.total_shares
            totals["total_followers_gained"] += metrics.followers_gained
            totals["total_posts"] += metrics.posts_published
        except Exception as e:
            results[platform_name] = {"error": str(e)}

    overall_engagement = (
        (totals["total_likes"] + totals["total_comments"] + totals["total_shares"]) /
        max(totals["total_impressions"], 1) * 100
    )

    return {
        "campaign_id": campaign_id,
        "period_days": days,
        "platforms": results,
        "totals": totals,
        "overall_engagement_rate": round(overall_engagement, 2),
        "best_performing_platform": max(
            results.items(),
            key=lambda x: x[1].get("engagement_rate", 0) if isinstance(x[1], dict) else 0,
            default=("N/A", {})
        )[0] if results else "N/A",
        "recommendation": _generate_performance_recommendation(results, totals),
    }


def _generate_performance_recommendation(
    results: Dict[str, Any],
    totals: Dict[str, int],
) -> str:
    """Generate a performance recommendation based on metrics."""
    if not results:
        return "Connect platforms to get performance insights"

    best_platform = max(
        results.items(),
        key=lambda x: x[1].get("engagement_rate", 0) if isinstance(x[1], dict) else 0,
        default=("N/A", {})
    )

    rec = f"הפלטפורמה הטובה ביותר שלך היא {best_platform[0]} עם שיעור מעורבות של {best_platform[1].get('engagement_rate', 0):.1f}%. "

    if totals["total_followers_gained"] < 100:
        rec += "מומלץ להגדיל את תדירות הפרסום ולשפר את איכות התוכן. "
    elif totals["total_followers_gained"] > 500:
        rec += "גדילה מצוינת! שקלו להשקיע בפרסום ממומן כדי לזרז את הצמיחה. "

    return rec


async def compare_platforms_performance(
    days: int = 30,
) -> Dict[str, Any]:
    """
    Compare performance across all connected platforms.

    Args:
        days: Number of days to analyze
    """
    platforms = list(_platform_registry.keys())
    if not platforms:
        return {"error": "No platforms connected"}

    comparison = {}
    for platform_name in platforms:
        p = _platform_registry.get(platform_name)
        if not p:
            continue
        try:
            metrics = await p.get_metrics(days)
            comparison[platform_name] = {
                "engagement_rate": metrics.engagement_rate,
                "reach": metrics.total_reach,
                "followers_gained": metrics.followers_gained,
                "posts": metrics.posts_published,
                "avg_likes_per_post": metrics.total_likes // max(metrics.posts_published, 1),
                "roi_score": round(metrics.engagement_rate * metrics.followers_gained / 100, 2),
            }
        except Exception as e:
            comparison[platform_name] = {"error": str(e)}

    # Rank platforms
    valid_platforms = {k: v for k, v in comparison.items() if "error" not in v}
    rankings = {
        "best_engagement": max(valid_platforms.items(), key=lambda x: x[1].get("engagement_rate", 0), default=("N/A", {}))[0],
        "best_reach": max(valid_platforms.items(), key=lambda x: x[1].get("reach", 0), default=("N/A", {}))[0],
        "best_growth": max(valid_platforms.items(), key=lambda x: x[1].get("followers_gained", 0), default=("N/A", {}))[0],
        "best_roi": max(valid_platforms.items(), key=lambda x: x[1].get("roi_score", 0), default=("N/A", {}))[0],
    }

    return {
        "period_days": days,
        "platforms": comparison,
        "rankings": rankings,
        "insight": f"הפלטפורמה המשתלמת ביותר עבורך היא {rankings['best_roi']} על בסיס ROI",
    }


async def get_audience_insights(
    platform: str,
) -> Dict[str, Any]:
    """
    Get audience demographics and behavior insights.

    Args:
        platform: Platform to analyze
    """
    # Demo insights - in production these come from platform analytics APIs
    demo_insights = {
        "facebook": {
            "age_distribution": {"18-24": 15, "25-34": 35, "35-44": 28, "45-54": 15, "55+": 7},
            "gender": {"male": 45, "female": 52, "other": 3},
            "top_locations": ["Tel Aviv", "Jerusalem", "Haifa", "Beer Sheva"],
            "peak_hours": ["09:00", "12:00", "19:00"],
            "top_interests": ["Technology", "Business", "Food", "Travel", "Sports"],
            "language": {"Hebrew": 85, "English": 10, "Arabic": 5},
        },
        "instagram": {
            "age_distribution": {"18-24": 35, "25-34": 40, "35-44": 18, "45+": 7},
            "gender": {"male": 40, "female": 57, "other": 3},
            "top_locations": ["Tel Aviv", "Jerusalem", "Haifa"],
            "peak_hours": ["08:00", "12:00", "21:00"],
            "top_interests": ["Fashion", "Food", "Travel", "Fitness", "Art"],
        },
        "linkedin": {
            "age_distribution": {"18-24": 10, "25-34": 45, "35-44": 30, "45+": 15},
            "gender": {"male": 55, "female": 43, "other": 2},
            "top_industries": ["Technology", "Finance", "Marketing", "Consulting", "Healthcare"],
            "seniority": {"entry": 20, "senior": 35, "manager": 25, "director": 12, "executive": 8},
            "peak_hours": ["08:00", "10:00", "12:00"],
        },
        "twitter": {
            "age_distribution": {"18-24": 28, "25-34": 42, "35-44": 20, "45+": 10},
            "top_interests": ["Technology", "Politics", "Sports", "Entertainment", "News"],
            "peak_hours": ["08:00", "13:00", "17:00"],
        },
        "tiktok": {
            "age_distribution": {"13-17": 25, "18-24": 42, "25-34": 22, "35+": 11},
            "gender": {"male": 40, "female": 58, "other": 2},
            "top_interests": ["Entertainment", "Dance", "Comedy", "Food", "DIY"],
            "peak_hours": ["07:00", "12:00", "19:00", "22:00"],
        },
        "youtube": {
            "age_distribution": {"18-24": 22, "25-34": 38, "35-44": 25, "45+": 15},
            "gender": {"male": 55, "female": 43, "other": 2},
            "top_devices": {"mobile": 70, "desktop": 20, "tablet": 10},
            "avg_watch_time": "8 minutes",
            "peak_hours": ["12:00-14:00", "20:00-23:00"],
        },
    }

    insights = demo_insights.get(platform, {"message": "No insights available for this platform"})

    return {
        "platform": platform,
        "insights": insights,
        "recommendations": _generate_audience_recommendations(platform, insights),
    }


def _generate_audience_recommendations(platform: str, insights: Dict) -> List[str]:
    """Generate actionable recommendations based on audience insights."""
    recs = []

    if platform == "instagram" and insights.get("age_distribution", {}).get("18-24", 0) > 30:
        recs.append("הקהל שלך צעיר - השתמש ב-Reels ו-Stories לתוצאות טובות יותר")

    if platform == "linkedin":
        recs.append("פרסם תוכן מקצועי בשעות 8:00-10:00 בבוקר לימי עבודה")
        recs.append("כתב מאמרים ארוכי טווח לבניית סמכות מקצועית")

    if platform == "tiktok":
        recs.append("תוכן מקורי וטבעי מבצע טוב יותר מתוכן מוצלח")
        recs.append("השתמש בטרנדים נוכחיים לחשיפה מירבית")

    if not recs:
        recs = [
            f"פרסם בשעות השיא של {platform} לחשיפה מרבית",
            "נסה תכנים שונים ועקוב אחרי מה עובד הכי טוב",
        ]

    return recs


async def track_lead_conversions(
    campaign_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Track lead generation and conversion metrics.

    Args:
        campaign_id: Optional campaign ID to filter
    """
    # Demo conversion data
    return {
        "campaign_id": campaign_id,
        "period": "last_30_days",
        "leads": {
            "total_leads": 45,
            "qualified_leads": 18,
            "converted": 7,
            "conversion_rate": 38.9,
            "sources": {
                "facebook": 15,
                "instagram": 12,
                "linkedin": 10,
                "twitter": 5,
                "other": 3,
            },
        },
        "cost_per_lead": {
            "facebook": 35.0,
            "instagram": 28.0,
            "linkedin": 85.0,
        },
        "recommendations": [
            "Instagram מספק את הלידים הזולים ביותר - הגדל תקציב שם",
            "LinkedIn מספק לידים איכותיים יותר למרות העלות הגבוהה יותר",
            "שקול להוסיף landing page ייעודי לכל קמפיין",
        ],
    }
