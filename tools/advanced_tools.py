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

import anthropic as _anthropic

logger = logging.getLogger(__name__)


def _claude(prompt: str, max_tokens: int = 600) -> str:
    """Call Claude Haiku synchronously for a single-turn generation task."""
    from config import config
    client = _anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text.strip()
    except Exception as e:
        logger.error(f"Claude call failed in advanced_tools: {e}")
        raise RuntimeError(f"AI generation failed: {e}") from e


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
    """Create two real post variants for A/B testing using Claude."""
    cta = f" קישור: {website_url}" if website_url else ""
    base = f"עסק: {business_name}.{cta}"

    content_a = _claude(
        f"כתוב פוסט {platform} על '{topic}' בסגנון {tone_a}. {base} "
        f"כתוב רק את הפוסט עצמו, ללא הסברים.",
        max_tokens=400,
    )
    content_b = _claude(
        f"כתוב פוסט {platform} על '{topic}' בסגנון {tone_b}. {base} "
        f"כתוב רק את הפוסט עצמו, ללא הסברים.",
        max_tokens=400,
    )

    return {
        "test_id": f"ab_{platform}_{datetime.now().strftime('%m%d%H%M')}",
        "platform": platform,
        "topic": topic,
        "variant_a": {"name": "Variant A", "tone": tone_a, "content": content_a},
        "variant_b": {"name": "Variant B", "tone": tone_b, "content": content_b},
        "testing_guide": {
            "duration": "פרסם את שני הווריאנטים — 50% מהקהל לכל אחד",
            "measure": ["clicks", "likes", "comments", "shares", "reach"],
            "decide_after": "48 שעות",
            "winner_criteria": "הווריאנט עם CTR גבוה יותר מנצח",
        },
    }


