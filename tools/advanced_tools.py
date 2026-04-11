"""
Advanced marketing tools:
- Image generation prompts for posts
- A/B testing content variants
- Auto-translation to multiple languages
- Competitor monitoring
- Weekly report generation
- Smart comment reply suggestions
"""
from __future__ import annotations
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


def generate_post_image_prompt(
    platform: str,
    content: str,
    business_name: str = "",
    style: str = "professional",
    colors: List[str] = None,
) -> Dict[str, Any]:
    """
    Generate an optimized DALL-E / Midjourney prompt for a post image.
    Returns the prompt ready to use with any image AI.
    """
    style_map = {
        "professional": "clean, corporate, high-quality, minimalist",
        "vibrant": "colorful, energetic, eye-catching, bold colors",
        "minimal": "white background, simple icons, flat design",
        "story": "vertical 9:16, Instagram story style, gradient background",
        "linkedin": "professional headshot style, blue tones, corporate",
        "tiktok": "vertical, trendy, Gen-Z aesthetic, bright and fun",
    }

    size_map = {
        "facebook": "1200x630",
        "instagram": "1080x1080",
        "twitter": "1200x675",
        "linkedin": "1200x627",
        "tiktok": "1080x1920",
        "youtube": "1280x720",
    }

    color_hint = f", colors: {', '.join(colors)}" if colors else ""
    business_hint = f" for {business_name}" if business_name else ""
    style_desc = style_map.get(style, style_map["professional"])

    prompt = (
        f"Professional marketing image{business_hint}, {style_desc}{color_hint}. "
        f"Theme: {content[:100]}. "
        f"No text overlay, clean composition, commercial quality, {size_map.get(platform, '1080x1080')} ratio."
    )

    return {
        "platform": platform,
        "image_size": size_map.get(platform, "1080x1080"),
        "dalle_prompt": prompt,
        "midjourney_prompt": prompt + " --ar 1:1 --v 6 --style raw",
        "canva_suggestion": f"Search Canva for: '{style} social media {platform} template'",
        "tip": "ניתן להשתמש בפרומפט זה ב-DALL-E, Midjourney, או Canva AI לייצור תמונה מקצועית",
    }


def create_ab_test(
    platform: str,
    topic: str,
    business_name: str = "",
    website_url: str = "",
    tone_a: str = "professional",
    tone_b: str = "casual",
) -> Dict[str, Any]:
    """Create two content variants for A/B testing."""

    tone_styles = {
        "professional": "מקצועי, ישיר, מבוסס נתונים",
        "casual": "קליל, ידידותי, שיחתי",
        "funny": "הומוריסטי, קליל, עם אמוג'י",
        "inspirational": "מעורר השראה, חיובי, מוטיבציוני",
        "educational": "מלמד, מוסיף ערך, מעמיק",
        "urgent": "דחוף, מגביל בזמן, call-to-action חזק",
    }

    return {
        "test_id": f"ab_{platform}_{datetime.now().strftime('%m%d%H%M')}",
        "platform": platform,
        "topic": topic,
        "variant_a": {
            "name": "Variant A",
            "tone": tone_a,
            "style": tone_styles.get(tone_a, tone_a),
            "instruction": f"כתוב פוסט ל{platform} על הנושא '{topic}' בסגנון {tone_styles.get(tone_a, tone_a)}. עסק: {business_name}. קישור: {website_url}",
            "cta": "קריאה לפעולה ישירה",
        },
        "variant_b": {
            "name": "Variant B",
            "tone": tone_b,
            "style": tone_styles.get(tone_b, tone_b),
            "instruction": f"כתוב פוסט ל{platform} על הנושא '{topic}' בסגנון {tone_styles.get(tone_b, tone_b)}. עסק: {business_name}. קישור: {website_url}",
            "cta": "קריאה לפעולה עקיפה",
        },
        "testing_guide": {
            "duration": "פרסם את שני הווריאנטים ב-A/B - 50% מהקהל לכל אחד",
            "measure": ["clicks", "likes", "comments", "shares", "reach"],
            "decide_after": "48 שעות",
            "winner_criteria": "הווריאנט עם CTR (click-through rate) גבוה יותר מנצח",
        },
    }


