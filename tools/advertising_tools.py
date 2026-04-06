"""
Paid advertising guidance tools for Google Ads and Facebook/Meta Ads.
Provides step-by-step guidance for setting up and managing ad campaigns.
"""
from __future__ import annotations
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


def setup_facebook_ad_campaign(
    goal: str,
    daily_budget: float,
    target_audience: Dict[str, Any],
    ad_creative_description: str = "",
) -> Dict[str, Any]:
    """
    Provide step-by-step guidance for setting up a Facebook/Meta ad campaign.

    Args:
        goal: Campaign objective (awareness, traffic, leads, sales, app_installs)
        daily_budget: Daily budget in NIS/USD
        target_audience: Audience targeting parameters
        ad_creative_description: Description of the ad content
    """
    objective_map = {
        "new_users": "OUTCOME_AWARENESS",
        "brand_awareness": "OUTCOME_AWARENESS",
        "lead_generation": "OUTCOME_LEADS",
        "sales": "OUTCOME_SALES",
        "traffic": "OUTCOME_TRAFFIC",
        "engagement": "OUTCOME_ENGAGEMENT",
        "app_installs": "OUTCOME_APP_PROMOTION",
    }

    fb_objective = objective_map.get(goal, "OUTCOME_AWARENESS")

    steps = [
        {
            "step": 1,
            "title": "כניסה ל-Meta Ads Manager",
            "url": "https://adsmanager.facebook.com",
            "action": "לחץ על '+ Create' ליצירת קמפיין חדש",
        },
        {
            "step": 2,
            "title": "בחירת מטרת הקמפיין",
            "action": f"בחר את המטרה: {fb_objective.replace('OUTCOME_', '').title()}",
            "options": list(objective_map.values()),
            "recommendation": fb_objective,
        },
        {
            "step": 3,
            "title": "הגדרת תקציב",
            "action": f"הגדר תקציב יומי: ₪{daily_budget}",
            "tips": [
                f"תקציב מינימלי מומלץ: ₪50-100/יום",
                f"עם תקציב של ₪{daily_budget}/יום תוכל להגיע ל-{int(daily_budget * 50)}-{int(daily_budget * 100)} אנשים",
                "התחל בתקציב קטן, נתח תוצאות, ואז הגדל",
            ],
        },
        {
            "step": 4,
            "title": "הגדרת קהל יעד",
            "action": "הגדר Audience בהתבסס על:",
            "targeting": {
                "location": target_audience.get("locations", ["Israel"]),
                "age": f"{target_audience.get('age_min', 18)}-{target_audience.get('age_max', 65)}",
                "interests": target_audience.get("interests", []),
                "languages": target_audience.get("languages", ["Hebrew"]),
            },
            "advanced_options": [
                "Lookalike Audience מלקוחות קיימים",
                "Retargeting לביקורים באתר",
                "Custom Audience מרשימת אימיילים",
            ],
        },
        {
            "step": 5,
            "title": "יצירת מודעה (Ad Creative)",
            "formats": [
                "תמונה יחידה - פשוט ויעיל",
                "וידאו - מעורבות גבוהה",
                "קרוסל - הצג מספר מוצרים",
                "Collection - לחנויות",
            ],
            "copy_tips": [
                "כתוב כותרת מושכת תוך 3 שניות",
                "הסבר את הערך בשורה אחת",
                "הוסף Call-to-Action ברור",
                "בדוק עם A/B Testing",
            ],
        },
        {
            "step": 6,
            "title": "מעקב ואופטימיזציה",
            "action": "הוסף Facebook Pixel לאתר שלך",
            "url": "https://www.facebook.com/events_manager",
            "kpis_to_track": ["CPM", "CTR", "CPC", "ROAS", "Cost per Lead"],
        },
    ]

    estimated_results = _estimate_facebook_results(daily_budget, goal, target_audience)

    return {
        "platform": "Facebook / Meta Ads",
        "campaign_objective": fb_objective,
        "daily_budget": daily_budget,
        "monthly_budget": daily_budget * 30,
        "setup_steps": steps,
        "estimated_results": estimated_results,
        "helpful_links": {
            "Ads Manager": "https://adsmanager.facebook.com",
            "Business Help Center": "https://www.facebook.com/business/help",
            "Facebook Blueprint": "https://www.facebookblueprint.com",
        },
        "israel_specific_tips": [
            "פרסם בעברית לקהל ישראלי - אחוזי הקלקה גבוהים יותר",
            "הימנע מפרסום ביום שבת (שישי אחה\"צ עד מוצ\"ש)",
            "ימי ג'-ה' הם הטובים ביותר בישראל",
        ],
    }


