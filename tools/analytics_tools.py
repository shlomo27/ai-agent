"""
Analytics and performance tracking tools.
"""
from __future__ import annotations
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# Platform registry for analytics
_platform_registry: Dict[str, Any] = {}
_campaign_store: Dict[str, Any] = {}


def register_platform(name: str, platform_instance: Any):
    _platform_registry[name] = platform_instance


def store_campaign(campaign_id: str, campaign_data: Dict[str, Any]):
    _campaign_store[campaign_id] = campaign_data


def _real_post_counts(session_id: str, days: int = 30) -> Dict[str, int]:
    """Count actual published posts per platform from scheduler + audit log."""
    counts: Dict[str, int] = {}
    cutoff = datetime.now() - timedelta(days=days)
    try:
        from tools.scheduler import PostScheduler
        for j in PostScheduler._load_jobs():
            if j.get("session_id") != session_id:
                continue
            raw = j.get("created_at") or j.get("scheduled_for", "")
            try:
                ts = datetime.fromisoformat(raw.replace("+00:00", "")).replace(tzinfo=None)
            except Exception:
                continue
            if ts < cutoff:
                continue
            for p in j.get("platforms", []):
                counts[p] = counts.get(p, 0) + 1
    except Exception as e:
        logger.warning(f"Could not load scheduler data: {e}")
    try:
        from tools.action_log import get_action_log
        kws = ("post_published", "publish", "פרסם", "פרסום", "posted")
        for entry in get_action_log(session_id, limit=200):
            try:
                ts = datetime.fromisoformat(entry["timestamp"])
            except Exception:
                continue
            if ts.replace(tzinfo=None) < cutoff:
                continue
            text = (entry.get("action_type", "") + " " + entry.get("description", "")).lower()
            if not any(k in text for k in kws):
                continue
            details = entry.get("details", {})
            plats = details.get("platforms") or (
                [details["platform"]] if details.get("platform") else []
            )
            for p in plats:
                counts[p] = counts.get(p, 0) + 1
    except Exception as e:
        logger.warning(f"Could not load audit log: {e}")
    return counts


def _fetch_real_stats(platform_name: str, platform) -> Dict[str, Any]:
    """Fetch real analytics from a connected platform (synchronous httpx)."""
    try:
        import httpx
        token = getattr(platform, "access_token", "")
        if not token:
            return {}

        if platform_name == "youtube" and getattr(platform, "_oauth_mode", False):
            return _fetch_youtube_stats(token)
        elif platform_name == "facebook":
            return _fetch_facebook_stats(token, getattr(platform, "page_id", None))
        elif platform_name == "twitter":
            return _fetch_twitter_stats(token)
        elif platform_name == "linkedin":
            return _fetch_linkedin_stats(token)

    except Exception as e:
        logger.warning(f"Real stats fetch failed for {platform_name}: {e}")
    return {}


def _fetch_youtube_stats(token: str) -> Dict[str, Any]:
    """Fetch YouTube channel stats + per-video breakdown."""
    import httpx
    result: Dict[str, Any] = {}
    try:
        # Channel-level stats
        r = httpx.get(
            "https://www.googleapis.com/youtube/v3/channels",
            params={"part": "statistics,contentDetails", "mine": "true"},
            headers={"Authorization": f"Bearer {token}"},
            timeout=10, follow_redirects=True,
        )
        if r.status_code != 200:
            return {"error": f"YouTube API {r.status_code}"}
        items = r.json().get("items", [])
        if not items:
            return {}
        ch = items[0]
        stats = ch.get("statistics", {})
        result["subscribers"] = int(stats.get("subscriberCount", 0))
        result["total_views"] = int(stats.get("viewCount", 0))
        result["total_videos"] = int(stats.get("videoCount", 0))

        # Per-video stats via uploads playlist
        uploads_playlist = (
            ch.get("contentDetails", {})
            .get("relatedPlaylists", {})
            .get("uploads", "")
        )
        if uploads_playlist:
            pl_r = httpx.get(
                "https://www.googleapis.com/youtube/v3/playlistItems",
                params={
                    "part": "contentDetails",
                    "playlistId": uploads_playlist,
                    "maxResults": "10",
                },
                headers={"Authorization": f"Bearer {token}"},
                timeout=10,
            )
            if pl_r.status_code == 200:
                video_ids = [
                    item["contentDetails"]["videoId"]
                    for item in pl_r.json().get("items", [])
                ]
                if video_ids:
                    vid_r = httpx.get(
                        "https://www.googleapis.com/youtube/v3/videos",
                        params={
                            "part": "statistics,snippet",
                            "id": ",".join(video_ids),
                        },
                        headers={"Authorization": f"Bearer {token}"},
                        timeout=10,
                    )
                    if vid_r.status_code == 200:
                        videos = []
                        for v in vid_r.json().get("items", []):
                            vs = v.get("statistics", {})
                            videos.append({
                                "title": v.get("snippet", {}).get("title", "")[:60],
                                "views": int(vs.get("viewCount", 0)),
                                "likes": int(vs.get("likeCount", 0)),
                                "comments": int(vs.get("commentCount", 0)),
                            })
                        result["videos"] = sorted(videos, key=lambda x: x["views"], reverse=True)
    except Exception as e:
        logger.warning(f"YouTube stats error: {e}")
    return result


