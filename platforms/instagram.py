"""
Instagram platform integration using Meta Graph API.
API Docs: https://developers.facebook.com/docs/instagram-api
"""
from __future__ import annotations
import logging
from datetime import datetime
from typing import List, Dict, Any

from config import config
from models.platform import PlatformAccount, SocialPost, DiscoveredUser, DiscoveredGroup, PlatformMetrics
from platforms.base import BasePlatform

logger = logging.getLogger(__name__)


class InstagramPlatform(BasePlatform):
    """Instagram integration via Meta Graph API."""

    platform_name = "instagram"
    BASE_URL = "https://graph.instagram.com"

    def __init__(self, access_token: str = ""):
        token = access_token or config.INSTAGRAM_ACCESS_TOKEN
        super().__init__(
            access_token=token,
            demo_mode=False if access_token else config.DEMO_MODE,
        )
        self.account_id = config.INSTAGRAM_ACCOUNT_ID

    def _auth_params(self) -> Dict[str, str]:
        return {"access_token": self.access_token}

    async def connect(self) -> PlatformAccount:
        if self.demo_mode:
            return self._demo_account()
        url = f"{self.BASE_URL}/{self.account_id}"
        params = {**self._auth_params(), "fields": "id,username,biography,followers_count,follows_count,media_count"}
        data = await self._request("GET", url, params=params)
        return PlatformAccount(
            platform="instagram",
            account_id=data.get("id", ""),
            username=data.get("username", ""),
            bio=data.get("biography", ""),
            followers_count=data.get("followers_count", 0),
            following_count=data.get("follows_count", 0),
            posts_count=data.get("media_count", 0),
            is_connected=True,
            is_business_account=True,
        )

    async def get_account_info(self) -> PlatformAccount:
        return await self.connect()

    async def post_content(
        self,
        text: str,
        media_urls: List[str] = None,
        target_id: str = None,
        **kwargs,
    ) -> SocialPost:
        """Post a photo or video to Instagram."""
        if self.demo_mode:
            return SocialPost(
                platform="instagram",
                platform_post_id=f"demo_ig_{datetime.now().timestamp():.0f}",
                content=text,
                media_urls=media_urls or [],
                post_url="https://instagram.com/p/demo",
                posted_at=datetime.now(),
            )
        if not media_urls:
            logger.warning("Instagram requires media (photo/video) for posts")
            return SocialPost(platform="instagram", content=text, posted_at=datetime.now())

        # Step 1: Create media container
        url = f"https://graph.facebook.com/v18.0/{self.account_id}/media"
        payload: Dict[str, Any] = {
            "image_url": media_urls[0],
            "caption": text,
            **self._auth_params(),
        }
        container = await self._request("POST", url, json=payload)
        container_id = container.get("id", "")

        # Step 2: Publish the container
        publish_url = f"https://graph.facebook.com/v18.0/{self.account_id}/media_publish"
        publish_data = await self._request("POST", publish_url, json={"creation_id": container_id, **self._auth_params()})

        return SocialPost(
            platform="instagram",
            platform_post_id=publish_data.get("id", ""),
            content=text,
            media_urls=media_urls,
            posted_at=datetime.now(),
        )

    async def find_relevant_users(
        self,
        keywords: List[str],
        limit: int = 20,
    ) -> List[DiscoveredUser]:
        """Find Instagram users via hashtag searches."""
        if self.demo_mode:
            return [
                DiscoveredUser(
                    platform="instagram",
                    user_id=f"demo_ig_user_{i}",
                    username=f"ig_creator_{i}",
                    display_name=f"יוצר תוכן #{i+1}",
                    bio=f"תוכן על {', '.join(keywords[:2])} | מנסה לעשות שינוי",
                    followers_count=8000 + i * 500,
                    topics=keywords,
                    relevance_score=0.88 - (i * 0.04),
                )
                for i in range(min(limit, 10))
            ]
        results = []
        for keyword in keywords[:2]:
            # Search by hashtag
            hashtag_url = f"https://graph.facebook.com/v18.0/ig_hashtag_search"
            params = {**self._auth_params(), "user_id": self.account_id, "q": keyword}
            hashtag_data = await self._request("GET", hashtag_url, params=params)
            hashtag_id = hashtag_data.get("data", [{}])[0].get("id", "")
            if hashtag_id:
                posts_url = f"https://graph.facebook.com/v18.0/{hashtag_id}/recent_media"
                posts_params = {**self._auth_params(), "user_id": self.account_id, "fields": "id,owner"}
                posts_data = await self._request("GET", posts_url, params=posts_params)
                for post in posts_data.get("data", [])[:limit // 2]:
                    owner = post.get("owner", {})
                    results.append(DiscoveredUser(
                        platform="instagram",
                        user_id=owner.get("id", ""),
                        username=owner.get("username", ""),
                        topics=keywords,
                        relevance_score=0.65,
                    ))
        return results[:limit]

    async def find_relevant_groups(
        self,
        keywords: List[str],
        limit: int = 10,
    ) -> List[DiscoveredGroup]:
        """Instagram doesn't have groups - return hashtag communities instead."""
        if self.demo_mode:
            return [
                DiscoveredGroup(
                    platform="instagram",
                    group_id=f"#{''.join(kw.split())}",
                    name=f"#{kw.replace(' ', '')}",
                    description=f"האשטג פופולרי על {kw}",
                    members_count=10000 + i * 2000,
                    posts_per_day=50,
                    topics=[kw],
                    relevance_score=0.8 - (i * 0.05),
                )
                for i, kw in enumerate(keywords[:limit])
            ]
        return [
            DiscoveredGroup(
                platform="instagram",
                group_id=f"#{kw.replace(' ', '')}",
                name=f"#{kw.replace(' ', '')}",
                description=f"Instagram hashtag community for {kw}",
                topics=[kw],
                relevance_score=0.7,
            )
            for kw in keywords[:limit]
        ]

    async def follow_user(self, user_id: str) -> bool:
        if self.demo_mode:
            logger.info(f"[DEMO] Followed Instagram user {user_id}")
            return True
        # Instagram Graph API doesn't support following users programmatically for most apps
        logger.warning("Instagram API doesn't support following users via Graph API for standard apps")
        return False

    async def comment_on_post(self, post_id: str, comment: str) -> bool:
        if self.demo_mode:
            logger.info(f"[DEMO] Commented on Instagram post {post_id}")
            return True
        url = f"https://graph.facebook.com/v18.0/{post_id}/comments"
        payload = {"message": comment, **self._auth_params()}
        data = await self._request("POST", url, json=payload)
        return bool(data.get("id"))

    async def like_post(self, post_id: str) -> bool:
        if self.demo_mode:
            logger.info(f"[DEMO] Liked Instagram post {post_id}")
            return True
        # Liking is not available via Instagram Graph API for standard apps
        logger.warning("Instagram API doesn't support liking posts via Graph API for standard apps")
        return False

    async def get_feed(self, limit: int = 20) -> List[SocialPost]:
        if self.demo_mode:
            return [
                SocialPost(
                    platform="instagram",
                    platform_post_id=f"demo_ig_feed_{i}",
                    content=f"תוכן אינסטגרם #{i+1} 📸 #ישראל #עסקים",
                    likes_count=200 + i * 30,
                    comments_count=15 + i * 3,
                    posted_at=datetime.now(),
                )
                for i in range(min(limit, 5))
            ]
        url = f"{self.BASE_URL}/{self.account_id}/media"
        params = {**self._auth_params(), "limit": limit, "fields": "id,caption,like_count,comments_count,timestamp,permalink"}
        data = await self._request("GET", url, params=params)
        return [
            SocialPost(
                platform="instagram",
                platform_post_id=p.get("id", ""),
                content=p.get("caption", ""),
                likes_count=p.get("like_count", 0),
                comments_count=p.get("comments_count", 0),
                post_url=p.get("permalink", ""),
                posted_at=datetime.fromisoformat(p.get("timestamp", "").replace("Z", "+00:00")) if p.get("timestamp") else None,
            )
            for p in data.get("data", [])
        ]

    async def get_metrics(self, days: int = 30) -> PlatformMetrics:
        if self.demo_mode:
            return PlatformMetrics(
                platform="instagram",
                period_days=days,
                followers_gained=280,
                posts_published=25,
                total_reach=68000,
                total_impressions=200000,
                total_likes=8500,
                total_comments=620,
                engagement_rate=5.8,
                best_posting_times=["08:00", "12:00", "19:00", "21:00"],
            )
        url = f"https://graph.facebook.com/v18.0/{self.account_id}/insights"
        params = {**self._auth_params(), "metric": "follower_count,impressions,reach", "period": "month"}
        data = await self._request("GET", url, params=params)
        return PlatformMetrics(platform="instagram", period_days=days)

    def _demo_account(self) -> PlatformAccount:
        return PlatformAccount(
            platform="instagram",
            account_id="demo_ig_123",
            username="my_business_ig",
            display_name="העסק שלי 📸",
            bio="עסק ישראלי | 🇮🇱 | DM לשיתופי פעולה",
            followers_count=3200,
            following_count=450,
            posts_count=85,
            is_connected=True,
            is_business_account=True,
        )