def setup_google_ads_campaign(
    goal: str,
    daily_budget: float,
    keywords: List[str],
    landing_page_url: str = "",
    location: str = "Israel",
) -> Dict[str, Any]:
    """
    Provide step-by-step guidance for setting up a Google Ads campaign.

    Args:
        goal: Campaign goal
        daily_budget: Daily budget in NIS/USD
        keywords: Target keywords
        landing_page_url: Landing page for the ads
        location: Target location
    """
    campaign_types = {
        "new_users": "Search Campaign",
        "brand_awareness": "Display Campaign",
        "lead_generation": "Search Campaign + Lead Form",
        "sales": "Search + Shopping Campaign",
        "traffic": "Search Campaign",
        "engagement": "Display Campaign",
    }

    campaign_type = campaign_types.get(goal, "Search Campaign")

    steps = [
        {
            "step": 1,
            "title": "כניסה ל-Google Ads",
            "url": "https://ads.google.com",
            "action": "לחץ על 'New Campaign' ובחר את מטרת הקמפיין",
        },
        {
            "step": 2,
            "title": f"בחירת סוג קמפיין: {campaign_type}",
            "options": list(campaign_types.values()),
            "recommendation": campaign_type,
            "why": f"לקמפיין {goal} {campaign_type} הוא הפתרון הטוב ביותר",
        },
        {
            "step": 3,
            "title": "הגדרת תקציב ובידינג",
            "action": f"תקציב יומי: ₪{daily_budget}",
            "bidding_strategies": [
                "Maximize Clicks - להגדיל תנועה",
                "Target CPA - לקבוע עלות רכישה",
                "Maximize Conversions - לקבל המרות",
                "Target ROAS - לקבוע יחס רווח",
            ],
            "recommendation": "התחל עם Maximize Clicks כדי לאסוף נתונים",
        },
        {
            "step": 4,
            "title": "הגדרת מיקוד גיאוגרפי",
            "location": location,
            "action": f"מקד למיקום: {location}",
            "israel_tip": "אפשר לבחור ערים ספציפיות בישראל לפרסום ממוקד יותר",
        },
        {
            "step": 5,
            "title": "מחקר מילות מפתח",
            "keywords_provided": keywords,
            "tools": [
                "Google Keyword Planner - https://ads.google.com/keywordplanner",
                "Google Trends - https://trends.google.com",
                "Ubersuggest - https://neilpatel.com/ubersuggest",
            ],
            "keyword_types": {
                "Broad Match": "נגיע לקהל רחב (פחות מדויק)",
                "Phrase Match": "נגיע לשאילתות הכוללות את הביטוי",
                'Exact Match': "נגיע בדיוק לביטוי שחיפשו",
                "Negative Keywords": "הימנע ממילות מפתח לא רלוונטיות",
            },
        },
        {
            "step": 6,
            "title": "כתיבת מודעות",
            "action": "צור לפחות 3 וריאנטים של מודעה",
            "structure": {
                "Headline 1 (30 chars)": "כותרת ראשית עם מילת מפתח",
                "Headline 2 (30 chars)": "יתרון מרכזי",
                "Headline 3 (30 chars)": "Call to Action",
                "Description 1 (90 chars)": "פרוט קצר של ההצעה",
                "Description 2 (90 chars)": "הוכחה חברתית / CTA",
            },
            "landing_page": landing_page_url or "צור דף נחיתה ייעודי לכל קמפיין",
        },
        {
            "step": 7,
            "title": "הגדרת המרות (Conversions)",
            "action": "הוסף Google Tag לאתר ומדד המרות",
            "url": "https://tagmanager.google.com",
            "conversions_to_track": ["Phone Calls", "Form Submissions", "Purchases", "Page Visits"],
        },
    ]

    keyword_cost_estimates = _estimate_keyword_costs(keywords, location)

    return {
        "platform": "Google Ads",
        "campaign_type": campaign_type,
        "daily_budget": daily_budget,
        "monthly_budget": daily_budget * 30,
        "setup_steps": steps,
        "keyword_estimates": keyword_cost_estimates,
        "estimated_monthly_clicks": int(daily_budget * 30 / max(keyword_cost_estimates.get("avg_cpc", 5), 1)),
        "helpful_links": {
            "Google Ads": "https://ads.google.com",
            "Keyword Planner": "https://ads.google.com/keywordplanner",
            "Google Ads Help": "https://support.google.com/google-ads",
            "Google Analytics": "https://analytics.google.com",
        },
        "israel_tips": [
            "שלב מילות מפתח בעברית ובאנגלית",
            "ישראלים מחפשים הרבה באנגלית גם על שירותים מקומיים",
            "CPC בישראל בדרך כלל נמוך יותר מארה\"ב",
        ],
    }