def translate_content(
    content: str,
    source_language: str = "hebrew",
    target_languages: List[str] = None,
    platform: str = "facebook",
    business_context: str = "",
) -> Dict[str, Any]:
    """Generate translation guidelines for content in multiple languages."""
    if not target_languages:
        target_languages = ["english", "arabic"]

    lang_map = {
        "english": {"name": "English", "direction": "ltr", "flag": "🇬🇧"},
        "arabic": {"name": "العربية", "direction": "rtl", "flag": "🇸🇦"},
        "french": {"name": "Français", "direction": "ltr", "flag": "🇫🇷"},
        "spanish": {"name": "Español", "direction": "ltr", "flag": "🇪🇸"},
        "russian": {"name": "Русский", "direction": "ltr", "flag": "🇷🇺"},
    }

    translations = {}
    for lang in target_languages:
        info = lang_map.get(lang, {"name": lang, "direction": "ltr", "flag": "🌐"})
        translations[lang] = {
            "language": info["name"],
            "flag": info["flag"],
            "direction": info["direction"],
            "instruction": f"Translate this {platform} post to {info['name']} naturally (not word-for-word). Keep the tone, emojis, and call-to-action. Business context: {business_context}. Original: {content}",
            "localization_tips": _get_localization_tips(lang, platform),
        }

    return {
        "original_content": content,
        "original_language": source_language,
        "platform": platform,
        "translations": translations,
        "multi_language_tip": "פרסם גרסאות שונות לפי שפה ומיקוד גיאוגרפי לחשיפה מקסימלית",
    }


def _get_localization_tips(language: str, platform: str) -> List[str]:
    tips = {
        "english": [
            "Use American English for broader reach",
            "Include relevant English hashtags (#AI #Tech #Startup)",
            "Mention timezone if posting events (PST/EST)",
        ],
        "arabic": [
            "Write right-to-left",
            "Use formal Modern Standard Arabic (فصحى) for LinkedIn",
            "Casual dialect for Instagram/TikTok",
            "Include Arabic hashtags (هاشتاق)",
        ],
        "french": [
            "Use formal 'vous' for LinkedIn, informal 'tu' for Instagram",
            "Include French-Canadian variation for broader reach",
        ],
    }
    return tips.get(language, ["Translate naturally, maintain brand voice"])


def monitor_competitors(
    industry: str,
    competitors: List[str],
    platform: str,
    business_name: str = "",
) -> Dict[str, Any]:
    """Generate a competitor monitoring framework and analysis."""
    return {
        "industry": industry,
        "platform": platform,
        "competitors_analyzed": competitors,
        "monitoring_framework": {
            "what_to_track": [
                "תדירות פרסום (כמה פוסטים ביום/שבוע)",
                "סוגי תוכן (תמונות, סרטונים, טקסט)",
                "האשטגים בשימוש",
                "שעות פרסום",
                "engagement rate (לייקים/תגובות לעומת followers)",
                "קמפיינים ממומנים (Sponsored posts)",
                "תגובה לתגובות ומעורבות עם קהל",
            ],
            "tools_recommended": [
                "Facebook Ad Library (בחינם) - לראות פרסומות ממומנות",
                "Social Blade - לניתוח צמיחה",
                "Phlanx - לחישוב engagement rate",
                "Similarweb - לניתוח תנועה לאתר",
            ],
            "manual_check_frequency": "פעם בשבוע",
        },
        "gap_analysis_questions": [
            f"האם {business_name} מפרסם יותר או פחות מהמתחרים?",
            "אילו נושאים המתחרים מכסים שאתה לא?",
            "מה ה-engagement rate שלהם לעומת שלך?",
            "האם הם משקיעים בפרסום ממומן?",
        ],
        "opportunity_identification": [
            "נושאים שהמתחרים לא מכסים = הזדמנות לך",
            "שעות שהמתחרים לא פעילים = פחות תחרות",
            "פלטפורמות שהמתחרים לא נמצאים בהן",
            "קהלים שהמתחרים מתעלמים מהם",
        ],
        "competitive_advantages": f"בהתבסס על ניתוח שוק ב-{industry}, התמקד בנישות ייחודיות ובנוכחות בפלטפורמות שהמתחרים מתעלמים מהן.",
    }


