"""
Facebook platform integration using Meta Graph API.
API Docs: https://developers.facebook.com/docs/graph-api
"""
from __future__ import annotations
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any

from config import config
from models.platform import PlatformAccount, SocialPost, DiscoveredUser, DiscoveredGroup, PlatformMetrics
from platforms.base import BasePlatform

logger = logging.getLogger(__name__)


class FacebookPlatform(BasePlatform):
    """Facebook integration via Meta Graph API."""

    platform_name = "facebook"
    BASE_URL = "https://graph.facebook.com/v18.0"

    def __init__(self):
        super().__init__(
            access_token=config.FACEBOOK_ACCESS_TOKEN,
            demo_mode=config.DEMO_MODE,
        )
        self.page_id = config.FACEBOOK_PAGE_ID
        self.app_id = config.FACEBOOK_APP_ID

    def _get_default_headers(self) -> Dict[str, str]:
        return {
            "Content-Type": "application/json",
            "User-Agent": "AIAdvertisingAgent/1.0",
        }

    def _auth_params(self) -> Dict[str, str]:
        return {"access_token": self.access_token}

    async def connect(self) -> PlatformAccount:
        """Connect to Facebook and return page account info."""
        if self.demo_mode:
            return self._demo_account()
        url = f"{self.BASE_URL}/{self.page_id}"
        params = {**self._auth_params(), "fields": "id,name,about,fan_count,followers_count"}
        data = await self._request("GET", url, params=params)
        return PlatformAccount(
            platform="facebook",
            account_id=data.get("id", self.page_id),
            username=data.get("name", ""),
            bio=data.get("about", ""),
            followers_count=data.get("followers_count", 0),
            is_connected=True,
            is_business_account=True,
            connected_at=datetime.now(),
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
        """Post to a Facebook page or group."""
        post_target = target_id or self.page_id
        if self.demo_mode:
            return SocialPost(
                platform="facebook",
                platform_post_id=f"demo_fb_{datetime.now().timestamp():.0f}",
                content=text,
                media_urls=media_urls or [],
                post_url=f"https://facebook.com/demo_post",
                posted_at=datetime.now(),
            )
        url = f"{self.BASE_URL}/{post_target}/feed"
        payload: Dict[str, Any] = {"message": text, **self._auth_params()}
        if media_urls:
            payload["link"] = media_urls[0]
        data = await self._request("POST", url, json=payload)
        return SocialPost(
            platform="facebook",
            platform_post_id=data.get("id", ""),
            content=text,
            media_urls=media_urls or [],
            post_url=f"https://facebook.com/{data.get('id', '')}",
            posted_at=datetime.now(),
        )

    async def post_to_group(self, group_id: str, text: str, media_urls: List[str] = None) -> SocialPost:
        """Post content to a specific Facebook group."""
        return await self.post_content(text, media_urls, target_id=group_id)

    async def find_relevant_groups(
        self,
        keywords: List[str],
        limit: int = 10,
    ) -> List[DiscoveredGroup]:
        """Search for Facebook groups matching the keywords."""
        if self.demo_mode:
            return [
                DiscoveredGroup(
                    platform="facebook",
                    group_id=f"demo_group_{i}",
                    name=f"קבוצת {kw} - ישראל #{i+1}",
                    description=f"קבוצה של אנשים שמתעניינים ב{kw}",
                    members_count=(5000 - i * 400),
                    posts_per_day=15,
                    topics=keywords,
                    relevance_score=0.9 - (i * 0.05),
                    is_public=True,
                )
                for i, kw in enumerate(keywords[:limit])
            ]
        url = f"{self.BASE_URL}/search"
        results = []
        for keyword in keywords[:3]:
            params = {**self._auth_params(), "q": keyword, "type": "group", "limit": limit // len(keywords)}
            data = await self._request("GET", url, params=params)
            for g in data.get("data", []):
                results.append(DiscoveredGroup(
                    platform="facebook",
                    group_id=g.get("id", ""),
                    name=g.get("name", ""),
                    description=g.get("description", ""),
                    members_count=g.get("member_count", 0),
                    topics=keywords,
                    relevance_score=0.7,
                ))
        return results[:limit]

    async def find_relevant_users(
        self,
        keywords: List[str],
        limit: int = 20,
    ) -> List[DiscoveredUser]:
        """Find Facebook users relevant to the keywords (via page interactions)."""
        if self.demo_mode:
            return [
                DiscoveredUser(
                    platform="facebook",
                    user_id=f"demo_user_{i}",
                    username=f"user_{i}_fb",
                    display_name=f"משתמש לדוגמה {i}",
                    bio=f"מתעניין ב: {', '.join(keywords[:2])}",
                    followers_count=1000 + i * 200,
                    topics=keywords,
                    relevance_score=0.85 - (i * 0.03),
                )
                for i in range(min(limit, 10))
            ]
        # Facebook doesn't allow user search - return page fans instead
        url = f"{self.BASE_URL}/{self.page_id}/fans"
        params = {**self._auth_params(), "limit": limit, "fields": "id,name,about"}
        data = await self._request("GET", url, params=params)
        return [
            DiscoveredUser(
                platform="facebook",
                user_id=u.get("id", ""),
                username=u.get("name", ""),
                display_name=u.get("name", ""),
                bio=u.get("about", ""),
                topics=keywords,
                relevance_score=0.6,
            )
            for u in data.get("data", [])
        ]

    async def follow_user(self, user_id: str) -> bool:
        """Like a Facebook page (follow equivalent)."""
        if self.demo_mode:
            logger.info(f"[DEMO] Followed Facebook user/page {user_id}")
            return True
        url = f"{self.BASE_URL}/{user_id}/likes"
        data = await self._request("POST", url, params=self._auth_params())
        return data.get("success", False)

    async def comment_on_post(self, post_id: str, comment: str) -> bool:
        """Comment on a Facebook post."""
        if self.demo_mode:
            logger.info(f"[DEMO] Commented on Facebook post {post_id}: {comment[:50]}...")
            return True
        url = f"{self.BASE_URL}/{post_id}/comments"
        payload = {"message": comment, **self._auth_params()}
        data = await self._request("POST", url, json=payload)
        return bool(data.get("id"))

    async def like_post(self, post_id: str) -> bool:
        """Like a Facebook post."""
        if self.demo_mode:
            logger.info(f"[DEMO] Liked Facebook post {post_id}")
            return True
        url = f"{self.BASE_URL}/{post_id}/likes"
        data = await self._request("POST", url, params=self._auth_params())
        return data.get("success", False)

    async def get_feed(self, limit: int = 20) -> List[SocialPost]:
        """Get the Facebook page feed."""
        if self.demo_mode:
            return [
                SocialPost(
                    platform="facebook",
                    platform_post_id=f"demo_feed_{i}",
                    content=f"פוסט לדוגמה #{i+1} מהפיד",
                    likes_count=50 + i * 10,
                    comments_count=5 + i,
                    posted_at=datetime.now(),
                )
                for i in range(min(limit, 5))
            ]
        url = f"{self.BASE_URL}/{self.page_id}/feed"
        params = {**self._auth_params(), "limit": limit, "fields": "id,message,likes.summary(true),comments.summary(true),created_time"}
        data = await self._request("GET", url, params=params)
        return [
            SocialPost(
                platform="facebook",
                platform_post_id=p.get("id", ""),
                content=p.get("message", ""),
                likes_count=p.get("likes", {}).get("summary", {}).get("total_count", 0),
                comments_count=p.get("comments", {}).get("summary", {}).get("total_count", 0),
                posted_at=datetime.fromisoformat(p.get("created_time", "").replace("Z", "+00:00")) if p.get("created_time") else None,
            )
            for p in data.get("data", [])
        ]

    async def get_metrics(self, days: int = 30) -> PlatformMetrics:
        """Get Facebook page insights."""
        if self.demo_mode:
            return PlatformMetrics(
                platform="facebook",
                period_days=days,
                followers_gained=150,
                posts_published=30,
                total_reach=45000,
                total_impressions=120000,
                total_likes=2800,
                total_comments=340,
                total_shares=180,
                engagement_rate=4.2,
                best_posting_times=["09:00", "12:00", "18:00"],
            )
        url = f"{self.BASE_URL}/{self.page_id}/insights"
        params = {**self._auth_params(), "metric": "page_fans,page_impressions,page_reach", "period": "month"}
        data = await self._request("GET", url, params=params)
        return PlatformMetrics(platform="facebook", period_days=days)

    async def get_page_insights(self) -> Dict[str, Any]:
        """Get detailed page insights."""
        metrics = await self.get_metrics()
        return metrics.model_dump()

    def _demo_account(self) -> PlatformAccount:
        return PlatformAccount(
            platform="facebook",
            account_id="demo_page_123",
            username="my_business_page",
            display_name="העסק שלי",
            bio="עמוד העסק שלנו",
            followers_count=1500,
            following_count=0,
            posts_count=120,
            is_connected=True,
            is_business_account=True,
            connected_at=datetime.now(),
        )