def estimate_ad_budget(
    goal: str,
    platform: str,
    target_reach: int,
    industry: str = "general",
) -> Dict[str, Any]:
    """
    Estimate the advertising budget needed to achieve a goal.

    Args:
        goal: Marketing goal
        platform: Advertising platform
        target_reach: Desired number of people to reach
        industry: Business industry (affects costs)
    """
    # Average CPM (cost per 1000 impressions) by platform in NIS
    platform_cpm = {
        "facebook": {"awareness": 15, "leads": 45, "sales": 60},
        "instagram": {"awareness": 20, "leads": 55, "sales": 70},
        "google": {"awareness": 8, "leads": 35, "sales": 50},
        "linkedin": {"awareness": 80, "leads": 150, "sales": 200},
        "tiktok": {"awareness": 10, "leads": 30, "sales": 40},
        "youtube": {"awareness": 12, "leads": 40, "sales": 55},
    }

    goal_type_map = {
        "new_users": "awareness",
        "brand_awareness": "awareness",
        "lead_generation": "leads",
        "sales": "sales",
        "traffic": "awareness",
        "engagement": "awareness",
    }

    goal_type = goal_type_map.get(goal, "awareness")
    cpm = platform_cpm.get(platform, {}).get(goal_type, 30)

    estimated_budget = (target_reach / 1000) * cpm
    estimated_impressions = target_reach
    estimated_clicks = int(target_reach * 0.02)  # ~2% CTR
    estimated_leads = int(estimated_clicks * 0.05)  # ~5% conversion

    return {
        "goal": goal,
        "platform": platform,
        "target_reach": target_reach,
        "estimated_budget_nis": round(estimated_budget, 2),
        "estimated_budget_usd": round(estimated_budget / 3.7, 2),
        "estimated_impressions": estimated_impressions,
        "estimated_clicks": estimated_clicks,
        "estimated_leads": estimated_leads,
        "cost_breakdown": {
            "daily_budget": round(estimated_budget / 30, 2),
            "weekly_budget": round(estimated_budget / 4, 2),
            "monthly_budget": round(estimated_budget, 2),
        },
        "industry_note": f"עלויות עשויות להשתנות לפי תחום ({industry})",
        "recommendation": f"התחל עם ₪{max(50, round(estimated_budget / 30, 0))}/יום ועלה בהדרגה לפי תוצאות",
    }