def translate_content(
    content: str,
    source_language: str = "hebrew",
    target_languages: List[str] = None,
    platform: str = "facebook",
    business_context: str = "",
) -> Dict[str, Any]:
    """Translate post content to multiple languages using Claude."""
    if not target_languages:
        target_languages = ["english"]

    lang_meta = {
        "english": {"name": "English", "direction": "ltr", "flag": "🇬🇧"},
        "arabic":  {"name": "العربية", "direction": "rtl", "flag": "🇸🇦"},
        "french":  {"name": "Français", "direction": "ltr", "flag": "🇫🇷"},
        "spanish": {"name": "Español",  "direction": "ltr", "flag": "🇪🇸"},
        "russian": {"name": "Русский",  "direction": "ltr", "flag": "🇷🇺"},
        "german":  {"name": "Deutsch",  "direction": "ltr", "flag": "🇩🇪"},
    }

    translations = {}
    for lang in target_languages:
        meta = lang_meta.get(lang, {"name": lang, "direction": "ltr", "flag": "🌐"})
        translated = _claude(
            f"Translate this {platform} post from {source_language} to {meta['name']}. "
            f"Keep the same tone, emojis, hashtags style, and call-to-action. "
            f"Business context: {business_context}. "
            f"Return ONLY the translated post, no explanations.\n\nPost:\n{content}",
            max_tokens=500,
        )
        translations[lang] = {
            "language": meta["name"],
            "flag": meta["flag"],
            "direction": meta["direction"],
            "translated_content": translated,
        }

    return {
        "original_content": content,
        "original_language": source_language,
        "platform": platform,
        "translations": translations,
        "tip": "פרסם גרסאות שונות לפי שפה ומיקוד גיאוגרפי לחשיפה מקסימלית",
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
    """Analyze competitors using Claude's knowledge of the industry."""
    competitors_str = ", ".join(competitors) if competitors else "מתחרים בתחום"

    analysis = _claude(
        f"אתה מנתח שיווק דיגיטלי מומחה. נתח את המתחרים הבאים בתחום '{industry}' בפלטפורמה {platform}:\n"
        f"מתחרים: {competitors_str}\n"
        f"עסק שלנו: {business_name}\n\n"
        f"ספק ניתוח מעשי הכולל:\n"
        f"1. אסטרטגיית התוכן הנפוצה שלהם\n"
        f"2. חוזקות שלהם\n"
        f"3. חולשות / פערים שניתן לנצל\n"
        f"4. 3 המלצות קונקרטיות ל-{business_name} כדי להתבלט\n"
        f"כתוב בעברית, ענייני ומעשי.",
        max_tokens=700,
    )

    gap_analysis = _claude(
        f"בהינתן שהמתחרים ב'{industry}' על {platform} הם: {competitors_str}, "
        f"מהן 5 הזדמנויות ספציפיות שעסק כמו '{business_name}' יכול לנצל? "
        f"תשובה קצרה בנקודות, עברית.",
        max_tokens=300,
    )

    return {
        "industry": industry,
        "platform": platform,
        "competitors_analyzed": competitors,
        "analysis": analysis,
        "opportunities": gap_analysis,
        "tools_recommended": [
            "Facebook Ad Library (בחינם) — לראות פרסומות ממומנות של מתחרים",
            "Social Blade — לניתוח צמיחת עוקבים",
            "Phlanx — לחישוב engagement rate",
            "Similarweb — לניתוח תנועה לאתר",
        ],
        "check_frequency": "פעם בשבוע",
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

    platforms_str = ", ".join(platforms_active) if platforms_active else "לא צוינו"
    top_str = f"הפוסט המוביל: {top_performing_content}. " if top_performing_content else ""

    insights_raw = _claude(
        f"הפק 4 תובנות שיווקיות קונקרטיות ומעשיות לעסק '{business_name}' "
        f"בהתבסס על הנתונים הבאים:\n"
        f"- פוסטים שפורסמו השבוע: {posts_this_week}\n"
        f"- פלטפורמות פעילות: {platforms_str}\n"
        f"- ציון ביצועים: {performance_score}/100\n"
        f"- {top_str}"
        f"כתוב 4 נקודות ספציפיות בעברית, כל אחת בשורה נפרדת.",
        max_tokens=400,
    )
    insights = [line.strip() for line in insights_raw.split("\n") if line.strip()][:4] or [
        f"פורסמו {posts_this_week} פוסטים על {len(platforms_active)} פלטפורמות"]

    next_week_raw = _claude(
        f"תכנן את השבוע הבא לעסק '{business_name}' ב-{platforms_str}. "
        f"השבוע פורסמו {posts_this_week} פוסטים (ציון {performance_score}/100). "
        f"תן תוכנית תמציתית: כמה פוסטים, באיזה ימים, ואיזה נושאים. "
        f"כתוב ב-3-4 משפטים קצרים בעברית.",
        max_tokens=300,
    )

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
            }
            for p in platforms_active
        },
        "top_performing": top_performing_content or "לא סופקו נתונים",
        "insights": insights,
        "next_week_plan": next_week_raw,
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
    """Generate real reply suggestions using Claude."""
    short_reply = _claude(
        f"כתוב תגובה קצרה (1-2 משפטים) לתגובה הבאה ב-{platform} בשם העסק '{business_name}'.\n"
        f"סנטימנט: {comment_sentiment}. טון: {tone}.\n"
        f"תגובה מקורית: \"{comment_text}\"\n"
        f"כתוב רק את התגובה עצמה.",
        max_tokens=150,
    )
    detailed_reply = _claude(
        f"כתוב תגובה מפורטת (3-4 משפטים) לתגובה הבאה ב-{platform} בשם העסק '{business_name}'.\n"
        f"סנטימנט: {comment_sentiment}. טון: {tone}. כלול ערך מוסף או מידע שימושי.\n"
        f"תגובה מקורית: \"{comment_text}\"\n"
        f"כתוב רק את התגובה עצמה.",
        max_tokens=250,
    )

    return {
        "original_comment": comment_text,
        "platform": platform,
        "sentiment_detected": comment_sentiment,
        "suggested_replies": [
            {"variant": "קצר ומהיר", "content": short_reply},
            {"variant": "מפורט עם ערך", "content": detailed_reply},
        ],
        "tips": [
            "הגב תוך 1-2 שעות לשיפור ה-engagement rate",
            "עבור תלונות — העבר לפרטי/וואטסאפ",
            "הוסף שאלה חוזרת לשמירת שיחה פעילה",
        ],
    }