def _fetch_facebook_stats(token: str, page_id: str = None) -> Dict[str, Any]:
    """Fetch Facebook page stats + recent post insights using Page Access Token."""
    import httpx
    result: Dict[str, Any] = {}
    page_token = token  # may be upgraded to Page Access Token below
    try:
        # Always fetch accounts to get Page Access Token (needed for insights)
        accounts_r = httpx.get(
            "https://graph.facebook.com/me/accounts",
            params={"fields": "id,name,access_token,fan_count,followers_count", "access_token": token},
            timeout=8,
        )
        if accounts_r.status_code == 200:
            pages = accounts_r.json().get("data", [])
            # Match the stored page_id or take the first page
            matched = next((p for p in pages if p.get("id") == str(page_id)), None) if page_id else None
            matched = matched or (pages[0] if pages else None)
            if matched:
                page_id = matched["id"]
                page_token = matched.get("access_token", token)  # Page Access Token
                result["page_name"] = matched.get("name", "")
                result["followers"] = matched.get("followers_count") or matched.get("fan_count", 0)

        if not page_id:
            return result

        # Page details with Page Access Token
        page_r = httpx.get(
            f"https://graph.facebook.com/{page_id}",
            params={"fields": "fan_count,followers_count,name,posts_count", "access_token": page_token},
            timeout=8,
        )
        if page_r.status_code == 200:
            d = page_r.json()
            result["followers"] = d.get("followers_count") or d.get("fan_count") or result.get("followers", 0)
            result["page_name"] = result.get("page_name") or d.get("name", "")

        # Recent posts with engagement (requires Page Access Token)
        posts_r = httpx.get(
            f"https://graph.facebook.com/{page_id}/posts",
            params={
                "fields": "message,story,created_time,likes.summary(true),comments.summary(true),shares",
                "limit": "5",
                "access_token": page_token,
            },
            timeout=8,
        )
        if posts_r.status_code == 200:
            posts = []
            for p in posts_r.json().get("data", []):
                text = p.get("message") or p.get("story") or ""
                posts.append({
                    "preview": text[:60],
                    "likes": p.get("likes", {}).get("summary", {}).get("total_count", 0),
                    "comments": p.get("comments", {}).get("summary", {}).get("total_count", 0),
                    "shares": p.get("shares", {}).get("count", 0),
                })
            if posts:
                result["recent_posts"] = posts
        else:
            result["posts_note"] = f"posts API {posts_r.status_code}"

    except Exception as e:
        logger.warning(f"Facebook stats error: {e}")
        result["error"] = str(e)
    return result


def _fetch_twitter_stats(token: str) -> Dict[str, Any]:
    """Fetch Twitter/X user metrics for recent tweets."""
    import httpx
    result: Dict[str, Any] = {}
    try:
        # Get authenticated user
        me_r = httpx.get(
            "https://api.twitter.com/2/users/me",
            params={"user.fields": "public_metrics"},
            headers={"Authorization": f"Bearer {token}"},
            timeout=8,
        )
        if me_r.status_code != 200:
            return {}
        user = me_r.json().get("data", {})
        metrics = user.get("public_metrics", {})
        result["followers"] = metrics.get("followers_count", 0)
        result["following"] = metrics.get("following_count", 0)
        result["tweet_count"] = metrics.get("tweet_count", 0)

        # Recent tweets with metrics
        user_id = user.get("id")
        if user_id:
            tweets_r = httpx.get(
                f"https://api.twitter.com/2/users/{user_id}/tweets",
                params={
                    "tweet.fields": "public_metrics,created_at",
                    "max_results": "5",
                },
                headers={"Authorization": f"Bearer {token}"},
                timeout=8,
            )
            if tweets_r.status_code == 200:
                tweets = []
                for t in tweets_r.json().get("data", []):
                    pm = t.get("public_metrics", {})
                    tweets.append({
                        "preview": t.get("text", "")[:50],
                        "likes": pm.get("like_count", 0),
                        "retweets": pm.get("retweet_count", 0),
                        "replies": pm.get("reply_count", 0),
                        "impressions": pm.get("impression_count", 0),
                    })
                if tweets:
                    result["recent_tweets"] = tweets
    except Exception as e:
        logger.warning(f"Twitter stats error: {e}")
    return result