def analyze_competitor_ads(
    industry: str,
    platform: str,
    location: str = "Israel",
) -> Dict[str, Any]:
    """
    Analyze competitor advertising strategies in the industry.

    Args:
        industry: Business industry
        platform: Platform to analyze
        location: Target market location
    """
    # Tools for competitor research
    research_tools = {
        "facebook": {
            "tool": "Facebook Ad Library",
            "url": "https://www.facebook.com/ads/library/",
            "how_to_use": [
                "1. פתח את Facebook Ad Library",
                "2. חפש שם חברת מתחרה",
                "3. סנן לפי מדינה: ישראל",
                "4. ראה את כל המודעות הפעילות שלהם",
                "5. נתח קריאייטיב, הצעת ערך, ו-CTA",
            ],
        },
        "google": {
            "tool": "Google Ads Transparency Center",
            "url": "https://adstransparency.google.com",
            "additional_tools": ["SEMrush", "SpyFu", "Ahrefs"],
        },
        "instagram": {
            "tool": "Facebook Ad Library (Instagram)",
            "url": "https://www.facebook.com/ads/library/",
            "note": "Instagram ו-Facebook חולקים את אותה ספריית מודעות",
        },
    }

    best_practices = {
        "tech_startup": [
            "הדגשת חדשנות ויתרון טכנולוגי",
            "Social proof - כמה לקוחות/משתמשים",
            "Trial/Freemium הצעה",
            "Focus on problem-solving",
        ],
        "retail": [
            "מחיר ומבצעים בולטים",
            "תמונות מוצר איכותיות",
            "Urgency - 'מבצע מוגבל'",
            "User reviews/testimonials",
        ],
        "restaurant": [
            "תמונות אוכל מושכות",
            "הצעת ערך ייחודית (מה מייחד אתכם)",
            "מיקום ושעות פתיחה",
            "הזמנה מקוונת",
        ],
        "general": [
            "הבן מה מייחד אותך מהמתחרים",
            "מקד למיקוד גיאוגרפי ספציפי",
            "בדוק מה עובד אצל מתחרים ושפר",
            "השתמש ב-A/B testing",
        ],
    }

    tool_info = research_tools.get(platform, research_tools.get("facebook"))
    practices = best_practices.get(industry, best_practices["general"])

    return {
        "industry": industry,
        "platform": platform,
        "location": location,
        "research_tools": tool_info,
        "best_practices": practices,
        "analysis_checklist": [
            "✅ מה מוצרים/שירותים המתחרים מפרסמים?",
            "✅ מה הצעת הערך שלהם?",
            "✅ איזה קריאייטיב הם משתמשים?",
            "✅ מה ה-CTA שלהם?",
            "✅ לאיזה קהל הם מפנים?",
            "✅ כמה זמן המודעה פעילה? (מודעות ארוכות = עובדות)",
        ],
        "opportunity_gaps": "נתח את הפערים בשוק שהמתחרים לא מכסים - שם הזדמנות שלך",
    }


def _estimate_facebook_results(
    daily_budget: float,
    goal: str,
    target_audience: Dict[str, Any],
) -> Dict[str, Any]:
    """Estimate Facebook campaign results based on budget and goal."""
    cpm = 20  # Average CPM in NIS for Israel
    daily_impressions = int((daily_budget / cpm) * 1000)
    ctr = 0.025  # 2.5% average CTR
    daily_clicks = int(daily_impressions * ctr)
    conversion_rate = 0.03  # 3% conversion rate

    return {
        "daily_impressions": daily_impressions,
        "monthly_impressions": daily_impressions * 30,
        "daily_clicks": daily_clicks,
        "monthly_clicks": daily_clicks * 30,
        "estimated_leads_per_month": int(daily_clicks * 30 * conversion_rate),
        "estimated_cpc": round(daily_budget / max(daily_clicks, 1), 2),
        "note": "אלה הערכות ממוצעות - תוצאות אמיתיות עשויות להשתנות",
    }


def _estimate_keyword_costs(keywords: List[str], location: str) -> Dict[str, Any]:
    """Estimate Google Ads keyword costs."""
    # Demo data - in production use Google Keyword Planner API
    avg_cpc = 5.0  # Average CPC in NIS for Israel

    return {
        "keywords": keywords,
        "avg_cpc": avg_cpc,
        "avg_search_volume": "1,000-10,000/month (estimated)",
        "competition": "Medium",
        "note": "השתמש ב-Google Keyword Planner לנתונים מדויקים",
    }
