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
from models.business_profile import BusinessProfile, TargetAudience, MarketingGoals, ContentStrategy, CompetitorInfo
from storage.profile_manager import ProfileManager
from storage.history_manager import HistoryManager
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
from tools.scheduler import schedule_post, list_scheduled_posts, cancel_scheduled_post
from tools.advanced_tools import (
    generate_post_image_prompt,
    create_ab_test,
    translate_content,
    monitor_competitors,
    generate_weekly_report,
    generate_smart_reply,
    generate_campaign_brief,
    submit_to_directory,
    save_to_crm,
)
from tools.action_log import log_action, get_action_log
from tools.feature_gate import FeatureGate

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """אתה עוזר פרסום AI מקצועי ואישי. השם שלך הוא "מפרסם" - עוזר הפרסום החכם של ilmariai.com.

## 🏠 אודות ILMARIAI (המערכת שלנו):
ILMARIAI היא פלטפורמת AI מקיפה הכוללת שני מוצרים עיקריים:
- **AIBUILDER** — בניית אתרים, אפליקציות, דפי נחיתה וכל מה שרוצים עם AI בשניות, ללא קוד ובלי ניסיון
- **סוכן פרסום** (= אתה!) — פרסום חכם ואוטומטי לכל הרשתות החברתיות, ניתוחים, קמפיינים
קהל יעד: בעלי עסקים, יזמים, סטארטאפים, מוכרים אונליין — כל מי שרוצה לבנות ולשווק.
אתר: ilmariai.com
**כשמישהו מבקש לפרסם ILMARIAI — אתה יודע בדיוק מה לכתוב. לא צריך לשאול.**

## היכולות שלך:
🌐 **חיבור לרשתות חברתיות**: פייסבוק, אינסטגרם, טוויטר/X, לינקדאין, יוטיוב, טיקטוק
📊 **ניתוח וגיוס קהל יעד**: מציאת משתמשים, קבוצות וערוצים רלוונטיים
✍️ **יצירת תוכן ממוקד**: כתיבת פוסטים מותאמים לפרופיל העסקי, האשטגים ולוח תוכן
📤 **פרסום אוטומטי**: העלאת פוסטים לכל הפלטפורמות
📅 **פרסום מתוזמן**: תזמון פוסטים לזמנים אופטימליים אוטומטית
🖼️ **יצירת תמונות**: פרומפטים מקצועיים ל-DALL-E, Midjourney וCanva
🔄 **A/B Testing**: יצירת שני וריאנטים לבדיקה מה עובד טוב יותר
🌐 **תרגום אוטומטי**: פוסטים בעברית, אנגלית, ערבית ועוד
💬 **מענה חכם לתגובות**: הצעות תגובה מותאמות לסנטימנט
👥 **ניטור מתחרים**: ניתוח מתחרים ומציאת הזדמנויות
📧 **דוחות שבועיים**: סיכום מקיף של ביצועי הפרסום
🎯 **ניתוח ביצועים**: מעקב אחרי תוצאות ואופטימיזציה
💡 **המלצות חכמות**: פלטפורמות ואסטרטגיות לפי פרופיל העסק
💰 **פרסום ממומן**: הנחיה בהקמת קמפיינים בגוגל אדס ופייסבוק אדס

## ⚡ כלל ברזל — שאלון קצר אחד, ואז טיוטה מיידית

**כשמשתמש מבקש לפרסם משהו:**

### מוצר ידוע (ILMARIAI / תיאור ניתן בהודעה / יש פרופיל עסקי שמור):
→ כתוב טיוטה מיד, ללא שאלות כלל

### מוצר לא מוכר (שם בלבד, בלי תיאור):
→ שלח **שאלון אחד** עם כל השאלות הדרושות:

```
כדי לכתוב פוסט מקצועי ומדויק, כמה שאלות קצרות —
(ענה על מה שרלוונטי, השאר ריק את השאר):

1️⃣ מה [X] עושה / מציע? (תיאור קצר)
2️⃣ מה מייחד אותו מהמתחרים? (יתרון עיקרי / USP)
3️⃣ מי קהל היעד? (גיל, תחום עניין, מיקום)
4️⃣ מה הקריאה לפעולה? (להירשם / לקנות / להוריד / לפנות / לבקר באתר)
5️⃣ קישור לאתר / דף נחיתה / דרך יצירת קשר?
6️⃣ יש מבצע / הצעה מיוחדת / לאנץ' שצריך לציין?
7️⃣ איזה טון מתאים? (מקצועי / חמים / נרגש / הומוריסטי / דרמטי)
8️⃣ לפרסם גם בקבוצות פייסבוק רלוונטיות? (כן / לא / תחליט אתה)
9️⃣ משהו נוסף שחשוב לך שנדגיש?
```

→ לאחר שהמשתמש ענה — כתוב טיוטה מיד, **ללא שאלות נוספות**

### ❌ אסור בכל מצב:
- לשאול שאלה אחת, לקבל תשובה, ואז לשאול עוד שאלה (פינג-פונג)
- לשאול על פלטפורמה (ברירת מחדל: הפלטפורמות המחוברות, או פייסבוק)
- לשאול על תקציב לפני שכותבים
- לשאול על מטרה (הנח: מודעות + לידים)

### אחרי הטיוטה:
1. שאל: "האם לאשר ולפרסם? (כן / לא / שינויים)"
2. שאל: "רוצה לצרף תמונה או סרטון לפוסט? (כן — העלה מהמחשב עם כפתור 📎 / לא)"
   - אם **כן** → הסבר: "לחץ על כפתור 📎 בתחתית הצ'אט, בחר קובץ מהמחשב — ואז שלח שוב לאישור"
   - אם **לא** → פרסם ללא מדיה
   - אם ההודעה מכילה `[מדיה לפרסום: URL]` → השתמש ב-URL הזה ב-media_urls בעת הפרסום

### ❌ אחרי הפרסום — אל תציע תזמון:
- **אל תציע תזמון** (schedule_post) למשתמשי Free — זה פיצ'ר Pro בלבד
- **אל תציע לוח תוכן שלם** למשתמשי Free
- מותר להזכיר: "רוצה לשדרג לPro בשביל פרסומים מתוזמנים?"

## 📢 סוג פרסום — פוסט אורגני vs ממומן

**כשמשתמש מבקש לפרסם לראשונה (בכל שיחה), שאל פעם אחת:**
"פוסט **אורגני** (חינם — מגיע רק לעוקבים) או **ממומן** (בתשלום דרך Ads Manager — מגיע לקהל רחב)?"

**פוסט אורגני** — תוכן מעורב, סיפורי, עם ערך ומידע:
- אורך: בינוני (3-6 שורות)
- טון: חמים, שיתופי, אנושי
- CTA: עדין ("ספרו לנו בתגובות", "שתפו", "בקרו אותנו")

**פרסום ממומן** — תוכן שיווקי ממוקד, מנצח:
- אורך: קצר (2-3 שורות מקסימום)
- כותרת חזקה + יתרון ברור + CTA אגרסיבי
- **חובה לציין**: "מומלץ להוסיף תמונה/וידאו מקצועי לפרסום ממומן"
- CTA: ישיר ("לחץ כאן", "הירשם עכשיו", "קנה היום — הנחה X%")

**תמונות בפרסום ממומן:**
- לאחר כתיבת הטקסט, הצע: "רוצה לצרף תמונה/סרטון מקצועי? לחץ על 📎 בתחתית הצ'אט"

## 🏗️ מגיע מ-AIBuilder — כלל עדיפות עליונה

**אם ההודעה הראשונה מכילה "ILMARIAI AIBuilder" עם פרטי אפליקציה (שם, כתובת, תיאור):**

→ **אסור לשלוח שאלון onboarding כללי**
→ אתה כבר יודע מה המוצר — השתמש בפרטים שסופקו
→ שאל **בדיוק 3 שאלות** אלו ולא יותר:

```
מצוין! ראיתי שבנית [שם האפליקציה] — נתחיל לפרסם 🚀

כדי ליצור פוסטים מושלמים, רק ענה:

1️⃣ מי קהל היעד? (גיל, תחום עניין, מיקום)
2️⃣ יש מבצע / הצעה מיוחדת לציין?
3️⃣ איזה טון מתאים? (חמים / מקצועי / נרגש)
```

### ❌ חוקים קריטיים לאחר שליחת 3 השאלות:
- **אסור** להוסיף שאלה 4, 5, או "יש עוד משהו?" — שלוש שאלות בדיוק
- **אסור** לחזור על השאלות אם המשתמש ענה "לא" — "לא" = תשובה תקינה (אין מבצע, אין להוסיף)
- **חובה** לכתוב פוסט מיד לאחר כל תגובה של המשתמש לשאלות אלו, גם אם התשובה קצרה ("לא", "כן", "מקצועי")
- אם המשתמש ענה "לא" על מבצע → אל תשאל שוב, פשוט כתוב פוסט ללא מבצע
- אם המשתמש לא ענה על שאלה מסוימת → המשך עם ברירת מחדל

→ לאחר כל תגובה של המשתמש — **כתוב פוסטים מיידית, ללא שאלות נוספות**

## תהליך קבלת משתמש חדש (ONBOARDING):

**כשמשתמש מתחבר בפעם הראשונה (אין פרופיל עסקי):**
1. הצג את עצמך בשורה קצרה
2. שלח **שאלון אחד בלבד** עם כל השאלות ביחד:

```
כדי שאוכל לפרסם בצורה חכמה ומדויקת, כמה שאלות קצרות —
(ענה על מה שרלוונטי, השאר ריק את השאר):

1️⃣ שם העסק?
2️⃣ מה העסק עושה/מציע? (תיאור קצר)
3️⃣ מה מייחד אותו מהמתחרים? (USP)
4️⃣ מי קהל היעד? (גיל, תחום עניין, מיקום)
5️⃣ מה הקריאה לפעולה? (לקנות / להירשם / לפנות / לבקר באתר)
6️⃣ קישור לאתר / דף נחיתה?
7️⃣ יש מבצע / הצעה מיוחדת?
8️⃣ איזה טון? (מקצועי / חמים / נרגש / הומוריסטי)
9️⃣ מה המטרה? (מודעות למותג / לידים / מכירות / קהילה)
🔟 תקציב חודשי לפרסום? (בשקלים, אפשר גם "לא יודע")
```

3. אחרי שהמשתמש ענה — קרא ל-`save_business_profile` לשמירה, ואמור:
**"מעולה! הפרופיל שמור. מה תרצה לפרסם היום?"**

### ❌ אסור בתהליך ה-Onboarding:
- לשאול שאלה אחת ולחכות לתשובה, ואז לשאול עוד אחת (פינג-פונג)
- השאלון כולו בהודעה **אחת** בלבד

**כשמשתמש חוזר (יש פרופיל):**
- ברך אותו בשמו/שם העסק בשורה קצרה
- שאל מה הוא רוצה לעשות היום

## עקרונות העבודה:
1. **כתוב קודם, שאל אחר כך** — טיוטה מיידית, שיפורים אחרי
2. הסבר בקצרה מה אתה עומד לעשות
3. דווח על תוצאות בצורה ברורה ואמיתית
4. המלץ על השלבים הבאים לאחר כל פעולה
5. התאם את התוכן לקהל הישראלי (תוך שמירה על אפשרות לפרסום בינלאומי)
6. שמור על אתיקה - אל תשלח ספאם ואל תפר תנאי שימוש

## ⚠️ טיפול בשגיאות פרסום:
- אם פרסום נכשל בגלל שגיאת API → ציין: "הפרסום לא הצליח. שגיאה טכנית: [סיבה]"
- **אל תאמר** "הפלטפורמה לא מחוברת" אם יש שגיאת API — ייתכן שיש בעיה זמנית, לא היעדר חיבור
- **אל תאמר** "נדרשות הרשאות" אם הפלטפורמה מחוברת — השגיאה היא טכנית
- הצע תמיד: "רוצה לנסות שוב?" ו"בינתיים הנה הטקסט לפרסום ידני"

## ⚠️ חוקים ואיסורים — חובה לעמוד בהם:

### 🔐 חוק 1 — אישור לפני פרסום (NO PUBLISHING WITHOUT APPROVAL)
**לפני כל שימוש ב-`post_content` או `schedule_post`:**
- הצג את תוכן הפוסט המלא למשתמש
- שאל: **"האם לאשר ולפרסם/לתזמן? (כן/לא)"**
- המתן לתגובת "כן" מפורשת לפני ביצוע הפרסום
- אם המשתמש ביקש שינויים — ערוך ושאל שוב
- **לעולם אל תפרסם אוטומטית ללא אישור המשתמש**

### ✏️ חוק 2 — גיוון תוכן בין פלטפורמות (NO DUPLICATE TEXT)
כאשר מפרסמים לכמה פלטפורמות בו-זמנית:
- כל פלטפורמה חייבת לקבל גרסה **שונה מעט** של הפוסט (פתיחה שונה, אורך מתאים)
- פייסבוק: ניתן להאריך, LinkedIn: מקצועי יותר, Instagram: ויזואלי + hashtags, Twitter: קצר בלבד
- אין להדביק אותו טקסט מילה במילה לכל הפלטפורמות

### 🎯 חוק 3 — קריאה לפעולה חובה (CTA MANDATORY)
- כל פוסט פרסומי **חייב** לכלול קריאה לפעולה (CTA) ברורה
- ה-CTA חייב לכלול קישור לאתר העסק (מהפרופיל) או דרך יצירת קשר
- דוגמאות: "בקרו ב-[אתר]", "שלחו הודעה", "הירשמו עכשיו"

### 🔒 חוק 4 — קישורים מאושרים בלבד (AUTHORIZED LINKS ONLY)
- אין להוסיף קישורים חיצוניים שאינם מהפרופיל העסקי של המשתמש
- הקישור היחיד המותר הוא ה-website_url מהפרופיל העסקי
- אין ליצור, להמציא, או לצרף URL שלא סופק על ידי המשתמש

### 📋 חוק 5 — תיעוד פעולות (LOG ALL ACTIONS)
- לאחר כל פרסום, תיזמון, או יצירת קמפיין: קרא ל-`log_action`
- פרט: סוג הפעולה, פלטפורמות, תוכן (ראשי 100 תווים), תוצאה

## 🌐 שפה — חוק מחייב:

**עקוב אחרי שפת המשתמש בכל הודעה:**
- משתמש כותב בעברית → ענה בעברית, כתוב פוסטים בעברית
- משתמש כותב באנגלית → ענה באנגלית, כתוב פוסטים באנגלית
- המשתמש ביחר שפה ב-UI → זו שפת ברירת המחדל שלו
- **אסור לשנות שפה ללא בקשה מפורשת**
- אם המשתמש מבקש פוסט בשפה אחרת — כתוב בשפה שביקש

היה ידידותי, מקצועי ומעורר השראה.
תגובות קצרות וממוקדות — לא טבלאות ארוכות וכותרות גדולות.

You are a professional AI advertising assistant. Detect the user's language from each message and always respond in that same language."""


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
    {
        "name": "schedule_post",
        "description": "תזמן פוסט לפרסום בזמן אופטימלי אוטומטי. Schedule a post for automatic publishing at the optimal time.",
        "input_schema": {
            "type": "object",
            "properties": {
                "platforms": {"type": "array", "items": {"type": "string"}, "description": "פלטפורמות לפרסום"},
                "content": {"type": "string", "description": "תוכן הפוסט"},
                "scheduled_for": {"type": "string", "description": "'optimal' לזמן אוטומטי, או תאריך ISO כמו '2024-12-25T09:00'"},
                "hashtags": {"type": "array", "items": {"type": "string"}},
                "media_urls": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["platforms", "content"],
        },
    },
    {
        "name": "list_scheduled_posts",
        "description": "הצג את כל הפוסטים המתוזמנים. List all scheduled posts.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "cancel_scheduled_post",
        "description": "בטל פוסט מתוזמן. Cancel a scheduled post.",
        "input_schema": {
            "type": "object",
            "properties": {
                "job_id": {"type": "string", "description": "מזהה הפוסט המתוזמן"},
            },
            "required": ["job_id"],
        },
    },
    {
        "name": "generate_post_image",
        "description": "צור פרומפט מקצועי לתמונה לפוסט (DALL-E / Midjourney / Canva). Generate image prompt for a post.",
        "input_schema": {
            "type": "object",
            "properties": {
                "platform": {"type": "string"},
                "content": {"type": "string", "description": "תוכן הפוסט"},
                "style": {"type": "string", "description": "professional / vibrant / minimal / story / tiktok"},
                "colors": {"type": "array", "items": {"type": "string"}, "description": "צבעי המותג"},
            },
            "required": ["platform", "content"],
        },
    },
    {
        "name": "create_ab_test",
        "description": "צור שני וריאנטים של פוסט לבדיקת A/B. Create two post variants for A/B testing.",
        "input_schema": {
            "type": "object",
            "properties": {
                "platform": {"type": "string"},
                "topic": {"type": "string"},
                "tone_a": {"type": "string", "description": "סגנון ווריאנט A: professional/casual/funny/inspirational/educational/urgent"},
                "tone_b": {"type": "string", "description": "סגנון ווריאנט B"},
            },
            "required": ["platform", "topic"],
        },
    },
    {
        "name": "translate_content",
        "description": "תרגם פוסט לשפות נוספות (עברית, אנגלית, ערבית). Translate post content to multiple languages.",
        "input_schema": {
            "type": "object",
            "properties": {
                "content": {"type": "string", "description": "תוכן לתרגום"},
                "source_language": {"type": "string", "default": "hebrew"},
                "target_languages": {"type": "array", "items": {"type": "string"}, "description": "english, arabic, french, spanish, russian"},
                "platform": {"type": "string"},
            },
            "required": ["content"],
        },
    },
    {
        "name": "monitor_competitors",
        "description": "נתח מתחרים ומצא הזדמנויות. Analyze competitors and find opportunities.",
        "input_schema": {
            "type": "object",
            "properties": {
                "industry": {"type": "string", "description": "תחום העסק"},
                "competitors": {"type": "array", "items": {"type": "string"}, "description": "שמות מתחרים"},
                "platform": {"type": "string"},
            },
            "required": ["industry", "competitors", "platform"],
        },
    },
    {
        "name": "generate_weekly_report",
        "description": "צור דוח שבועי מקיף של ביצועי הפרסום. Generate comprehensive weekly marketing report.",
        "input_schema": {
            "type": "object",
            "properties": {
                "posts_this_week": {"type": "integer", "default": 0},
                "platforms_active": {"type": "array", "items": {"type": "string"}},
                "top_performing_content": {"type": "string"},
                "total_reach_estimate": {"type": "integer"},
                "new_followers_estimate": {"type": "integer"},
            },
        },
    },
    {
        "name": "generate_smart_reply",
        "description": "צור תגובה חכמה לתגובה ברשת חברתית. Generate smart reply to a social media comment.",
        "input_schema": {
            "type": "object",
            "properties": {
                "comment_text": {"type": "string", "description": "תוכן התגובה שהתקבלה"},
                "platform": {"type": "string"},
                "tone": {"type": "string", "default": "professional", "description": "professional / casual / funny"},
                "comment_sentiment": {"type": "string", "default": "positive", "description": "positive / negative / question / neutral"},
            },
            "required": ["comment_text", "platform"],
        },
    },
    {
        "name": "save_business_profile",
        "description": "שמור פרטי העסק של המשתמש. קרא לכלי הזה לאחר שאספת מידע מספיק על העסק. Save or update the business profile with information gathered from the user.",
        "input_schema": {
            "type": "object",
            "properties": {
                "business_name": {"type": "string", "description": "שם העסק"},
                "website_url": {"type": "string", "description": "כתובת האתר"},
                "description": {"type": "string", "description": "תיאור קצר של העסק"},
                "full_description": {"type": "string", "description": "תיאור מפורט"},
                "product_service": {"type": "string", "description": "מה בדיוק מוצע/נמכר"},
                "unique_value": {"type": "string", "description": "מה מייחד את העסק ממתחרים"},
                "pricing_model": {"type": "string", "description": "freemium / subscription / one_time / free"},
                "price_range": {"type": "string", "description": "טווח מחירים"},
                "target_age_range": {"type": "string", "description": "טווח גילאים של קהל היעד"},
                "target_locations": {"type": "array", "items": {"type": "string"}, "description": "מיקומים גיאוגרפיים"},
                "target_languages": {"type": "array", "items": {"type": "string"}, "description": "שפות"},
                "target_interests": {"type": "array", "items": {"type": "string"}, "description": "תחומי עניין של קהל היעד"},
                "target_pain_points": {"type": "array", "items": {"type": "string"}, "description": "כאבים/בעיות של קהל היעד"},
                "target_professions": {"type": "array", "items": {"type": "string"}, "description": "מקצועות של קהל היעד"},
                "primary_goal": {"type": "string", "description": "brand_awareness / sales / leads / community / app_downloads"},
                "secondary_goals": {"type": "array", "items": {"type": "string"}},
                "monthly_budget": {"type": "number", "description": "תקציב שיווק חודשי בשקלים"},
                "kpis": {"type": "array", "items": {"type": "string"}, "description": "מדדי הצלחה"},
                "tone": {"type": "string", "description": "professional / casual / funny / inspirational / educational"},
                "content_types": {"type": "array", "items": {"type": "string"}, "description": "סוגי תוכן מועדפים"},
                "posting_frequency": {"type": "string", "description": "daily / 3x_week / weekly"},
                "preferred_platforms": {"type": "array", "items": {"type": "string"}, "description": "פלטפורמות מועדפות"},
                "brand_keywords": {"type": "array", "items": {"type": "string"}, "description": "מילות מפתח של המותג"},
                "avoid_topics": {"type": "array", "items": {"type": "string"}, "description": "נושאים להימנע"},
                "competitors": {"type": "array", "items": {"type": "string"}, "description": "שמות מתחרים"},
                "onboarding_complete": {"type": "boolean", "description": "האם ה-onboarding הושלם"},
            },
        },
    },
    {
        "name": "get_business_profile",
        "description": "קבל את פרופיל העסק הנוכחי. Get the current business profile.",
        "input_schema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "generate_targeted_content",
        "description": "צור תוכן פרסומי ממוקד לפי פרופיל העסק. Generate highly targeted content based on the business profile.",
        "input_schema": {
            "type": "object",
            "properties": {
                "platform": {"type": "string", "description": "שם הפלטפורמה"},
                "content_type": {"type": "string", "description": "promotional / educational / story / engagement / announcement"},
                "topic": {"type": "string", "description": "נושא ספציפי לפוסט"},
                "include_cta": {"type": "boolean", "default": True, "description": "האם לכלול קריאה לפעולה"},
            },
            "required": ["platform", "content_type"],
        },
    },
    {
        "name": "find_targeted_groups",
        "description": "מצא קבוצות ממוקדות לפי פרופיל העסק. Find highly targeted groups based on business profile.",
        "input_schema": {
            "type": "object",
            "properties": {
                "platform": {"type": "string"},
                "max_results": {"type": "integer", "default": 20},
            },
            "required": ["platform"],
        },
    },
    {
        "name": "generate_campaign_brief",
        "description": "צור בריף קמפיין שיווקי מלא — מסמך אסטרטגי עם יעדים, מסרים, קהל, תקציב ולוח זמנים. Generate a full advertising campaign brief.",
        "input_schema": {
            "type": "object",
            "properties": {
                "goal": {"type": "string", "description": "brand_awareness / lead_generation / sales / community / app_downloads"},
                "platforms": {"type": "array", "items": {"type": "string"}, "description": "פלטפורמות לקמפיין"},
                "target_audience": {"type": "string", "description": "תיאור קהל היעד"},
                "budget_ils": {"type": "number", "description": "תקציב כולל בשקלים"},
                "duration_weeks": {"type": "integer", "default": 4, "description": "אורך הקמפיין בשבועות"},
            },
            "required": ["goal", "platforms", "target_audience"],
        },
    },
    {
        "name": "submit_to_directory",
        "description": "צור חבילת רישום לדירקטוריות עסקיות (גוגל ביזנס, דפי זהב, ועוד). Generate business directory submission package.",
        "input_schema": {
            "type": "object",
            "properties": {
                "category": {"type": "string", "description": "קטגוריית העסק"},
                "location": {"type": "string", "default": "Israel", "description": "מיקום גיאוגרפי"},
                "phone": {"type": "string", "description": "טלפון (אופציונלי)"},
                "email": {"type": "string", "description": "מייל (אופציונלי)"},
            },
            "required": ["category"],
        },
    },
    {
        "name": "save_to_crm",
        "description": "שמור קשר / ליד שנוצר מפעולה ברשת חברתית ב-CRM הפנימי. Save a lead or contact result to the internal CRM.",
        "input_schema": {
            "type": "object",
            "properties": {
                "contact_name": {"type": "string", "description": "שם הקשר"},
                "contact_platform": {"type": "string", "description": "פלטפורמה שממנה הגיע"},
                "contact_id": {"type": "string", "description": "מזהה המשתמש/קשר בפלטפורמה"},
                "action_taken": {"type": "string", "description": "הפעולה שבוצעה (follow, message, comment)"},
                "notes": {"type": "string", "description": "הערות נוספות"},
                "tags": {"type": "array", "items": {"type": "string"}, "description": "תגיות (ליד חם, B2B, וכו')"},
                "follow_up_date": {"type": "string", "description": "תאריך מעקב מומלץ (ISO)"},
            },
            "required": ["contact_name", "contact_platform", "contact_id", "action_taken"],
        },
    },
    {
        "name": "log_action",
        "description": "תעד פעולה בלוג הביקורת. Log an action to the audit trail. Call after every publish/schedule/campaign action.",
        "input_schema": {
            "type": "object",
            "properties": {
                "action_type": {"type": "string", "description": "post_published / post_scheduled / campaign_created / report_generated / follower_added / comment_posted"},
                "description": {"type": "string", "description": "תיאור קצר של הפעולה"},
                "details": {"type": "object", "description": "פרטים נוספים (פלטפורמה, תוכן וכו')"},
                "status": {"type": "string", "default": "success", "description": "success / failed / pending"},
            },
            "required": ["action_type", "description"],
        },
    },
    {
        "name": "get_action_log",
        "description": "קבל היסטוריית פעולות מלאה של הסשן. Get the full action audit log for this session.",
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "default": 50, "description": "מספר פעולות אחרונות להציג"},
            },
        },
    },
]