def _fetch_linkedin_stats(token: str) -> Dict[str, Any]:
    """Fetch LinkedIn profile stats. Company-page analytics require Marketing API partnership."""
    import httpx
    result: Dict[str, Any] = {}
    headers = {"Authorization": f"Bearer {token}", "X-Restli-Protocol-Version": "2.0.0"}
    try:
        # Personal profile — works with openid+profile scope
        profile_r = httpx.get(
            "https://api.linkedin.com/v2/userinfo",
            headers={"Authorization": f"Bearer {token}"},
            timeout=8,
        )
        if profile_r.status_code == 200:
            p = profile_r.json()
            name = p.get("name") or f"{p.get('given_name','')} {p.get('family_name','')}".strip()
            result["profile_name"] = name
        else:
            # Fallback to v2/me
            me_r = httpx.get(
                "https://api.linkedin.com/v2/me",
                params={"projection": "(id,localizedFirstName,localizedLastName)"},
                headers=headers,
                timeout=8,
            )
            if me_r.status_code == 200:
                p = me_r.json()
                name = f"{p.get('localizedFirstName','')} {p.get('localizedLastName','')}".strip()
                result["profile_name"] = name

        # Company page analytics require r_organization_social (LinkedIn Marketing API partner only)
        # Try it — return gracefully if 403
        orgs_r = httpx.get(
            "https://api.linkedin.com/v2/organizationAcls",
            params={"q": "roleAssignee", "role": "ADMINISTRATOR",
                    "projection": "(elements*(organization~(localizedName,id)))"},
            headers=headers,
            timeout=8,
        )
        if orgs_r.status_code == 200:
            elements = orgs_r.json().get("elements", [])
            if elements:
                org = elements[0].get("organization~", {})
                org_id_url = elements[0].get("organization", "")
                org_id = org_id_url.split(":")[-1] if ":" in org_id_url else org_id_url
                result["company_page"] = org.get("localizedName", "")
                if org_id:
                    size_r = httpx.get(
                        f"https://api.linkedin.com/v2/networkSizes/urn:li:organization:{org_id}",
                        params={"edgeType": "CompanyFollowedByMember"},
                        headers=headers,
                        timeout=8,
                    )
                    if size_r.status_code == 200:
                        result["page_followers"] = size_r.json().get("firstDegreeSize", 0)
        # 403 = no company page or no Marketing API access — just skip, don't report error

    except Exception as e:
        logger.warning(f"LinkedIn stats error: {e}")
    return result




async def get_campaign_performance(
    campaign_id: Optional[str] = None,
    platforms: Optional[List[str]] = None,
    days: int = 30,
    session_id: str = "",
) -> Dict[str, Any]:
    """
    Get overall campaign performance metrics across platforms.
    Only shows actually-connected (non-demo) platforms.
    """
    # Only work with platforms that have real tokens
    connected = {
        name: p for name, p in _platform_registry.items()
        if not getattr(p, "demo_mode", True)
    }

    if platforms:
        connected = {k: v for k, v in connected.items() if k in platforms}

    if not connected:
        return {
            "error": "no_connected_platforms",
            "message": "לא נמצאו פלטפורמות מחוברות עם טוקן אמיתי. וודא שחיברת את הפלטפורמות דרך הפאנל.",
            "period_days": days,
            "platforms": {},
        }

    # Count real published posts from our own tracking
    post_counts = _real_post_counts(session_id, days) if session_id else {}

    results: Dict[str, Any] = {}
    for platform_name, p in connected.items():
        entry: Dict[str, Any] = {
            "connected": True,
            "posts_tracked": post_counts.get(platform_name, 0),
            "note": "נתוני engagement (חשיפות, לייקים) זמינים ישירות בפלטפורמה",
        }
        # Fetch any real stats we can get from the API
        real = _fetch_real_stats(platform_name, p)
        entry.update(real)
        results[platform_name] = entry

    not_connected = [
        name for name, p in _platform_registry.items()
        if getattr(p, "demo_mode", True)
    ]

    return {
        "campaign_id": campaign_id,
        "period_days": days,
        "connected_platforms": list(connected.keys()),
        "not_connected_platforms": not_connected,
        "platforms": results,
        "total_posts_tracked": sum(post_counts.values()),
        "data_note": (
            "נתוני posts_tracked מגיעים מהמעקב הפנימי שלנו. "
            "נתוני חשיפה/מעורבות מדויקים זמינים ב: "
            "Facebook → Business Manager, YouTube → Studio Analytics, "
            "Twitter → Analytics, LinkedIn → Company Page Analytics."
        ),
    }



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
