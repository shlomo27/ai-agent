"""
TikTok platform integration using TikTok for Developers API.
API Docs: https://developers.tiktok.com/
"""
from __future__ import annotations
import logging
from datetime import datetime
from typing import List, Dict, Any

from config import config
from models.platform import PlatformAccount, SocialPost, DiscoveredUser, DiscoveredGroup, PlatformMetrics
from platforms.base import BasePlatform

logger = logging.getLogger(__name__)


class TikTokPlatform(BasePlatform):
    """TikTok integration via TikTok for Developers API."""

    platform_name = "tiktok"
    BASE_URL = "https://open.tiktokapis.com/v2"

    def __init__(self, access_token: str = ""):
        token = access_token or config.TIKTOK_ACCESS_TOKEN
        super().__init__(
            access_token=token,
            demo_mode=False if access_token else config.DEMO_MODE,
        )
        self.client_key = config.TIKTOK_CLIENT_KEY
        self._user_open_id: str = ""

    def _get_default_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json; charset=UTF-8",
        }

    async def connect(self) -> PlatformAccount:
        if self.demo_mode:
            return self._demo_account()
        url = f"{self.BASE_URL}/user/info/"
        payload = {"fields": ["open_id", "display_name", "bio_description", "follower_count", "following_count", "video_count"]}
        data = await self._request("POST", url, json=payload)
        user = data.get("data", {}).get("user", {})
        self._user_open_id = user.get("open_id", "")
        return PlatformAccount(
            platform="tiktok",
            account_id=self._user_open_id,
            username=user.get("display_name", ""),
            display_name=user.get("display_name", ""),
            bio=user.get("bio_description", ""),
            followers_count=user.get("follower_count", 0),
            following_count=user.get("following_count", 0),
            posts_count=user.get("video_count", 0),
            is_connected=True,
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
        """Upload a TikTok video."""
        if self.demo_mode:
            return SocialPost(
                platform="tiktok",
                platform_post_id=f"demo_tt_{datetime.now().timestamp():.0f}",
                content=text,
                media_urls=media_urls or [],
                post_url="https://tiktok.com/@user/video/demo",
                posted_at=datetime.now(),
            )
        # TikTok requires video upload via chunked upload API
        logger.info("TikTok video upload requires chunked upload API - see developers.tiktok.com")
        return SocialPost(platform="tiktok", content=text, posted_at=datetime.now())

    async def find_relevant_users(
        self,
        keywords: List[str],
        limit: int = 20,
    ) -> List[DiscoveredUser]:
        """Find TikTok creators in relevant niches."""
        if self.demo_mode:
            return [
                DiscoveredUser(
                    platform="tiktok",
                    user_id=f"demo_tt_user_{i}",
                    username=f"@tiktok_creator_{i}",
                    display_name=f"יוצר TikTok #{i+1}",
                    bio=f"תוכן על {keywords[0] if keywords else 'כל הנושאים'} | {(i+1)*10}K עוקבים",
                    followers_count=(i + 1) * 10000,
                    topics=keywords,
                    relevance_score=0.81 - (i * 0.04),
                )
                for i in range(min(limit, 8))
            ]
        # TikTok API doesn't provide public user search - use video search instead
        url = f"{self.BASE_URL}/video/search/"
        results = []
        for keyword in keywords[:2]:
            payload = {
                "query": keyword,
                "count": limit // 2,
                "fields": ["author_info"],
            }
            data = await self._request("POST", url, json=payload)
            for video in data.get("data", {}).get("videos", []):
                author = video.get("author_info", {})
                results.append(DiscoveredUser(
                    platform="tiktok",
                    user_id=author.get("id", ""),
                    username=f"@{author.get('unique_id', '')}",
                    display_name=author.get("nickname", ""),
                    bio=author.get("bio_link", ""),
                    followers_count=author.get("follower_count", 0),
                    topics=keywords,
                    relevance_score=0.6,
                ))
        return results[:limit]

    async def find_relevant_groups(
        self,
        keywords: List[str],
        limit: int = 10,
    ) -> List[DiscoveredGroup]:
        """TikTok doesn't have groups - return trending hashtags."""
        if self.demo_mode:
            return [
                DiscoveredGroup(
                    platform="tiktok",
                    group_id=f"#{kw.replace(' ', '')}",
                    name=f"#{kw.replace(' ', '')}",
                    description=f"טרנד TikTok - {kw} | {(i+1)*1000000} צפיות",
                    members_count=500000 + i * 100000,
                    posts_per_day=2000,
                    topics=[kw],
                    relevance_score=0.77 - (i * 0.06),
                )
                for i, kw in enumerate(keywords[:limit])
            ]
        return [
            DiscoveredGroup(
                platform="tiktok",
                group_id=f"#{kw.replace(' ', '')}",
                name=f"#{kw.replace(' ', '')}",
                description=f"TikTok trending hashtag: {kw}",
                topics=[kw],
                relevance_score=0.65,
            )
            for kw in keywords[:limit]
        ]

    async def follow_user(self, user_id: str) -> bool:
        """Follow a TikTok user."""
        if self.demo_mode:
            logger.info(f"[DEMO] Followed TikTok user {user_id}")
            return True
        url = f"{self.BASE_URL}/user/follow/"
        payload = {"to_user_id": user_id}
        data = await self._request("POST", url, json=payload)
        return data.get("data", {}).get("followed", False)

    async def comment_on_post(self, post_id: str, comment: str) -> bool:
        """Comment on a TikTok video."""
        if self.demo_mode:
            logger.info(f"[DEMO] Commented on TikTok video {post_id}")
            return True
        url = f"{self.BASE_URL}/comment/publish/"
        payload = {"video_id": post_id, "text": comment}
        data = await self._request("POST", url, json=payload)
        return bool(data.get("data", {}).get("comment_id"))

    async def like_post(self, post_id: str) -> bool:
        """Like a TikTok video."""
        if self.demo_mode:
            logger.info(f"[DEMO] Liked TikTok video {post_id}")
            return True
        url = f"{self.BASE_URL}/video/like/"
        payload = {"video_id": post_id}
        data = await self._request("POST", url, json=payload)
        return data.get("data", {}).get("liked", False)

    async def get_feed(self, limit: int = 20) -> List[SocialPost]:
        if self.demo_mode:
            return [
                SocialPost(
                    platform="tiktok",
                    platform_post_id=f"demo_tt_feed_{i}",
                    content=f"סרטון TikTok #{i+1} | טרנד חדש 🔥 #viral",
                    views_count=50000 + i * 10000,
                    likes_count=3000 + i * 500,
                    comments_count=200 + i * 50,
                    posted_at=datetime.now(),
                )
                for i in range(min(limit, 5))
            ]
        if not self._user_open_id:
            await self.connect()
        url = f"{self.BASE_URL}/video/list/"
        payload = {
            "fields": ["id", "title", "statistics"],
            "max_count": limit,
        }
        data = await self._request("POST", url, json=payload)
        return [
            SocialPost(
                platform="tiktok",
                platform_post_id=v.get("id", ""),
                content=v.get("title", ""),
                views_count=v.get("statistics", {}).get("play_count", 0),
                likes_count=v.get("statistics", {}).get("digg_count", 0),
                comments_count=v.get("statistics", {}).get("comment_count", 0),
            )
            for v in data.get("data", {}).get("videos", [])
        ]

    async def get_metrics(self, days: int = 30) -> PlatformMetrics:
        if self.demo_mode:
            return PlatformMetrics(
                platform="tiktok",
                period_days=days,
                followers_gained=450,
                posts_published=20,
                total_reach=150000,
                total_impressions=800000,
                total_likes=35000,
                total_comments=2800,
                total_shares=5500,
                engagement_rate=8.5,
                best_posting_times=["07:00", "12:00", "19:00", "22:00"],
            )
        return PlatformMetrics(platform="tiktok", period_days=days)

    def _demo_account(self) -> PlatformAccount:
        return PlatformAccount(
            platform="tiktok",
            account_id="demo_tt_123",
            username="@my_business_tt",
            display_name="העסק שלי 🎵",
            bio="תוכן יצירתי | ישראל 🇮🇱 | Follow for updates",
            followers_count=5600,
            following_count=320,
            posts_count=65,
            is_connected=True,
        )
