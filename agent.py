"""
AI Advertising Agent - Powered by Claude claude-opus-4-6
The brain of the advertising assistant that orchestrates all social media platforms.
"""
from __future__ import annotations
import json
import logging
import asyncio
from typing import List, Dict, Any, Optional

import anthropic

from config import config, SUPPORTED_PLATFORMS
from models.campaign import Campaign, MarketingGoal, PlatformRecommendation
from models.platform import PlatformAccount
from platforms.facebook import FacebookPlatform
from platforms.instagram import InstagramPlatform
from platforms.twitter import TwitterPlatform
from platforms.linkedin import LinkedInPlatform
from platforms.youtube import YoutubePlatform
from platforms.tiktok import TikTokPlatform
import tools.social_tools as social_tools
import tools.analytics_tools as analytics_tools
from tools.content_tools import (
    generate_post_content, generate_hashtags,
    analyze_best_posting_time, create_content_calendar,
    suggest_content_ideas,
)
from tools.advertising_tools import (
    setup_facebook_ad_campaign, setup_google_ads_campaign,
    estimate_ad_budget, analyze_competitor_ads,
)

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """אתה עוזר פרסום AI מקצועי ואישי. השם שלך הוא "מפרסם" - עוזר הפרסום החכם.

## היכולות שלך:
🌐 **חיבור לרשתות חברתיות**: פייסבוק, אינסטגרם, טוויטר/X, לינקדאין, יוטיוב, טיקטוק
📊 **ניתוח וגיוס קהל יעד**: מציאת משתמשים, קבוצות וערוצים רלוונטיים
✍️ **יצירת תוכן**: כתיבת פוסטים, האשטגים ולוח תוכן
📤 **פרסום אוטומטי**: העלאת פוסטים, סרטונים ותמונות לכל הפלטפורמות
💬 **מעורבות פעילה**: הגבה לפוסטים, כתוב תגובות, עשה לייקים ועקוב אחרי משתמשים
🎯 **ניתוח ביצועים**: מעקב אחרי תוצאות ואופטימיזציה
💡 **המלצות**: הצע פלטפורמות חדשות ואסטרטגיות פרסום
💰 **פרסום ממומן**: הנחיה בהקמת קמפיינים בגוגל אדס ופייסבוק אדס

## עקרונות העבודה:
1. תמיד שאל שאלות הבהרה לפני פעולה
2. הסבר מה אתה עומד לעשות לפני שאתה עושה זאת
3. דווח על תוצאות בצורה ברורה
4. המלץ על השלבים הבאים לאחר כל פעולה
5. התאם את התוכן לקהל הישראלי (תוך שמירה על אפשרות לפרסום בינלאומי)
6. שמור על אתיקה - אל תשלח ספאם ואל תפר תנאי שימוש

## כשמשתמש שואל אותך:
- אם הוא רוצה לפרסם: שאל מה לפרסם, לאן, ומתי
- אם הוא רוצה לגדול: שאל מה המטרה ומה הקהל
- אם הוא רוצה ניתוח: בקש גישה לנתוני הפלטפורמות
- אם הוא רוצה עצה: תן המלצות מבוססות על הנתונים שיש לך

## שפה:
- עברית כברירת מחדל
- עבור לאנגלית כאשר מתאים (פוסטים לקהל בינלאומי)
- היה ידידותי, מקצועי ומעורר השראה

You are a professional AI advertising assistant named "מפרסם" (Mefaresem).
You help businesses manage their social media presence and advertising campaigns.
Always be helpful, proactive, and guide users step by step."""


