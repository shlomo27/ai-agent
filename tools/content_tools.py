"""
Content creation and strategy tools.
These help generate post content, hashtags, and publishing schedules.
"""
from __future__ import annotations
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


def generate_post_content(
    goal: str,
    topic: str,
    platform: str,
    tone: str = "professional",
    language: str = "hebrew",
    include_cta: bool = True,
) -> Dict[str, Any]:
    """
    Generate social media post content based on marketing goal and topic.
    Note: Claude agent uses this as a tool; the actual generation is done by Claude itself.

    Args:
        goal: Marketing goal (new_users, brand_awareness, lead_generation, sales, engagement)
        topic: Main topic or subject of the post
        platform: Target platform (affects character limits and style)
        tone: Content tone (professional, casual, funny, inspirational)
        language: Content language (hebrew, english, both)
        include_cta: Whether to include a call-to-action
    """
    platform_limits = {
        "twitter": 280,
        "instagram": 2200,
        "facebook": 63206,
        "linkedin": 3000,
        "tiktok": 2200,
        "youtube": 5000,
    }

    cta_by_goal = {
        "new_users": "הצטרפו אלינו עכשיו! לחצו על הקישור בביו 👆",
        "brand_awareness": "שתפו עם חברים שצריכים לדעת על זה! 🔄",
        "lead_generation": "השאירו פרטים בהודעה פרטית ונחזור אליכם ✉️",
        "sales": "הזמינו עכשיו - מבצע מוגבל! 🛒",
        "engagement": "ספרו לנו בתגובות - מה דעתכם? 💬",
        "traffic": "לקריאה מלאה - הקישור בביו 🔗",
    }

    templates = {
        "professional": f"💡 {topic}\n\nאנחנו ב[שם העסק] מאמינים ש...\n\n✅ יתרון 1\n✅ יתרון 2\n✅ יתרון 3",
        "casual": f"היי חברים! 👋\n\nרצינו לשתף אתכם ב{topic}...\n\nמה אתם חושבים?",
        "inspirational": f"🌟 {topic}\n\n'ציטוט מעורר השראה'\n\nזה מה שמניע אותנו בכל יום...",
        "funny": f"😄 {topic}\n\nאתם לא תאמינו מה קרה לנו...\n\n(סיפור מצחיק קצר)",
    }

    content_template = templates.get(tone, templates["professional"])
    cta = cta_by_goal.get(goal, "") if include_cta else ""
    char_limit = platform_limits.get(platform, 1000)

    return {
        "content_template": content_template,
        "cta": cta,
        "platform": platform,
        "char_limit": char_limit,
        "goal": goal,
        "tone": tone,
        "instructions": f"Generate a {tone} post about '{topic}' for {platform} targeting {goal}. Max {char_limit} chars. Language: {language}. {'Include CTA: ' + cta if include_cta else ''}",
        "tips": [
            f"Keep it under {min(char_limit, 300)} characters for best engagement",
            "Use emojis to increase visual appeal",
            "Ask a question to boost comments",
            f"Best posting times for {platform}: check your analytics",
        ],
    }


def generate_hashtags(
    topic: str,
    platform: str,
    count: int = 15,
    include_hebrew: bool = True,
) -> Dict[str, Any]:
    """
    Generate relevant hashtags for a topic and platform.

    Args:
        topic: Topic to generate hashtags for
        platform: Target platform
        count: Number of hashtags to generate
        include_hebrew: Include Hebrew hashtags
    """
    topic_clean = topic.replace(" ", "").lower()

    # Platform-specific hashtag counts
    optimal_counts = {
        "instagram": 20,
        "twitter": 2,
        "linkedin": 5,
        "tiktok": 6,
        "facebook": 3,
        "youtube": 10,
    }

    base_tags = [
        f"#{topic_clean}",
        "#ישראל",
        "#עסקים",
        "#שיווק",
        "#יזמות",
        "#startup",
        "#business",
        "#marketing",
        "#socialmedia",
        "#digitalmarketing",
        "#branding",
        "#content",
        "#entrepreneur",
        "#growth",
        "#success",
    ]

    platform_specific = {
        "instagram": ["#instagood", "#photooftheday", "#reels", "#explore"],
        "tiktok": ["#fyp", "#foryoupage", "#viral", "#trending"],
        "linkedin": ["#networking", "#leadership", "#career", "#innovation"],
        "twitter": ["#trending", "#viral"],
        "youtube": ["#youtube", "#subscribe", "#youtuber"],
        "facebook": ["#facebook", "#community"],
    }

    all_tags = base_tags + platform_specific.get(platform, [])
    selected_tags = all_tags[:count]
    optimal = optimal_counts.get(platform, 10)

    return {
        "hashtags": selected_tags,
        "recommended_count": min(optimal, count),
        "platform": platform,
        "topic": topic,
        "tips": {
            "instagram": "Use 20-30 hashtags in first comment for best reach",
            "twitter": "1-2 hashtags perform best - don't overdo it",
            "linkedin": "3-5 professional hashtags are ideal",
            "tiktok": "Use 3-5 trending hashtags + niche ones",
            "facebook": "1-3 hashtags maximum",
            "youtube": "Use in description, not title",
        }.get(platform, "Use relevant hashtags"),
    }