class AdvertisingAgent:
    """
    AI Advertising Agent powered by Claude claude-opus-4-6.
    Manages social media presence and advertising campaigns.
    """

    def __init__(self, session_id: str = "default"):
        self.session_id = session_id
        self.plan = "free"
        self.client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
        self.conversation_history: List[Dict[str, Any]] = []
        self.connected_platforms: Dict[str, Any] = {}
        self.current_campaign: Optional[Campaign] = None

        # Load or create business profile for this session
        self.profile = ProfileManager.get_or_create(session_id)

        # Restore conversation history from disk
        self.conversation_history = HistoryManager.load(session_id)

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

    def set_platform_tokens(self, tokens: Dict[str, str], page_ids: Dict[str, str] = None) -> None:
        """Update platform instances with per-user OAuth tokens (plan-gated)."""
        page_ids = page_ids or {}
        # Count currently connected (real token) platforms
        already_connected = sum(
            1 for p in self.platforms.values() if not getattr(p, "demo_mode", True)
        )
        for platform_name, token in tokens.items():
            if not token:
                continue
            # Skip if already registered with a real token (re-auth is fine)
            if not getattr(self.platforms.get(platform_name), "demo_mode", True):
                pass  # updating existing — doesn't count as new
            else:
                allowed, reason = FeatureGate.check_platform_limit(self.plan, already_connected)
                if not allowed:
                    logger.warning(f"Platform limit reached for plan={self.plan}: {reason}")
                    continue
                already_connected += 1

            page_id = page_ids.get(platform_name)
            if platform_name == "facebook":
                platform = FacebookPlatform(access_token=token, page_id=page_id)
            elif platform_name == "instagram":
                platform = InstagramPlatform(access_token=token)
            elif platform_name == "twitter":
                platform = TwitterPlatform(access_token=token)
            elif platform_name == "linkedin":
                platform = LinkedInPlatform(access_token=token)
            elif platform_name == "tiktok":
                platform = TikTokPlatform(access_token=token)
            else:
                continue
            self.platforms[platform_name] = platform
            social_tools.register_platform(platform_name, platform)
            analytics_tools.register_platform(platform_name, platform)
            logger.info(f"Updated {platform_name} with user token (page_id={page_id}) for session {self.session_id}")

    async def connect_platform(self, platform_name: str) -> Optional[PlatformAccount]:
        """Connect to a social media platform and return account info (plan-gated)."""
        platform = self.platforms.get(platform_name)
        if not platform:
            logger.error(f"Unknown platform: {platform_name}")
            return None

        # Check if re-connecting an already-connected platform (always allowed)
        if platform_name not in self.connected_platforms:
            current = len(self.connected_platforms)
            allowed, reason = FeatureGate.check_platform_limit(self.plan, current)
            if not allowed:
                logger.warning(f"Platform limit for session {self.session_id}: {reason}")
                raise ValueError(reason)

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

    def _build_system_prompt(self) -> str:
        """Build dynamic system prompt with business profile context."""
        self.profile = ProfileManager.get_or_create(self.session_id)
        profile_context = self.profile.to_agent_context()

        if not self.profile.onboarding_complete:
            onboarding_instruction = """
## 🚀 התחלה - שאלון עסקי:
המשתמש עדיין לא הגדיר פרופיל עסקי. התחל את השיחה עם שאלון קצר וידידותי:
1. שם העסק / האתר
2. מה המוצר או השירות בדיוק?
3. מי קהל היעד? (גיל, תחומי עניין, מקצוע)
4. מה המטרה העיקרית? (מודעות / מכירות / גיוס משתמשים)
5. מה הייחודיות שלך לעומת מתחרים?
6. איזה טון? (מקצועי / קליל / מצחיק / מעורר השראה)
7. תקציב חודשי לשיווק (בשקלים)

לאחר שאספת את המידע → קרא לכלי `save_business_profile` כדי לשמור את הפרופיל.
"""
        else:
            onboarding_instruction = ""

        return SYSTEM_PROMPT + "\n\n" + profile_context + onboarding_instruction

    def _select_model(self, message: str) -> tuple[str, bool]:
        """
        Choose model based on message complexity.
        Returns (model_name, use_extended_thinking).
        - Complex tasks → claude-opus-4-6 + thinking (best quality)
        - Simple tasks  → claude-sonnet-4-6 (fast + cheap)
        """
        OPUS_KEYWORDS = [
            # Hebrew
            "אסטרטגיה", "קמפיין", "ניתוח", "דוח", "תכנון", "מתחרים",
            "תקציב", "יעדים", "שנתי", "רבעוני", "מחקר", "השוואה",
            # English
            "strategy", "campaign", "analysis", "report", "planning",
            "competitor", "budget", "annual", "quarterly", "research",
            "comprehensive", "detailed", "full plan",
        ]
        needs_opus = any(kw in message.lower() for kw in OPUS_KEYWORDS)
        if needs_opus:
            return "claude-opus-4-6", True
        return "claude-sonnet-4-6", False

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
        dynamic_system = self._build_system_prompt()

        # Select model based on message complexity
        model, use_thinking = self._select_model(user_message)
        logger.info(f"Model selected: {model} (thinking={use_thinking})")

        while True:
            create_kwargs = dict(
                model=model,
                max_tokens=8096,
                system=dynamic_system,
                tools=TOOLS,
                messages=messages,
            )
            if use_thinking:
                create_kwargs["thinking"] = {"type": "adaptive"}

            response = self.client.messages.create(**create_kwargs)

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
                # Persist to disk so history survives restarts
                HistoryManager.save(self.session_id, self.conversation_history)
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

            # Scheduler tools
            elif tool_name == "schedule_post":
                ok, reason = FeatureGate.check_scheduling_quota(self.session_id, self.plan)
                if not ok:
                    return {"error": reason, "blocked": True}
                result = schedule_post(session_id=self.session_id, **tool_input)
                FeatureGate.record_scheduled_post(self.session_id)
                return result
            elif tool_name == "list_scheduled_posts":
                return list_scheduled_posts(session_id=self.session_id)
            elif tool_name == "cancel_scheduled_post":
                return cancel_scheduled_post(**tool_input)

            # Advanced tools
            elif tool_name == "generate_post_image":
                return generate_post_image_prompt(
                    business_name=self.profile.business_name, **tool_input
                )
            elif tool_name == "create_ab_test":
                ok, reason = FeatureGate.check(self.plan, "ab_testing")
                if not ok:
                    return {"error": reason, "blocked": True}
                return create_ab_test(
                    business_name=self.profile.business_name,
                    website_url=self.profile.website_url,
                    **tool_input,
                )
            elif tool_name == "translate_content":
                langs = tool_input.get("target_languages", [])
                ok, reason = FeatureGate.check_translation_languages(self.plan, len(langs))
                if not ok:
                    return {"error": reason, "blocked": True}
                return translate_content(
                    business_context=self.profile.description, **tool_input
                )
            elif tool_name == "monitor_competitors":
                ok, reason = FeatureGate.check(self.plan, "competitor_analysis")
                if not ok:
                    return {"error": reason, "blocked": True}
                return monitor_competitors(
                    business_name=self.profile.business_name, **tool_input
                )
            elif tool_name == "generate_weekly_report":
                ok, reason = FeatureGate.check(self.plan, "weekly_report")
                if not ok:
                    return {"error": reason, "blocked": True}
                return generate_weekly_report(
                    session_id=self.session_id,
                    business_name=self.profile.business_name,
                    website_url=self.profile.website_url,
                    **tool_input,
                )
            elif tool_name == "generate_smart_reply":
                ok, reason = FeatureGate.check(self.plan, "smart_reply")
                if not ok:
                    return {"error": reason, "blocked": True}
                return generate_smart_reply(
                    business_name=self.profile.business_name,
                    tone=self.profile.content_strategy.tone,
                    **tool_input,
                )

            # Profile tools
            elif tool_name == "save_business_profile":
                return self._save_business_profile(**tool_input)
            elif tool_name == "get_business_profile":
                return self._get_business_profile()
            elif tool_name == "generate_targeted_content":
                return self._generate_targeted_content(**tool_input)
            elif tool_name == "find_targeted_groups":
                return await self._find_targeted_groups(**tool_input)

            # New tools: campaign brief, directories, CRM, audit log
            elif tool_name == "generate_campaign_brief":
                return generate_campaign_brief(
                    business_name=self.profile.business_name,
                    unique_value=self.profile.unique_value,
                    website_url=self.profile.website_url,
                    **tool_input,
                )
            elif tool_name == "submit_to_directory":
                return submit_to_directory(
                    business_name=self.profile.business_name,
                    business_description=self.profile.description,
                    website_url=self.profile.website_url,
                    **tool_input,
                )
            elif tool_name == "save_to_crm":
                return save_to_crm(session_id=self.session_id, **tool_input)
            elif tool_name == "log_action":
                return log_action(session_id=self.session_id, **tool_input)
            elif tool_name == "get_action_log":
                return {"actions": get_action_log(session_id=self.session_id, **tool_input)}

            else:
                return {"error": f"Unknown tool: {tool_name}"}

        except Exception as e:
            logger.error(f"Tool {tool_name} failed: {e}", exc_info=True)
            return {"error": str(e), "tool": tool_name}

    def _save_business_profile(self, **kwargs) -> Dict[str, Any]:
        """Save business profile from agent-collected data."""
        profile = ProfileManager.get_or_create(self.session_id)

        # Basic info
        for field in ["business_name", "website_url", "description", "full_description",
                      "product_service", "unique_value", "pricing_model", "price_range"]:
            if field in kwargs and kwargs[field]:
                setattr(profile, field, kwargs[field])

        # Target audience
        if any(k.startswith("target_") for k in kwargs):
            profile.target_audience.age_range = kwargs.get("target_age_range", profile.target_audience.age_range)
            if kwargs.get("target_locations"): profile.target_audience.locations = kwargs["target_locations"]
            if kwargs.get("target_languages"): profile.target_audience.languages = kwargs["target_languages"]
            if kwargs.get("target_interests"): profile.target_audience.interests = kwargs["target_interests"]
            if kwargs.get("target_pain_points"): profile.target_audience.pain_points = kwargs["target_pain_points"]
            if kwargs.get("target_professions"): profile.target_audience.profession = kwargs["target_professions"]

        # Goals
        if kwargs.get("primary_goal"): profile.goals.primary_goal = kwargs["primary_goal"]
        if kwargs.get("secondary_goals"): profile.goals.secondary_goals = kwargs["secondary_goals"]
        if kwargs.get("monthly_budget"): profile.goals.monthly_budget_ils = kwargs["monthly_budget"]
        if kwargs.get("kpis"): profile.goals.kpis = kwargs["kpis"]

        # Content strategy
        if kwargs.get("tone"): profile.content_strategy.tone = kwargs["tone"]
        if kwargs.get("content_types"): profile.content_strategy.content_types = kwargs["content_types"]
        if kwargs.get("posting_frequency"): profile.content_strategy.posting_frequency = kwargs["posting_frequency"]
        if kwargs.get("preferred_platforms"): profile.content_strategy.preferred_platforms = kwargs["preferred_platforms"]
        if kwargs.get("brand_keywords"): profile.content_strategy.brand_keywords = kwargs["brand_keywords"]
        if kwargs.get("avoid_topics"): profile.content_strategy.avoid_topics = kwargs["avoid_topics"]

        # Competitors
        if kwargs.get("competitors"):
            profile.competitors = [CompetitorInfo(name=c) for c in kwargs["competitors"]]

        # Onboarding complete flag
        if kwargs.get("onboarding_complete"):
            profile.onboarding_complete = True

        ProfileManager.save(profile)
        self.profile = profile

        return {
            "success": True,
            "message": "פרופיל העסק נשמר בהצלחה",
            "profile_complete": profile.onboarding_complete,
            "business_name": profile.business_name,
        }

    def _get_business_profile(self) -> Dict[str, Any]:
        """Get current business profile as dict."""
        profile = ProfileManager.get_or_create(self.session_id)
        return {
            "business_name": profile.business_name,
            "website_url": profile.website_url,
            "description": profile.description,
            "product_service": profile.product_service,
            "unique_value": profile.unique_value,
            "target_audience": {
                "age_range": profile.target_audience.age_range,
                "locations": profile.target_audience.locations,
                "interests": profile.target_audience.interests,
                "pain_points": profile.target_audience.pain_points,
            },
            "goals": {
                "primary": profile.goals.primary_goal,
                "budget_ils": profile.goals.monthly_budget_ils,
            },
            "content_strategy": {
                "tone": profile.content_strategy.tone,
                "platforms": profile.content_strategy.preferred_platforms,
                "frequency": profile.content_strategy.posting_frequency,
            },
            "onboarding_complete": profile.onboarding_complete,
        }

    def _generate_targeted_content(
        self,
        platform: str,
        content_type: str,
        topic: str = "",
        include_cta: bool = True,
    ) -> Dict[str, Any]:
        """Generate highly targeted content based on business profile."""
        profile = self.profile
        if not profile.onboarding_complete:
            return {"error": "פרופיל עסקי לא מלא. אנא השלם את ה-onboarding תחילה."}

        # Build targeted content guidelines
        tone_map = {
            "professional": "מקצועי, ישיר, מבוסס נתונים",
            "casual": "קליל, ידידותי, שיחתי",
            "funny": "הומוריסטי, קליל, מבדר",
            "inspirational": "מעורר השראה, מוטיבציוני, חיובי",
            "educational": "מלמד, מעמיק, מוסיף ערך",
        }

        char_limits = {
            "facebook": 500,
            "instagram": 300,
            "twitter": 280,
            "linkedin": 700,
            "tiktok": 150,
            "youtube": 200,
        }

        cta_map = {
            "sales": f"🎯 התחל עכשיו → {profile.website_url}",
            "leads": f"📝 השאר פרטים ונחזור אליך → {profile.website_url}",
            "brand_awareness": f"🔗 גלה עוד → {profile.website_url}",
            "community": f"💬 הצטרף אלינו → {profile.website_url}",
        }

        return {
            "platform": platform,
            "content_type": content_type,
            "guidelines": {
                "business": profile.business_name,
                "website": profile.website_url,
                "tone": tone_map.get(profile.content_strategy.tone, "מקצועי"),
                "target_audience": f"{profile.target_audience.age_range}, {', '.join(profile.target_audience.interests[:3])}",
                "pain_points_to_address": profile.target_audience.pain_points[:2],
                "unique_value_to_highlight": profile.unique_value,
                "max_chars": char_limits.get(platform, 300),
                "suggested_hashtags": profile.content_strategy.brand_keywords[:5],
                "cta": cta_map.get(profile.goals.primary_goal, f"→ {profile.website_url}") if include_cta else "",
                "topic": topic or profile.product_service,
                "avoid": profile.content_strategy.avoid_topics,
            },
            "instruction": "השתמש בהנחיות אלה ליצירת פוסט ממוקד ואפקטיבי לפלטפורמה",
        }

    async def _find_targeted_groups(
        self,
        platform: str,
        max_results: int = 20,
    ) -> Dict[str, Any]:
        """Find groups highly relevant to the business profile."""
        profile = self.profile
        if not profile.onboarding_complete:
            return {"error": "פרופיל עסקי לא מלא"}

        # Build smart keywords from profile
        keywords = (
            profile.target_audience.interests[:4] +
            profile.content_strategy.brand_keywords[:3] +
            [profile.product_service] +
            profile.target_audience.profession[:2]
        )
        keywords = [k for k in keywords if k]

        # Use existing find_relevant_groups tool
        return await social_tools.find_relevant_groups(
            platform=platform,
            keywords=keywords,
            limit=max_results,
        )

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
        """Clear conversation history from memory and disk."""
        self.conversation_history = []
        HistoryManager.clear(self.session_id)

    async def close(self):
        """Close all platform connections."""
        for platform in self.platforms.values():
            await platform.close()
