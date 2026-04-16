"""
Configuration management for the AI Advertising Agent.
Loads environment variables and provides platform configurations.
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Claude AI
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")

    # Demo Mode - simulates API calls without real credentials
    DEMO_MODE: bool = os.getenv("DEMO_MODE", "true").lower() == "true"

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # API Server
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    PUBLIC_API_URL: str = os.getenv("PUBLIC_API_URL", "http://localhost:8000")

    # Facebook / Meta
    FACEBOOK_APP_ID: str = os.getenv("FACEBOOK_APP_ID", "")
    FACEBOOK_APP_SECRET: str = os.getenv("FACEBOOK_APP_SECRET", "")
    FACEBOOK_ACCESS_TOKEN: str = os.getenv("FACEBOOK_ACCESS_TOKEN", "")
    FACEBOOK_PAGE_ID: str = os.getenv("FACEBOOK_PAGE_ID", "")

    # Instagram
    INSTAGRAM_ACCESS_TOKEN: str = os.getenv("INSTAGRAM_ACCESS_TOKEN", "")
    INSTAGRAM_ACCOUNT_ID: str = os.getenv("INSTAGRAM_ACCOUNT_ID", "")

    # Twitter / X
    TWITTER_API_KEY: str = os.getenv("TWITTER_API_KEY", "")
    TWITTER_API_SECRET: str = os.getenv("TWITTER_API_SECRET", "")
    TWITTER_ACCESS_TOKEN: str = os.getenv("TWITTER_ACCESS_TOKEN", "")
    TWITTER_ACCESS_SECRET: str = os.getenv("TWITTER_ACCESS_SECRET", "")
    TWITTER_BEARER_TOKEN: str = os.getenv("TWITTER_BEARER_TOKEN", "")

    # LinkedIn
    LINKEDIN_CLIENT_ID: str = os.getenv("LINKEDIN_CLIENT_ID", "")
    LINKEDIN_CLIENT_SECRET: str = os.getenv("LINKEDIN_CLIENT_SECRET", "")
    LINKEDIN_ACCESS_TOKEN: str = os.getenv("LINKEDIN_ACCESS_TOKEN", "")

    # YouTube / Google
    YOUTUBE_API_KEY: str = os.getenv("YOUTUBE_API_KEY", "")
    YOUTUBE_CLIENT_ID: str = os.getenv("YOUTUBE_CLIENT_ID", "")
    YOUTUBE_CLIENT_SECRET: str = os.getenv("YOUTUBE_CLIENT_SECRET", "")
    YOUTUBE_REFRESH_TOKEN: str = os.getenv("YOUTUBE_REFRESH_TOKEN", "")

    # TikTok
    TIKTOK_CLIENT_KEY: str = os.getenv("TIKTOK_CLIENT_KEY", "")
    TIKTOK_CLIENT_SECRET: str = os.getenv("TIKTOK_CLIENT_SECRET", "")
    TIKTOK_ACCESS_TOKEN: str = os.getenv("TIKTOK_ACCESS_TOKEN", "")

    # Google Ads
    GOOGLE_ADS_DEVELOPER_TOKEN: str = os.getenv("GOOGLE_ADS_DEVELOPER_TOKEN", "")
    GOOGLE_ADS_CLIENT_ID: str = os.getenv("GOOGLE_ADS_CLIENT_ID", "")
    GOOGLE_ADS_CLIENT_SECRET: str = os.getenv("GOOGLE_ADS_CLIENT_SECRET", "")
    GOOGLE_ADS_REFRESH_TOKEN: str = os.getenv("GOOGLE_ADS_REFRESH_TOKEN", "")
    GOOGLE_ADS_CUSTOMER_ID: str = os.getenv("GOOGLE_ADS_CUSTOMER_ID", "")


# Platform metadata
SUPPORTED_PLATFORMS = {
    "facebook": {
        "name": "Facebook",
        "name_he": "פייסבוק",
        "icon": "📘",
        "features": ["posts", "groups", "pages", "ads", "videos", "stories"],
        "best_for": ["B2C", "local_business", "events", "community"],
        "api_url": "https://graph.facebook.com/v18.0",
        "docs_url": "https://developers.facebook.com/docs/",
    },
    "instagram": {
        "name": "Instagram",
        "name_he": "אינסטגרם",
        "icon": "📸",
        "features": ["photos", "videos", "reels", "stories", "ads", "hashtags"],
        "best_for": ["visual_brands", "fashion", "food", "travel", "influencers"],
        "api_url": "https://graph.instagram.com",
        "docs_url": "https://developers.facebook.com/docs/instagram-api/",
    },
    "twitter": {
        "name": "Twitter / X",
        "name_he": "טוויטר / X",
        "icon": "🐦",
        "features": ["tweets", "threads", "replies", "trending", "ads"],
        "best_for": ["news", "tech", "thought_leaders", "real_time"],
        "api_url": "https://api.twitter.com/2",
        "docs_url": "https://developer.twitter.com/en/docs",
    },
    "linkedin": {
        "name": "LinkedIn",
        "name_he": "לינקדאין",
        "icon": "💼",
        "features": ["posts", "articles", "groups", "connections", "ads", "jobs"],
        "best_for": ["B2B", "professionals", "recruiting", "thought_leadership"],
        "api_url": "https://api.linkedin.com/v2",
        "docs_url": "https://learn.microsoft.com/en-us/linkedin/",
    },
    "youtube": {
        "name": "YouTube",
        "name_he": "יוטיוב",
        "icon": "▶️",
        "features": ["videos", "shorts", "playlists", "live", "ads", "community"],
        "best_for": ["tutorials", "entertainment", "brands", "long_form"],
        "api_url": "https://www.googleapis.com/youtube/v3",
        "docs_url": "https://developers.google.com/youtube/v3",
    },
    "tiktok": {
        "name": "TikTok",
        "name_he": "טיקטוק",
        "icon": "🎵",
        "features": ["videos", "live", "duets", "ads", "trending"],
        "best_for": ["gen_z", "viral", "entertainment", "short_videos"],
        "api_url": "https://open.tiktokapis.com/v2",
        "docs_url": "https://developers.tiktok.com/",
    },
}

config = Config()