def analyze_best_posting_time(
    platform: str,
    audience_location: str = "Israel",
    industry: str = "general",
) -> Dict[str, Any]:
    """
    Analyze and recommend the best times to post on a platform.

    Args:
        platform: Social media platform
        audience_location: Where the target audience is located
        industry: Business industry/niche
    """
    # Research-based optimal posting times for Israeli audience
    optimal_times = {
        "facebook": {
            "best_days": ["Tuesday", "Wednesday", "Thursday"],
            "best_times": ["09:00-11:00", "13:00-14:00", "19:00-21:00"],
            "avoid": ["Saturday morning", "Friday afternoon"],
            "timezone": "Asia/Jerusalem",
            "hebrew": {
                "ימים_מומלצים": ["שלישי", "רביעי", "חמישי"],
                "שעות_מומלצות": ["09:00-11:00", "13:00-14:00", "19:00-21:00"],
            }
        },
        "instagram": {
            "best_days": ["Monday", "Tuesday", "Friday"],
            "best_times": ["08:00-09:00", "12:00-13:00", "17:00-18:00", "21:00-22:00"],
            "avoid": ["Saturday", "Sunday morning"],
            "timezone": "Asia/Jerusalem",
            "hebrew": {
                "ימים_מומלצים": ["שני", "שלישי", "שישי"],
                "שעות_מומלצות": ["08:00-09:00", "12:00-13:00", "17:00-18:00", "21:00-22:00"],
            }
        },
        "twitter": {
            "best_days": ["Tuesday", "Wednesday", "Thursday"],
            "best_times": ["08:00-10:00", "12:00-13:00", "17:00-18:00"],
            "timezone": "Asia/Jerusalem",
        },
        "linkedin": {
            "best_days": ["Tuesday", "Wednesday", "Thursday"],
            "best_times": ["07:00-09:00", "12:00-13:00"],
            "avoid": ["Weekend", "Evening"],
            "timezone": "Asia/Jerusalem",
        },
        "tiktok": {
            "best_days": ["Tuesday", "Thursday", "Friday"],
            "best_times": ["07:00-09:00", "12:00-15:00", "19:00-23:00"],
            "timezone": "Asia/Jerusalem",
        },
        "youtube": {
            "best_days": ["Thursday", "Friday", "Saturday"],
            "best_times": ["12:00-16:00", "20:00-23:00"],
            "note": "YouTube posts take time to rank - consistency is key",
            "timezone": "Asia/Jerusalem",
        },
    }

    platform_times = optimal_times.get(platform, {"best_times": ["09:00", "12:00", "19:00"]})

    return {
        "platform": platform,
        "audience_location": audience_location,
        "recommendation": platform_times,
        "frequency_recommendation": {
            "facebook": "1-2 posts per day",
            "instagram": "1-2 posts per day + 5-7 stories",
            "twitter": "3-5 tweets per day",
            "linkedin": "1 post per day (weekdays)",
            "tiktok": "1-3 videos per day",
            "youtube": "1-3 videos per week",
        }.get(platform, "1-2 times per day"),
    }