# Tool definitions for Claude
TOOLS = [
    {
        "name": "post_content",
        "description": "פרסם תוכן לאחת או יותר מהרשתות החברתיות המחוברות. Post content to social media platforms.",
        "input_schema": {
            "type": "object",
            "properties": {
                "platforms": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "רשימת פלטפורמות: facebook, instagram, twitter, linkedin, youtube, tiktok",
                },
                "content": {"type": "string", "description": "תוכן הפוסט"},
                "media_urls": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "קישורים לתמונות או סרטונים",
                },
                "groups": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "מזהי קבוצות לפרסום ממוקד",
                },
                "hashtags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "האשטגים להוסיף לפוסט",
                },
            },
            "required": ["platforms", "content"],
        },
    },
    {
        "name": "find_relevant_users",
        "description": "מצא משתמשים רלוונטיים לנושא מסוים ברשת חברתית. Find relevant users on a platform.",
        "input_schema": {
            "type": "object",
            "properties": {
                "platform": {"type": "string", "description": "שם הפלטפורמה"},
                "keywords": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "מילות מפתח לחיפוש",
                },
                "limit": {"type": "integer", "default": 20, "description": "מספר משתמשים מרבי"},
            },
            "required": ["platform", "keywords"],
        },
    },
    {
        "name": "find_relevant_groups",
        "description": "מצא קבוצות, קהילות או האשטגים רלוונטיים. Find relevant groups or communities.",
        "input_schema": {
            "type": "object",
            "properties": {
                "platform": {"type": "string", "description": "שם הפלטפורמה"},
                "keywords": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "מילות מפתח לחיפוש",
                },
                "limit": {"type": "integer", "default": 10, "description": "מספר קבוצות מרבי"},
            },
            "required": ["platform", "keywords"],
        },
    },
    {
        "name": "follow_user",
        "description": "עקוב אחרי משתמש או שלח בקשת חברות. Follow a user or send connection request.",
        "input_schema": {
            "type": "object",
            "properties": {
                "platform": {"type": "string", "description": "שם הפלטפורמה"},
                "user_id": {"type": "string", "description": "מזהה המשתמש"},
                "username": {"type": "string", "description": "שם המשתמש (לתיעוד)"},
            },
            "required": ["platform", "user_id"],
        },
    },
    {
        "name": "send_connection_request",
        "description": "שלח בקשת חיבור/חברות עם הודעה אישית. Send a personalized connection request.",
        "input_schema": {
            "type": "object",
            "properties": {
                "platform": {"type": "string"},
                "user_id": {"type": "string"},
                "message": {"type": "string", "description": "הודעה אישית"},
                "username": {"type": "string"},
            },
            "required": ["platform", "user_id"],
        },
    },
    {
        "name": "comment_on_post",
        "description": "הגב על פוסט ברשת חברתית. Comment on a social media post.",
        "input_schema": {
            "type": "object",
            "properties": {
                "platform": {"type": "string"},
                "post_id": {"type": "string", "description": "מזהה הפוסט"},
                "comment": {"type": "string", "description": "תוכן התגובה"},
            },
            "required": ["platform", "post_id", "comment"],
        },
    },
    {
        "name": "like_post",
        "description": "עשה לייק לפוסט. Like a post on social media.",
        "input_schema": {
            "type": "object",
            "properties": {
                "platform": {"type": "string"},
                "post_id": {"type": "string"},
            },
            "required": ["platform", "post_id"],
        },
    },
    {
        "name": "get_account_metrics",
        "description": "קבל מדדי ביצועים לחשבון ברשת חברתית. Get performance metrics for a platform.",
        "input_schema": {
            "type": "object",
            "properties": {
                "platform": {"type": "string"},
                "days": {"type": "integer", "default": 30, "description": "מספר ימים לניתוח"},
            },
            "required": ["platform"],
        },
    },
    {
        "name": "get_platform_feed",
        "description": "קבל פוסטים אחרונים מהפיד של פלטפורמה. Get recent posts from a platform feed.",
        "input_schema": {
            "type": "object",
            "properties": {
                "platform": {"type": "string"},
                "limit": {"type": "integer", "default": 10},
            },
            "required": ["platform"],
        },
    },
    {
        "name": "search_hashtags",
        "description": "חפש האשטגים רלוונטיים לנושא. Search for relevant hashtags.",
        "input_schema": {
            "type": "object",
            "properties": {
                "platform": {"type": "string"},
                "topic": {"type": "string", "description": "הנושא לחיפוש האשטגים"},
                "count": {"type": "integer", "default": 15},
            },
            "required": ["platform", "topic"],
        },
    },
    {
        "name": "get_campaign_performance",
        "description": "קבל ביצועי קמפיין כולל על כל הפלטפורמות. Get overall campaign performance.",
        "input_schema": {
            "type": "object",
            "properties": {
                "campaign_id": {"type": "string"},
                "platforms": {"type": "array", "items": {"type": "string"}},
                "days": {"type": "integer", "default": 30},
            },
        },
    },
    {
        "name": "compare_platforms_performance",
        "description": "השווה ביצועים בין פלטפורמות. Compare performance across platforms.",
        "input_schema": {
            "type": "object",
            "properties": {
                "days": {"type": "integer", "default": 30},
            },
        },
    },
    {
        "name": "get_audience_insights",
        "description": "קבל תובנות על קהל היעד. Get audience demographic insights.",
        "input_schema": {
            "type": "object",
            "properties": {
                "platform": {"type": "string"},
            },
            "required": ["platform"],
        },
    },
    {
        "name": "generate_post_content",
        "description": "צור תבנית תוכן לפוסט לפי מטרה ופלטפורמה. Generate post content template.",
        "input_schema": {
            "type": "object",
            "properties": {
                "goal": {"type": "string", "description": "מטרת השיווק"},
                "topic": {"type": "string", "description": "נושא הפוסט"},
                "platform": {"type": "string"},
                "tone": {"type": "string", "default": "professional"},
                "language": {"type": "string", "default": "hebrew"},
            },
            "required": ["goal", "topic", "platform"],
        },
    },
    {
        "name": "generate_hashtags",
        "description": "צור האשטגים לפוסט. Generate hashtags for a post.",
        "input_schema": {
            "type": "object",
            "properties": {
                "topic": {"type": "string"},
                "platform": {"type": "string"},
                "count": {"type": "integer", "default": 15},
            },
            "required": ["topic", "platform"],
        },
    },
    {
        "name": "create_content_calendar",
        "description": "צור לוח תוכן לשבועות הקרובים. Create a content calendar.",
        "input_schema": {
            "type": "object",
            "properties": {
                "goal": {"type": "string"},
                "platforms": {"type": "array", "items": {"type": "string"}},
                "weeks": {"type": "integer", "default": 4},
                "topics": {"type": "array", "items": {"type": "string"}},
                "business_name": {"type": "string"},
            },
            "required": ["goal", "platforms"],
        },
    },
    {
        "name": "analyze_best_posting_time",
        "description": "נתח ומצא את הזמנים הטובים ביותר לפרסום. Analyze best posting times.",
        "input_schema": {
            "type": "object",
            "properties": {
                "platform": {"type": "string"},
                "audience_location": {"type": "string", "default": "Israel"},
                "industry": {"type": "string", "default": "general"},
            },
            "required": ["platform"],
        },
    },
    {
        "name": "suggest_content_ideas",
        "description": "הצע רעיונות לתוכן לפי סוג עסק ומטרה. Suggest content ideas.",
        "input_schema": {
            "type": "object",
            "properties": {
                "business_type": {"type": "string"},
                "goal": {"type": "string"},
                "platform": {"type": "string"},
                "count": {"type": "integer", "default": 10},
            },
            "required": ["business_type", "goal", "platform"],
        },
    },
    {
        "name": "setup_facebook_ad_campaign",
        "description": "הנחיה בהקמת קמפיין פרסום בפייסבוק אדס. Guide through Facebook Ads setup.",
        "input_schema": {
            "type": "object",
            "properties": {
                "goal": {"type": "string"},
                "daily_budget": {"type": "number", "description": "תקציב יומי בשקלים"},
                "target_audience": {"type": "object", "description": "פרטי קהל היעד"},
                "ad_creative_description": {"type": "string"},
            },
            "required": ["goal", "daily_budget", "target_audience"],
        },
    },
    {
        "name": "setup_google_ads_campaign",
        "description": "הנחיה בהקמת קמפיין גוגל אדס. Guide through Google Ads setup.",
        "input_schema": {
            "type": "object",
            "properties": {
                "goal": {"type": "string"},
                "daily_budget": {"type": "number"},
                "keywords": {"type": "array", "items": {"type": "string"}},
                "landing_page_url": {"type": "string"},
                "location": {"type": "string", "default": "Israel"},
            },
            "required": ["goal", "daily_budget", "keywords"],
        },
    },
    {
        "name": "estimate_ad_budget",
        "description": "הערך תקציב פרסום לפי מטרה ויעד. Estimate advertising budget.",
        "input_schema": {
            "type": "object",
            "properties": {
                "goal": {"type": "string"},
                "platform": {"type": "string"},
                "target_reach": {"type": "integer", "description": "כמה אנשים לגעת"},
                "industry": {"type": "string", "default": "general"},
            },
            "required": ["goal", "platform", "target_reach"],
        },
    },
    {
        "name": "analyze_competitor_ads",
        "description": "נתח פרסום של מתחרים בתחום. Analyze competitor advertising.",
        "input_schema": {
            "type": "object",
            "properties": {
                "industry": {"type": "string"},
                "platform": {"type": "string"},
                "location": {"type": "string", "default": "Israel"},
            },
            "required": ["industry", "platform"],
        },
    },
    {
        "name": "get_platform_recommendations",
        "description": "קבל המלצות על פלטפורמות חדשות לפרסום. Get platform recommendations.",
        "input_schema": {
            "type": "object",
            "properties": {
                "connected_platforms": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "פלטפורמות מחוברות כעת",
                },
                "goals": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "מטרות שיווקיות",
                },
                "business_type": {"type": "string"},
                "target_audience": {"type": "string"},
            },
            "required": ["connected_platforms", "goals"],
        },
    },
    {
        "name": "track_lead_conversions",
        "description": "עקוב אחרי המרות ולידים. Track lead conversions.",
        "input_schema": {
            "type": "object",
            "properties": {
                "campaign_id": {"type": "string"},
            },
        },
    },
]


