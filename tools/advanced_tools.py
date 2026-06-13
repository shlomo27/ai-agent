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
import os
import textwrap
import uuid
from io import BytesIO
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

import anthropic as _anthropic

logger = logging.getLogger(__name__)

UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "/tmp/ai-agent-uploads"))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def generate_post_image(
    content: str,
    platform: str = "linkedin",
    business_name: str = "ilmariai.com",
    base_url: str = "",
) -> str | None:
    """
    Generate a branded image for a social media post using Pillow.
    Returns the public URL of the generated image, or None on failure.
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        logger.warning("Pillow not installed — skipping image generation")
        return None

    sizes = {
        "linkedin":  (1200, 627),
        "twitter":   (1200, 675),
        "facebook":  (1200, 630),
        "instagram": (1080, 1080),
        "tiktok":    (1080, 1920),
    }
    w, h = sizes.get(platform, (1200, 627))

    # ── Background gradient (dark purple → dark blue) ──────────────────────
    img = Image.new("RGB", (w, h))
    draw = ImageDraw.Draw(img)
    for y in range(h):
        ratio = y / h
        r = int(15  + ratio * 10)
        g = int(10  + ratio * 15)
        b = int(40  + ratio * 60)
        draw.line([(0, y), (w, y)], fill=(r, g, b))

    # ── Subtle grid lines ───────────────────────────────────────────────────
    grid_color = (255, 255, 255, 18)
    grid_img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    grid_draw = ImageDraw.Draw(grid_img)
    for x in range(0, w, 80):
        grid_draw.line([(x, 0), (x, h)], fill=grid_color, width=1)
    for y in range(0, h, 80):
        grid_draw.line([(0, y), (w, y)], fill=grid_color, width=1)
    img = Image.alpha_composite(img.convert("RGBA"), grid_img).convert("RGB")
    draw = ImageDraw.Draw(img)

    # ── Accent bar at top ───────────────────────────────────────────────────
    accent_h = max(6, h // 100)
    for x in range(w):
        ratio = x / w
        r = int(99  + ratio * (236 - 99))
        g = int(102 + ratio * (72  - 102))
        b = int(241 + ratio * (153 - 241))
        draw.line([(x, 0), (x, accent_h)], fill=(r, g, b))

    # ── Font selection (fall back to default) ──────────────────────────────
    font_size_body   = max(28, w // 28)
    font_size_brand  = max(20, w // 48)

    try:
        font_body  = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",  font_size_body)
        font_brand = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size_brand)
    except Exception:
        font_body  = ImageFont.load_default()
        font_brand = font_body

    # ── Extract headline (first non-empty, non-emoji line, max 60 chars) ─────
    padding = w // 12
    clean_lines = [l.strip() for l in content.split("\n") if l.strip()]
    # Pick the first line that looks like a real sentence (>10 chars)
    headline_raw = next((l for l in clean_lines if len(l) > 10), clean_lines[0] if clean_lines else "")
    # Strip emojis and markdown symbols for cleaner display
    import re
    headline_clean = re.sub(r'[^\x00-\x7F✅🚀💡⚡🎯📊🔥💰👉🌐📱]+', '', headline_raw).strip(" *#-→")
    headline_clean = headline_clean[:72] + ("..." if len(headline_clean) > 72 else "")

    # Large headline font
    font_size_headline = max(52, w // 20)
    try:
        font_headline = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size_headline)
    except Exception:
        font_headline = font_body

    headline_lines = textwrap.wrap(headline_clean, width=max(18, w // (font_size_headline // 2 + 2)))
    headline_lines = headline_lines[:3]

    total_h = len(headline_lines) * (font_size_headline + 16)
    y_start = (h - total_h) // 2 - 40

    for i, line in enumerate(headline_lines):
        y = y_start + i * (font_size_headline + 16)
        draw.text((padding + 2, y + 2), line, font=font_headline, fill=(0, 0, 30))
        draw.text((padding, y), line, font=font_headline, fill=(255, 255, 255))

    # ── Divider line ────────────────────────────────────────────────────────
    div_y = y_start + total_h + 24
    draw.line([(padding, div_y), (w - padding, div_y)], fill=(99, 102, 241), width=3)

    # ── Brand tag at bottom ─────────────────────────────────────────────────
    brand = business_name or "ilmariai.com"
    brand_upper = brand.upper()
    draw.text((padding, h - font_size_brand - 28), brand_upper, font=font_brand, fill=(160, 130, 255))

    # ── Save and return URL ─────────────────────────────────────────────────
    filename = f"post_{uuid.uuid4().hex[:12]}.png"
    dest = UPLOAD_DIR / filename
    img.save(dest, "PNG", optimize=True)

    base = (base_url or os.getenv("PUBLIC_API_URL", "")).rstrip("/")
    return f"{base}/uploads/{filename}" if base else None




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


def _fetch_platform_analytics(platform_name: str, platform) -> Dict[str, Any]:
    """Fetch real follower/subscriber counts from a connected platform (sync httpx)."""
    try:
        import httpx
        token = getattr(platform, "access_token", "")
        if not token:
            return {}

        if platform_name == "youtube" and getattr(platform, "_oauth_mode", False):
            resp = httpx.get(
                "https://www.googleapis.com/youtube/v3/channels",
                params={"part": "statistics", "mine": "true"},
                headers={"Authorization": f"Bearer {token}"},
                timeout=10,
                follow_redirects=True,
            )
            if resp.status_code == 200:
                items = resp.json().get("items", [])
                if items:
                    stats = items[0].get("statistics", {})
                    return {
                        "subscribers": stats.get("subscriberCount"),
                        "total_views": stats.get("viewCount"),
                        "videos": stats.get("videoCount"),
                    }

        elif platform_name == "facebook":
            page_id = getattr(platform, "page_id", None)
            if page_id:
                resp = httpx.get(
                    f"https://graph.facebook.com/{page_id}",
                    params={"fields": "fan_count,followers_count", "access_token": token},
                    timeout=10,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    fans = data.get("followers_count") or data.get("fan_count")
                    if fans is not None:
                        return {"followers": fans}

    except Exception as e:
        logger.warning(f"Analytics fetch failed for {platform_name}: {e}")
    return {}


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
    """Generate a comprehensive weekly marketing report using real audit-log data."""
    from tools.action_log import get_action_log
    import tools.social_tools as social_tools

    platforms_active = platforms_active or []
    week_start = (datetime.now() - timedelta(days=7)).strftime("%d/%m/%Y")
    week_end = datetime.now().strftime("%d/%m/%Y")
    one_week_ago = datetime.now() - timedelta(days=7)

    # ── Per-platform post counts from scheduled jobs (most reliable source) ──────
    from tools.scheduler import PostScheduler
    all_jobs = PostScheduler._load_jobs()
    per_platform_counts: Dict[str, int] = {}

    for j in all_jobs:
        if j.get("session_id") != session_id:
            continue
        # Count any job that was published (status=published) or attempted (status=pending/failed)
        # within the last 7 days — we count by creation date so we capture manual posts too
        created_raw = j.get("created_at") or j.get("scheduled_for", "")
        try:
            created = datetime.fromisoformat(created_raw.replace("+00:00", "")).replace(tzinfo=None)
        except Exception:
            continue
        if created < one_week_ago:
            continue
        for p in j.get("platforms", []):
            per_platform_counts[p] = per_platform_counts.get(p, 0) + 1

    # Also count from audit log (Claude logs each publish with log_action)
    logs = get_action_log(session_id, limit=200)
    publish_keywords = ("post_published", "publish", "פרסם", "פרסום", "posted")
    for entry in logs:
        try:
            ts = datetime.fromisoformat(entry["timestamp"])
        except Exception:
            continue
        if ts < one_week_ago:
            continue
        text = (entry.get("action_type", "") + " " + entry.get("description", "")).lower()
        if not any(kw in text for kw in publish_keywords):
            continue
        # Try to extract platform from details
        details = entry.get("details", {})
        platforms_in_log = details.get("platforms") or (
            [details["platform"]] if details.get("platform") else []
        )
        for p in platforms_in_log:
            per_platform_counts[p] = per_platform_counts.get(p, 0) + 1

    # ── Connected (non-demo) platforms ────────────────────────────────────────
    connected_platforms = {
        name: p for name, p in social_tools._platform_registry.items()
        if not getattr(p, "demo_mode", True)
    }
    if connected_platforms:
        platforms_active = list(connected_platforms.keys())

    # Merge: any platform that had a post this week is "active" even if not in registry now
    for p in per_platform_counts:
        if p not in platforms_active:
            platforms_active.append(p)

    total_posts = sum(per_platform_counts.values()) or posts_this_week

    # ── Fetch real analytics from connected platforms ─────────────────────────
    platform_analytics: Dict[str, Dict] = {}
    for name, plat in connected_platforms.items():
        stats = _fetch_platform_analytics(name, plat)
        if stats:
            platform_analytics[name] = stats

    performance_score = min(100, (
        (total_posts * 10) +
        (len(platforms_active) * 15) +
        (20 if top_performing_content else 0)
    ))

    platforms_str = ", ".join(platforms_active) if platforms_active else "לא צוינו"
    top_str = f"הפוסט המוביל: {top_performing_content}. " if top_performing_content else ""

    insights_raw = _claude(
        f"הפק 4 תובנות שיווקיות קונקרטיות ומעשיות לעסק '{business_name}' "
        f"בהתבסס על הנתונים הבאים:\n"
        f"- פוסטים שפורסמו השבוע: {total_posts}\n"
        f"- פלטפורמות פעילות: {platforms_str}\n"
        f"- ציון ביצועים: {performance_score}/100\n"
        f"- {top_str}"
        f"כתוב 4 נקודות ספציפיות בעברית, כל אחת בשורה נפרדת.",
        max_tokens=400,
    )
    insights = [line.strip() for line in insights_raw.split("\n") if line.strip()][:4] or [
        f"פורסמו {total_posts} פוסטים על {len(platforms_active)} פלטפורמות"]

    next_week_raw = _claude(
        f"תכנן את השבוע הבא לעסק '{business_name}' ב-{platforms_str}. "
        f"השבוע פורסמו {total_posts} פוסטים (ציון {performance_score}/100). "
        f"תן תוכנית תמציתית: כמה פוסטים, באיזה ימים, ואיזה נושאים. "
        f"כתוב ב-3-4 משפטים קצרים בעברית.",
        max_tokens=300,
    )

    # Build per-platform breakdown with real post counts + analytics
    platform_breakdown = {}
    for p in platforms_active:
        entry: Dict[str, Any] = {"posts": per_platform_counts.get(p, 0)}
        if p in platform_analytics:
            entry.update(platform_analytics[p])
        platform_breakdown[p] = entry

    # Build analytics summary for report
    analytics_lines = []
    for p, stats in platform_analytics.items():
        if "subscribers" in stats:
            analytics_lines.append(f"YouTube — {stats['subscribers']:,} מנויים, {stats.get('total_views','N/A')} צפיות כולל")
        if "followers" in stats:
            analytics_lines.append(f"Facebook — {stats['followers']:,} עוקבים")
    analytics_summary = "\n".join(analytics_lines) if analytics_lines else None

    return {
        "report_title": f"דוח שבועי - {business_name}",
        "period": f"{week_start} - {week_end}",
        "generated_at": datetime.now().isoformat(),
        "already_publishing": True,
        "executive_summary": {
            "performance_score": performance_score,
            "grade": "A" if performance_score >= 80 else "B" if performance_score >= 60 else "C",
            "posts_published": total_posts,
            "platforms_active": len(platforms_active),
            "analytics": analytics_summary or "נתונים ישירים לא זמינים — ניתן לראות ב-Facebook Insights / YouTube Studio",
        },
        "platform_breakdown": platform_breakdown,
        "top_performing": top_performing_content or "לא סופקו נתונים",
        "insights": insights,
        "next_week_plan": next_week_raw,
        "website_traffic_tip": f"הוסף UTM parameters לקישורים ל-{website_url} כדי לעקוב אחרי תנועה מרשתות חברתיות",
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