def create_content_calendar(
    goal: str,
    platforms: List[str],
    weeks: int = 4,
    topics: List[str] = None,
    business_name: str = "",
) -> Dict[str, Any]:
    """
    Create a content calendar with posting schedule and ideas.

    Args:
        goal: Marketing goal
        platforms: Target platforms
        weeks: Number of weeks to plan
        topics: Content topics/themes
        business_name: Business name for personalization
    """
    if not topics:
        topics = ["tips", "behind the scenes", "testimonials", "product showcase", "industry news", "Q&A"]

    content_types = {
        "new_users": ["introductory offers", "explainer posts", "testimonials", "how-to guides"],
        "brand_awareness": ["brand story", "values posts", "team introductions", "milestones"],
        "lead_generation": ["free resources", "webinar invitations", "case studies", "demos"],
        "sales": ["product showcases", "limited offers", "comparison posts", "reviews"],
        "engagement": ["polls", "questions", "challenges", "user-generated content"],
    }

    calendar_entries = []
    start_date = datetime.now()

    for week in range(weeks):
        for platform in platforms:
            # Add 2-3 posts per week per platform
            for day_offset in [1, 4, 6]:
                post_date = start_date + timedelta(weeks=week, days=day_offset)
                topic = topics[(week + day_offset) % len(topics)]
                content_type = content_types.get(goal, ["general content"])[(week + day_offset) % len(content_types.get(goal, ["general content"]))]

                calendar_entries.append({
                    "date": post_date.strftime("%Y-%m-%d"),
                    "day": post_date.strftime("%A"),
                    "platform": platform,
                    "content_type": content_type,
                    "topic_idea": topic,
                    "goal": goal,
                    "recommended_time": analyze_best_posting_time(platform)["recommendation"].get("best_times", ["09:00"])[0],
                    "notes": f"Week {week + 1} - {goal.replace('_', ' ').title()} campaign",
                })

    return {
        "calendar": calendar_entries,
        "total_posts": len(calendar_entries),
        "weeks": weeks,
        "platforms": platforms,
        "goal": goal,
        "summary": {
            "posts_per_week": len(calendar_entries) // weeks if weeks > 0 else 0,
            "platforms_covered": len(platforms),
            "content_variety": len(set(e["content_type"] for e in calendar_entries)),
        },
    }


def suggest_content_ideas(
    business_type: str,
    goal: str,
    platform: str,
    count: int = 10,
) -> Dict[str, Any]:
    """
    Suggest specific content ideas based on business type and goal.

    Args:
        business_type: Type of business (e.g., restaurant, tech startup, retail)
        goal: Marketing goal
        platform: Target platform
        count: Number of ideas to generate
    """
    ideas_by_goal = {
        "new_users": [
            "סרטון הכרה: מי אנחנו ומה אנחנו עושים",
            "5 סיבות לעבוד איתנו",
            "עדויות לקוחות מרוצים",
            "מבצע הכרות מיוחד לעוקבים חדשים",
            "שאלות ותשובות - הכל על העסק שלנו",
        ],
        "brand_awareness": [
            "סיפור הקמת העסק",
            "מאחורי הקלעים - יום בחיי העסק",
            "הערכים שמנחים אותנו",
            "חגיגת אבן דרך חשובה",
            "פרויקט שאנחנו גאים בו",
        ],
        "lead_generation": [
            "מדריך חינמי להורדה",
            "וובינר בחינם - הירשמו עכשיו",
            "שאלון: מה הצרכים שלך?",
            "תיק עבודות - תוצאות שהשגנו",
            "ייעוץ ראשוני חינם",
        ],
        "sales": [
            "מבצע מוגבל - 24 שעות בלבד",
            "השוואת מוצרים - למה לבחור בנו",
            "ביקורות 5 כוכבים מלקוחות",
            "לפני ואחרי - תוצאות אמיתיות",
            "חבילה מיוחדת לחודש זה",
        ],
        "engagement": [
            "שאלה לקהל: מה מעדיפים?",
            "משחק ניחושים",
            "אתגר - שתפו אתכם",
            "בחירת הקהל: איזה מוצר חדש?",
            "Fill in the blank: ___",
        ],
    }

    return {
        "ideas": (ideas_by_goal.get(goal, ideas_by_goal["engagement"]) * 2)[:count],
        "business_type": business_type,
        "goal": goal,
        "platform": platform,
        "tip": f"Mix these content types throughout your {platform} feed for best results",
    }
