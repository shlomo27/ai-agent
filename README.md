# 🚀 עוזר פרסום AI / AI Advertising Agent

<div dir="rtl">

## מה זה?

עוזר פרסום AI אישי המופעל על ידי Claude claude-opus-4-6. המערכת מנהלת את כל הפרסום שלך ברשתות החברתיות באופן אוטומטי וחכם.

## יכולות

### 🌐 רשתות חברתיות נתמכות
- **פייסבוק** - פוסטים, קבוצות, עמודים, פרסום ממומן
- **אינסטגרם** - תמונות, סרטוני ריילס, סטוריז
- **טוויטר / X** - ציוצים, תגובות, טרנדים
- **לינקדאין** - עדכונים מקצועיים, קבוצות, חיבורים
- **יוטיוב** - העלאת סרטונים, תגובות, מנויים
- **טיקטוק** - סרטונים קצרים, טרנדים, עוקבים

### 🎯 פונקציות עיקריות
- ✅ גיוס קהל יעד רלוונטי
- ✅ פרסום אוטומטי לכל הפלטפורמות
- ✅ מעורבות פעילה (תגובות, לייקים, עוקבים)
- ✅ יצירת תוכן מותאם אישית
- ✅ לוח תוכן חודשי
- ✅ ניתוח ביצועים
- ✅ המלצות על פלטפורמות חדשות
- ✅ הנחיה בפרסום ממומן (גוגל אדס, פייסבוק אדס)

## התקנה

### דרישות מקדימות
- Python 3.11+
- חשבון Anthropic עם API key

### שלבים

```bash
# 1. שכפול הפרויקט
git clone <repo-url>
cd ai-agent

# 2. התקנת תלויות
pip install -r requirements.txt

# 3. הגדרת משתני סביבה
cp .env.example .env
# ערוך את .env והוסף את המפתחות שלך

# 4. הפעלה
python main.py start
```

## שימוש

### מצב שיחה אינטראקטיבי
```bash
python main.py start
```

### יצירת קמפיין חדש
```bash
python main.py campaign
```

### חיבור פלטפורמה
```bash
python main.py connect facebook
python main.py connect instagram
```

### הפעלת API Server
```bash
python main.py serve --port 8000
```

### צפייה בניתוח ביצועים
```bash
python main.py analytics --days 30
python main.py analytics --platform facebook
```

### קבלת המלצות
```bash
python main.py recommend --platforms facebook,instagram --goals new_users,sales
```

## REST API

לאחר הפעלת `python main.py serve`:

### Chat
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "פרסם פוסט על המוצר החדש שלי בפייסבוק"}'
```

### פרסום פוסט
```bash
curl -X POST http://localhost:8000/api/posts \
  -H "Content-Type: application/json" \
  -d '{
    "platforms": ["facebook", "instagram"],
    "content": "פוסט לדוגמה!",
    "hashtags": ["ישראל", "עסקים"]
  }'
```

### תיעוד API מלא
פתח: http://localhost:8000/docs

## הגדרת API Keys

### Anthropic (חובה)
1. כנס ל: https://console.anthropic.com
2. צור API key
3. הוסף ל-.env: `ANTHROPIC_API_KEY=...`

### Facebook / Meta
1. כנס ל: https://developers.facebook.com
2. צור אפליקציה חדשה
3. קבל App ID, App Secret ו-Access Token

### Instagram
- משתמש ב-Meta Graph API (אותם credentials כמו פייסבוק)

### Twitter / X
1. כנס ל: https://developer.twitter.com
2. צור Project ו-App
3. קבל API keys ו-Bearer Token

### LinkedIn
1. כנס ל: https://www.linkedin.com/developers/
2. צור Application
3. קבל Client ID ו-Client Secret

### YouTube
1. כנס ל: https://console.developers.google.com
2. הפעל YouTube Data API v3
3. צור OAuth 2.0 credentials

### TikTok
1. כנס ל: https://developers.tiktok.com
2. צור Application
3. קבל Client Key ו-Client Secret

## מצב דמו

ברירת המחדל היא `DEMO_MODE=true` - לא מתבצעות פעולות אמיתיות.
לשינוי: `DEMO_MODE=false` ב-.env

## מבנה הפרויקט

```
ai-agent/
├── main.py              # נקודת כניסה ראשית + CLI
├── agent.py             # הסוכן הראשי עם Claude AI
├── config.py            # הגדרות ומשתני סביבה
├── questionnaire.py     # שאלון הגדרת קמפיין
├── requirements.txt     # תלויות Python
├── .env.example         # תבנית משתני סביבה
│
├── models/              # מודלי נתונים (Pydantic)
│   ├── campaign.py      # מודלי קמפיין ומטרות
│   └── platform.py      # מודלי פלטפורמות
│
├── platforms/           # אינטגרציות רשתות חברתיות
│   ├── base.py          # מחלקת בסיס
│   ├── facebook.py      # Meta Graph API
│   ├── instagram.py     # Instagram API
│   ├── twitter.py       # Twitter API v2
│   ├── linkedin.py      # LinkedIn API
│   ├── youtube.py       # YouTube Data API v3
│   └── tiktok.py        # TikTok API
│
├── tools/               # כלים לסוכן AI
│   ├── social_tools.py  # פעולות ברשתות חברתיות
│   ├── content_tools.py # יצירת תוכן
│   ├── analytics_tools.py # ניתוח ביצועים
│   └── advertising_tools.py # פרסום ממומן
│
└── api/                 # REST API (FastAPI)
    ├── main.py          # הגדרות ו-endpoints
    └── schemas.py       # סכמות Pydantic ל-API
```

## תרומה

Pull requests מתקבלים בברכה!

</div>

---

## English Summary

An AI-powered advertising assistant built with Claude claude-opus-4-6. Manages social media presence across Facebook, Instagram, Twitter/X, LinkedIn, YouTube, and TikTok. Features include automated posting, audience discovery, engagement automation, content generation, analytics, and paid advertising guidance.

**Tech Stack:** Python, FastAPI, Anthropic Claude API, Pydantic, Rich, Typer