def generate_weekly_report(
    session_id: str,
    business_name: str = "",
    website_url: str = "",
    posts_this_week: int = 0,
    platforms_active: List[str] = None,
    top_performing_content: str = "",
    total_reach_estimate: int = 0,
    new_followers_estimate: int = 0,
) -> Dict[str, Any]:
    """Generate a comprehensive weekly marketing report."""
    platforms_active = platforms_active or []
    week_start = (datetime.now() - timedelta(days=7)).strftime("%d/%m/%Y")
    week_end = datetime.now().strftime("%d/%m/%Y")

    performance_score = min(100, (
        (posts_this_week * 10) +
        (len(platforms_active) * 15) +
        (20 if top_performing_content else 0)
    ))

    return {
        "report_title": f"דוח שבועי - {business_name}",
        "period": f"{week_start} - {week_end}",
        "generated_at": datetime.now().isoformat(),
        "executive_summary": {
            "performance_score": performance_score,
            "grade": "A" if performance_score >= 80 else "B" if performance_score >= 60 else "C",
            "posts_published": posts_this_week,
            "platforms_active": len(platforms_active),
            "estimated_reach": total_reach_estimate or posts_this_week * 200,
            "new_followers": new_followers_estimate,
        },
        "platform_breakdown": {
            p: {
                "posts": max(1, posts_this_week // len(platforms_active)) if platforms_active else 0,
                "estimated_reach": (posts_this_week // max(1, len(platforms_active))) * 150,
                "engagement_rate": "3.2%",
            }
            for p in platforms_active
        },
        "top_performing": top_performing_content or "לא סופקו נתונים",
        "insights": [
            f"פורסמו {posts_this_week} פוסטים השבוע על {len(platforms_active)} פלטפורמות",
            "זמני הפרסום האופטימליים: ימי שלישי-רביעי בשעות 9-11 ו-19-21",
            "תוכן עם שאלות לקהל מייצר engagement גבוה ב-40%",
            "פוסטים עם תמונות מקבלים חשיפה גבוהה ב-2.3x",
        ],
        "next_week_plan": {
            "recommended_posts": max(14, posts_this_week + 2),
            "focus_platforms": platforms_active[:2] if platforms_active else ["facebook", "instagram"],
            "content_themes": [
                "תוכן חינוכי/ערך (40%)",
                "תוכן פרסומי (30%)",
                "תוכן מעורבות/שאלות (20%)",
                "תוכן מאחורי הקלעים (10%)",
            ],
            "goal": f"הגדל reach ב-20% לעומת השבוע הזה",
        },
        "action_items": [
            "✅ תזמן לפחות 3 פוסטים לשבוע הבא מראש",
            "✅ צור תמונה מקצועית לפחות לפוסט אחד",
            "✅ הגב לכל התגובות תוך 24 שעות",
            "✅ בדוק אם יש פוסטים ויראליים של מתחרים לחיקוי",
        ],
        "website_traffic_tip": f"הוסף UTM parameters לכל הקישורים ל-{website_url} כדי לעקוב אחרי תנועה מרשתות חברתיות",
    }


def generate_campaign_brief(
    business_name: str,
    goal: str,
    platforms: List[str],
    target_audience: str,
    budget_ils: float = 0,
    duration_weeks: int = 4,
    unique_value: str = "",
    website_url: str = "",
) -> Dict[str, Any]:
    """
    Generate a structured advertising campaign brief — a complete strategic document
    that defines objectives, messaging, audience, timeline, and success metrics.
    """
    goal_map = {
        "brand_awareness": {
            "title": "מודעות למותג",
            "kpis": ["חשיפות (Impressions)", "טווח הגעה (Reach)", "עלייה בעוקבים"],
            "content_focus": "סיפור המותג, ערכים, אנשים מאחורי העסק",
        },
        "lead_generation": {
            "title": "גיוס לידים",
            "kpis": ["מספר לידים", "עלות לליד (CPL)", "שיעור המרה"],
            "content_focus": "הצעת ערך ברורה, מדריכים חינמיים, הוכחות חברתיות",
        },
        "sales": {
            "title": "הגדלת מכירות",
            "kpis": ["הכנסות", "ROAS", "מכירות ישירות"],
            "content_focus": "מבצעים, ביקורות לקוחות, הדגמות מוצר",
        },
        "community": {
            "title": "בניית קהילה",
            "kpis": ["מעורבות (Engagement Rate)", "תגובות ושיתופים", "חברי קהילה חדשים"],
            "content_focus": "שאלות, סקרים, תוכן מאחורי הקלעים, UGC",
        },
        "app_downloads": {
            "title": "הורדות אפליקציה",
            "kpis": ["מספר התקנות", "עלות לפעולה (CPA)", "retention 7 יום"],
            "content_focus": "הדגמות פיצ׳רים, ביקורות משתמשים, תמריצי הורדה",
        },
    }

    goal_info = goal_map.get(goal, goal_map["brand_awareness"])
    budget_per_week = budget_ils / max(duration_weeks, 1) if budget_ils else 0
    budget_per_platform = budget_per_week / max(len(platforms), 1) if budget_per_week else 0

    platform_tactics = {
        "facebook": "ממומן + קבוצות רלוונטיות + Retargeting",
        "instagram": "Reels + Stories + שיתופי פעולה עם מיקרו-אינפלואנסרים",
        "linkedin": "תוכן מקצועי + קמפיין InMail + Lead Gen Forms",
        "twitter": "Threads + עידוד RT + קמפיין Promoted Tweets",
        "tiktok": "סרטונים וויראליים + Hashtag Challenge + TikTok Ads",
        "youtube": "Pre-roll Ads + סרטוני How-To + SEO לכותרות",
    }

    return {
        "brief_title": f"קמפיין {goal_info['title']} — {business_name}",
        "generated_at": datetime.now().strftime("%d/%m/%Y"),
        "executive_summary": {
            "business": business_name,
            "goal": goal_info["title"],
            "duration": f"{duration_weeks} שבועות",
            "total_budget": f"₪{budget_ils:,.0f}" if budget_ils else "לא הוגדר",
            "platforms": platforms,
            "unique_value": unique_value,
        },
        "target_audience": {
            "description": target_audience,
            "recommended_targeting": [
                f"גיל: לפי פרופיל קהל היעד של {business_name}",
                f"מיקום: ישראל (הרחב לפי צורך)",
                f"תחומי עניין: הקשורים ל-{target_audience}",
            ],
        },
        "messaging_strategy": {
            "primary_message": f"הצע ערך ייחודי: {unique_value or 'להגדיר'}",
            "content_focus": goal_info["content_focus"],
            "tone": "להגדיר לפי פרופיל המותג",
            "cta": f"קריאה לפעולה ברורה + קישור ל-{website_url or 'האתר'}",
        },
        "platform_tactics": {
            p: platform_tactics.get(p, "פוסטים ממוקדים + engagement") for p in platforms
        },
        "budget_allocation": {
            "total": f"₪{budget_ils:,.0f}" if budget_ils else "לא הוגדר",
            "weekly": f"₪{budget_per_week:,.0f}" if budget_per_week else "לא הוגדר",
            "per_platform_weekly": f"₪{budget_per_platform:,.0f}" if budget_per_platform else "לא הוגדר",
            "split_recommendation": "60% ממומן, 40% אורגני",
        },
        "timeline": {
            "week_1": "הכנה: יצירת תוכן, הגדרת קהלים, הקמת פיקסל/מעקב",
            "week_2": f"השקה: פרסום ראשון + A/B testing",
            "week_3": "אופטימיזציה: השבתת מה שלא עובד, הגברת מה שעובד",
            f"week_{duration_weeks}": "סיכום: דוח ביצועים + תכנון הקמפיין הבא",
        },
        "success_metrics": goal_info["kpis"],
        "content_calendar_note": f"מומלץ {len(platforms) * 3} פוסטים לשבוע בסה\"כ ({3} לפלטפורמה)",
        "next_steps": [
            "אשר את הבריף עם הלקוח",
            "צור את חומרי הקריאייטיב (תמונות + טקסטים)",
            "הגדר פיקסל מעקב באתר",
            "תזמן את הפוסטים הראשונים",
            "הגדר את הקמפיינים הממומנים",
        ],
    }


def submit_to_directory(
    business_name: str,
    business_description: str,
    website_url: str,
    category: str,
    location: str = "Israel",
    phone: str = "",
    email: str = "",
) -> Dict[str, Any]:
    """
    Generate a business directory submission package —
    ready-to-use listings for major Israeli and international directories.
    """
    short_desc = business_description[:150] + "..." if len(business_description) > 150 else business_description

    directories = {
        "israel": [
            {
                "name": "דפי זהב (d.co.il)",
                "url": "https://www.d.co.il",
                "free": True,
                "notes": "רשום עסק חינם, מוסיף אמינות בחיפוש גוגל",
                "listing_text": f"{business_name} | {short_desc} | {location}",
            },
            {
                "name": "BNI ישראל",
                "url": "https://bni.co.il",
                "free": False,
                "notes": "רשת עסקים בתשלום, מומלץ לעסקים B2B",
                "listing_text": f"{business_name} — {category}",
            },
            {
                "name": "Waze for Business",
                "url": "https://www.waze.com/en/business",
                "free": True,
                "notes": "חיוני לעסקים עם כתובת פיזית",
                "listing_text": f"{business_name}, {location}",
            },
            {
                "name": "Google Business Profile",
                "url": "https://business.google.com",
                "free": True,
                "notes": "**חשוב ביותר** — מופיע בחיפוש Google Maps",
                "listing_text": f"{business_name} | {category} | {location} | {website_url}",
            },
        ],
        "international": [
            {
                "name": "Yelp",
                "url": "https://biz.yelp.com",
                "free": True,
                "notes": "רלוונטי לעסקים עם קהל אנגלית",
                "listing_text": f"{business_name} — {short_desc}",
            },
            {
                "name": "Crunchbase",
                "url": "https://www.crunchbase.com",
                "free": True,
                "notes": "מומלץ לסטארטאפים וחברות טכנולוגיה",
                "listing_text": f"{business_name} | {category} startup | {website_url}",
            },
            {
                "name": "Product Hunt",
                "url": "https://www.producthunt.com",
                "free": True,
                "notes": "מצוין להשקות מוצרים טכנולוגיים",
                "listing_text": f"{business_name} — {short_desc}",
            },
        ],
    }

    standard_listing = {
        "business_name": business_name,
        "category": category,
        "description_short": short_desc,
        "description_long": business_description,
        "website": website_url,
        "phone": phone,
        "email": email,
        "location": location,
        "keywords": f"{category}, {business_name}, {location}",
    }

    return {
        "summary": f"חבילת רישום מוכנה עבור {business_name}",
        "directories": directories,
        "standard_listing": standard_listing,
        "seo_tips": [
            "השתמש באותו שם עסק בדיוק בכל הדירקטוריות (NAP Consistency)",
            "הוסף תמונות מקצועיות לכל פרופיל",
            "בקש מלקוחות מרוצים לכתוב ביקורות בגוגל",
            "עדכן שעות פתיחה ופרטי קשר בכל הפלטפורמות",
        ],
        "priority_order": [
            "1. Google Business Profile (חינם, השפעה הכי גדולה על SEO)",
            "2. דפי זהב (קהל ישראלי)",
            "3. Waze (עסק עם כתובת פיזית)",
            "4. Crunchbase / Product Hunt (אם טכנולוגיה/סטארטאפ)",
        ],
        "estimated_time": "2-3 שעות לרישום בכל הדירקטוריות המומלצות",
    }


def save_to_crm(
    session_id: str,
    contact_name: str,
    contact_platform: str,
    contact_id: str,
    action_taken: str,
    notes: str = "",
    tags: List[str] = None,
    follow_up_date: str = "",
) -> Dict[str, Any]:
    """
    Save a contact / lead interaction result to the internal CRM log.
    Stores leads gathered from social media actions for follow-up.
    """
    import os
    crm_dir = os.environ.get("CRM_DIR", "/tmp/ai-agent-crm")
    os.makedirs(crm_dir, exist_ok=True)
    crm_path = os.path.join(crm_dir, f"{session_id}.json")

    entry = {
        "id": f"lead_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "timestamp": datetime.now().isoformat(),
        "contact_name": contact_name,
        "platform": contact_platform,
        "contact_id": contact_id,
        "action_taken": action_taken,
        "notes": notes,
        "tags": tags or [],
        "follow_up_date": follow_up_date,
        "status": "new",
    }

    existing = []
    if os.path.exists(crm_path):
        try:
            with open(crm_path, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except Exception:
            existing = []

    existing.append(entry)
    with open(crm_path, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)

    logger.info(f"[CRM][{session_id}] Saved contact: {contact_name} from {contact_platform}")

    return {
        "saved": True,
        "lead_id": entry["id"],
        "contact": contact_name,
        "platform": contact_platform,
        "action": action_taken,
        "follow_up": follow_up_date or "לא נקבע",
        "total_leads": len(existing),
        "message": f"קשר '{contact_name}' נשמר ב-CRM. סה\"כ {len(existing)} קשרים.",
    }


def generate_smart_reply(
    comment_text: str,
    platform: str,
    business_name: str = "",
    tone: str = "professional",
    comment_sentiment: str = "positive",
) -> Dict[str, Any]:
    """Generate smart reply suggestions for a comment."""

    tone_guide = {
        "professional": "מקצועי, ישיר, מכבד",
        "casual": "קליל, ידידותי, אישי",
        "funny": "הומוריסטי, קל, מבדר",
    }

    sentiment_strategy = {
        "positive": "תודה, חיזוק, הזמנה להמשיך בקשר",
        "negative": "אמפתיה, פתרון, העברה לפרטי",
        "question": "תשובה מפורטת, הצעת עזרה נוספת",
        "neutral": "מעורבות, שאלה חוזרת, ערך מוסף",
    }

    return {
        "original_comment": comment_text,
        "platform": platform,
        "sentiment_detected": comment_sentiment,
        "reply_strategy": sentiment_strategy.get(comment_sentiment, "מעורבות חיובית"),
        "suggested_replies": [
            {
                "variant": "קצר ומהיר",
                "instruction": f"כתוב תגובה קצרה (1-2 משפטים) ל: '{comment_text}' בשם {business_name}, טון: {tone_guide.get(tone, tone)}. אסטרטגיה: {sentiment_strategy.get(comment_sentiment)}",
            },
            {
                "variant": "מפורט עם ערך",
                "instruction": f"כתוב תגובה מפורטת (3-4 משפטים) ל: '{comment_text}' בשם {business_name}, כלול ערך מוסף או מידע שימושי. טון: {tone_guide.get(tone, tone)}",
            },
        ],
        "auto_reply_tips": [
            "הגב תוך 1-2 שעות לשיפור ה-engagement rate",
            "תמיד קרא לאדם בשמו אם הוא ציין אותו",
            "עבור תלונות - העבר לפרטי/ווטסאפ",
            "הוסף שאלה חוזרת לשמירת שיחה פעילה",
        ],
    }