class AdvertisingAgent:
    """
    AI Advertising Agent powered by Claude claude-opus-4-6.
    Manages social media presence and advertising campaigns.
    """

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
        self.conversation_history: List[Dict[str, Any]] = []
        self.connected_platforms: Dict[str, Any] = {}
        self.current_campaign: Optional[Campaign] = None

        # Initialize platform instances
        self.platforms = {
            "facebook": FacebookPlatform(),
            "instagram": InstagramPlatform(),
            "twitter": TwitterPlatform(),
            "linkedin": LinkedInPlatform(),
            "youtube": YoutubePlatform(),
            "tiktok": TikTokPlatform(),
        }

        # Register platforms with tool modules
        for name, platform in self.platforms.items():
            social_tools.register_platform(name, platform)
            analytics_tools.register_platform(name, platform)

    async def connect_platform(self, platform_name: str) -> Optional[PlatformAccount]:
        """Connect to a social media platform and return account info."""
        platform = self.platforms.get(platform_name)
        if not platform:
            logger.error(f"Unknown platform: {platform_name}")
            return None

        try:
            account = await platform.connect()
            self.connected_platforms[platform_name] = account
            logger.info(f"Connected to {platform_name}: @{account.username}")
            return account
        except Exception as e:
            logger.error(f"Failed to connect to {platform_name}: {e}")
            return None

    async def connect_all_platforms(self) -> Dict[str, PlatformAccount]:
        """Attempt to connect to all configured platforms."""
        results = {}
        for platform_name in self.platforms:
            account = await self.connect_platform(platform_name)
            if account and account.is_connected:
                results[platform_name] = account
        return results

    async def chat(self, user_message: str) -> str:
        """
        Send a message to the agent and get a response.
        Handles the full tool-use loop with Claude.
        """
        self.conversation_history.append({
            "role": "user",
            "content": user_message,
        })

        messages = self.conversation_history.copy()

        while True:
            response = self.client.messages.create(
                model="claude-opus-4-6",
                max_tokens=4096,
                thinking={"type": "adaptive"},
                system=SYSTEM_PROMPT,
                tools=TOOLS,
                messages=messages,
            )

            # Build assistant message content (preserve all block types)
            assistant_content = []
            for block in response.content:
                if block.type == "thinking":
                    assistant_content.append({"type": "thinking", "thinking": block.thinking, "signature": block.signature})
                elif block.type == "text":
                    assistant_content.append({"type": "text", "text": block.text})
                elif block.type == "tool_use":
                    assistant_content.append({
                        "type": "tool_use",
                        "id": block.id,
                        "name": block.name,
                        "input": block.input,
                    })

            messages.append({"role": "assistant", "content": assistant_content})

            # Check if we're done
            if response.stop_reason == "end_turn":
                # Extract final text response
                final_text = ""
                for block in response.content:
                    if block.type == "text":
                        final_text += block.text

                # Update conversation history with text only (for multi-turn)
                self.conversation_history.append({
                    "role": "assistant",
                    "content": final_text,
                })
                return final_text

            # Handle tool use
            if response.stop_reason == "tool_use":
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        result = await self._process_tool_call(block.name, block.input)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": json.dumps(result, ensure_ascii=False, indent=2),
                        })

                messages.append({"role": "user", "content": tool_results})
            else:
                # Unexpected stop reason
                break

        return "אירעה שגיאה בעיבוד הבקשה. אנא נסה שוב."

    async def _process_tool_call(self, tool_name: str, tool_input: Dict[str, Any]) -> Any:
        """Dispatch tool calls to the appropriate functions."""
        logger.info(f"Executing tool: {tool_name} with input: {json.dumps(tool_input, ensure_ascii=False)[:200]}")

        try:
            # Social tools
            if tool_name == "post_content":
                return await social_tools.post_content(**tool_input)
            elif tool_name == "find_relevant_users":
                return await social_tools.find_relevant_users(**tool_input)
            elif tool_name == "find_relevant_groups":
                return await social_tools.find_relevant_groups(**tool_input)
            elif tool_name == "follow_user":
                return await social_tools.follow_user(**tool_input)
            elif tool_name == "send_connection_request":
                return await social_tools.send_connection_request(**tool_input)
            elif tool_name == "comment_on_post":
                return await social_tools.comment_on_post(**tool_input)
            elif tool_name == "like_post":
                return await social_tools.like_post(**tool_input)
            elif tool_name == "get_account_metrics":
                return await social_tools.get_account_metrics(**tool_input)
            elif tool_name == "get_platform_feed":
                return await social_tools.get_platform_feed(**tool_input)
            elif tool_name == "search_hashtags":
                return await social_tools.search_hashtags(**tool_input)

            # Analytics tools
            elif tool_name == "get_campaign_performance":
                return await analytics_tools.get_campaign_performance(**tool_input)
            elif tool_name == "compare_platforms_performance":
                return await analytics_tools.compare_platforms_performance(**tool_input)
            elif tool_name == "get_audience_insights":
                return await analytics_tools.get_audience_insights(**tool_input)
            elif tool_name == "track_lead_conversions":
                return await analytics_tools.track_lead_conversions(**tool_input)

            # Content tools
            elif tool_name == "generate_post_content":
                return generate_post_content(**tool_input)
            elif tool_name == "generate_hashtags":
                return generate_hashtags(**tool_input)
            elif tool_name == "create_content_calendar":
                return create_content_calendar(**tool_input)
            elif tool_name == "analyze_best_posting_time":
                return analyze_best_posting_time(**tool_input)
            elif tool_name == "suggest_content_ideas":
                return suggest_content_ideas(**tool_input)

            # Advertising tools
            elif tool_name == "setup_facebook_ad_campaign":
                return setup_facebook_ad_campaign(**tool_input)
            elif tool_name == "setup_google_ads_campaign":
                return setup_google_ads_campaign(**tool_input)
            elif tool_name == "estimate_ad_budget":
                return estimate_ad_budget(**tool_input)
            elif tool_name == "analyze_competitor_ads":
                return analyze_competitor_ads(**tool_input)

            # Platform recommendations
            elif tool_name == "get_platform_recommendations":
                return self._get_platform_recommendations(**tool_input)

            else:
                return {"error": f"Unknown tool: {tool_name}"}

        except Exception as e:
            logger.error(f"Tool {tool_name} failed: {e}", exc_info=True)
            return {"error": str(e), "tool": tool_name}

    def _get_platform_recommendations(
        self,
        connected_platforms: List[str],
        goals: List[str],
        business_type: str = "general",
        target_audience: str = "general",
    ) -> Dict[str, Any]:
        """Recommend new platforms based on goals and current setup."""
        all_platforms = list(SUPPORTED_PLATFORMS.keys())
        missing_platforms = [p for p in all_platforms if p not in connected_platforms]

        recommendations = []
        for platform_name in missing_platforms:
            platform_info = SUPPORTED_PLATFORMS[platform_name]
            score = 0
            reasons = []

            # Score based on goals
            if "new_users" in goals and platform_name in ["tiktok", "instagram"]:
                score += 3
                reasons.append("מצוין לגיוס משתמשים חדשים")
            if "lead_generation" in goals and platform_name in ["linkedin", "facebook"]:
                score += 3
                reasons.append("הפלטפורמה הטובה ביותר ליצירת לידים")
            if "brand_awareness" in goals and platform_name in ["instagram", "youtube", "tiktok"]:
                score += 2
                reasons.append("חשיפה ויזואלית גבוהה למותגים")
            if "sales" in goals and platform_name in ["facebook", "instagram"]:
                score += 2
                reasons.append("תמיכה בחנויות ופרסום ממומן לרכישות")

            if score > 0:
                recommendations.append({
                    "platform": platform_name,
                    "platform_name_he": platform_info["name_he"],
                    "icon": platform_info["icon"],
                    "score": score,
                    "reasons": reasons,
                    "best_for": platform_info["best_for"],
                    "features": platform_info["features"],
                    "docs_url": platform_info["docs_url"],
                })

        # Sort by score
        recommendations.sort(key=lambda x: x["score"], reverse=True)

        return {
            "connected_platforms": connected_platforms,
            "missing_platforms": missing_platforms,
            "recommendations": recommendations[:5],  # Top 5
            "top_recommendation": recommendations[0] if recommendations else None,
            "tip": "התחל עם הפלטפורמה בעלת הדירוג הגבוה ביותר עבור המטרות שלך",
        }

    def clear_history(self):
        """Clear conversation history."""
        self.conversation_history = []

    async def close(self):
        """Close all platform connections."""
        for platform in self.platforms.values():
            await platform.close()
