"""
LinkedIn platform integration.
API Docs: https://learn.microsoft.com/en-us/linkedin/
"""
from __future__ import annotations
import logging
from datetime import datetime
from typing import List, Dict, Any

from config import config
from models.platform import PlatformAccount, SocialPost, DiscoveredUser, DiscoveredGroup, PlatformMetrics
from platforms.base import BasePlatform

logger = logging.getLogger(__name__)


class LinkedInPlatform(BasePlatform):
    """LinkedIn integration via LinkedIn API."""

    platform_name = "linkedin"
    BASE_URL = "https://api.linkedin.com/v2"

    def __init__(self, access_token: str = ""):
        token = access_token or config.LINKEDIN_ACCESS_TOKEN
        super().__init__(
            access_token=token,
            demo_mode=False if access_token else config.DEMO_MODE,
        )
        self._person_urn: str = ""

    def _get_default_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0",
        }

    async def connect(self) -> PlatformAccount:
        if self.demo_mode:
            return self._demo_account()
        # OpenID Connect userinfo endpoint (works with openid+profile scopes)
        url = "https://api.linkedin.com/v2/userinfo"
        data = await self._request("GET", url)
        user_id = data.get("sub", "")
        self._person_urn = f"urn:li:person:{user_id}"
        name = data.get("name") or f"{data.get('given_name', '')} {data.get('family_name', '')}".strip()
        return PlatformAccount(
            platform="linkedin",
            account_id=user_id,
            username=name,
            display_name=name,
            followers_count=0,
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
        """Post an update to LinkedIn (personal or company page)."""
        if self.demo_mode:
            return SocialPost(
                platform="linkedin",
                platform_post_id=f"demo_li_{datetime.now().timestamp():.0f}",
                content=text,
                post_url="https://linkedin.com/feed/update/demo",
                posted_at=datetime.now(),
            )
        if not self._person_urn:
            await self.connect()
        author = target_id or self._person_urn
        url = f"{self.BASE_URL}/ugcPosts"
        payload = {
            "author": author,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": text},
                    "shareMediaCategory": "NONE",
                }
            },
            "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
        }
        data = await self._request("POST", url, json=payload)
        return SocialPost(
            platform="linkedin",
            platform_post_id=data.get("id", ""),
            content=text,
            posted_at=datetime.now(),
        )

    async def find_relevant_users(
        self,
        keywords: List[str],
        limit: int = 20,
    ) -> List[DiscoveredUser]:
        """Find LinkedIn professionals by keywords."""
        if self.demo_mode:
            job_titles = ["מנהל שיווק", "יזם", "מפתח", "מנכ\"ל", "מנהל מכירות"]
            return [
                DiscoveredUser(
                    platform="linkedin",
                    user_id=f"demo_li_user_{i}",
                    username=f"professional_{i}",
                    display_name=f"איש מקצוע {i+1}",
                    bio=f"{job_titles[i % len(job_titles)]} | מתמחה ב{keywords[0] if keywords else 'עסקים'}",
                    followers_count=500 + i * 100,
                    topics=keywords,
                    relevance_score=0.85 - (i * 0.03),
                    location="ישראל",
                )
                for i in range(min(limit, 10))
            ]
        url = f"{self.BASE_URL}/search/blended"
        params = {"keywords": " ".join(keywords), "filters": "List((name:resultType,values:List((value:PEOPLE,selectionType:INCLUDED))))", "count": limit}
        data = await self._request("GET", url, params=params)
        return [
            DiscoveredUser(
                platform="linkedin",
                user_id=p.get("trackingUrn", "").split(":")[-1],
                username=p.get("title", {}).get("text", ""),
                display_name=p.get("title", {}).get("text", ""),
                bio=p.get("primarySubtitle", {}).get("text", ""),
                topics=keywords,
                relevance_score=0.7,
            )
            for p in data.get("elements", [])
        ]

    async def find_relevant_groups(
        self,
        keywords: List[str],
        limit: int = 10,
    ) -> List[DiscoveredGroup]:
        """Find LinkedIn groups related to keywords."""
        if self.demo_mode:
            return [
                DiscoveredGroup(
                    platform="linkedin",
                    group_id=f"demo_li_group_{i}",
                    name=f"קבוצת {kw} - מקצוענים ישראליים",
                    description=f"קבוצה מקצועית לאנשי {kw} בישראל",
                    members_count=3000 + i * 500,
                    posts_per_day=8,
                    topics=[kw],
                    relevance_score=0.78 - (i * 0.05),
                )
                for i, kw in enumerate(keywords[:limit])
            ]
        url = f"{self.BASE_URL}/search/blended"
        params = {"keywords": " ".join(keywords), "filters": "List((name:resultType,values:List((value:GROUPS,selectionType:INCLUDED))))", "count": limit}
        data = await self._request("GET", url, params=params)
        return [
            DiscoveredGroup(
                platform="linkedin",
                group_id=g.get("trackingUrn", "").split(":")[-1],
                name=g.get("title", {}).get("text", ""),
                description=g.get("primarySubtitle", {}).get("text", ""),
                topics=keywords,
                relevance_score=0.65,
            )
            for g in data.get("elements", [])
        ]

    async def follow_user(self, user_id: str) -> bool:
        """Send a LinkedIn connection request."""
        if self.demo_mode:
            logger.info(f"[DEMO] Sent LinkedIn connection request to {user_id}")
            return True
        if not self._person_urn:
            await self.connect()
        url = f"{self.BASE_URL}/socialActions/{self._person_urn}/follows"
        payload = {"followee": {"com.linkedin.common.UrnFollowee": {"urn": f"urn:li:person:{user_id}"}}}
        data = await self._request("POST", url, json=payload)
        return bool(data)

    async def comment_on_post(self, post_id: str, comment: str) -> bool:
        """Comment on a LinkedIn post."""
        if self.demo_mode:
            logger.info(f"[DEMO] Commented on LinkedIn post {post_id}")
            return True
        if not self._person_urn:
            await self.connect()
        url = f"{self.BASE_URL}/socialActions/{post_id}/comments"
        payload = {
            "actor": self._person_urn,
            "message": {"text": comment},
        }
        data = await self._request("POST", url, json=payload)
        return bool(data.get("id"))

    async def like_post(self, post_id: str) -> bool:
        """Like a LinkedIn post."""
        if self.demo_mode:
            logger.info(f"[DEMO] Liked LinkedIn post {post_id}")
            return True
        if not self._person_urn:
            await self.connect()
        url = f"{self.BASE_URL}/socialActions/{post_id}/likes"
        payload = {"actor": self._person_urn}
        data = await self._request("POST", url, json=payload)
        return bool(data)

    async def get_feed(self, limit: int = 20) -> List[SocialPost]:
        if self.demo_mode:
            return [
                SocialPost(
                    platform="linkedin",
                    platform_post_id=f"demo_li_feed_{i}",
                    content=f"עדכון לינקדאין #{i+1} - תובנות מקצועיות",
                    likes_count=45 + i * 12,
                    comments_count=8 + i * 2,
                    posted_at=datetime.now(),
                )
                for i in range(min(limit, 5))
            ]
        return []

    async def get_metrics(self, days: int = 30) -> PlatformMetrics:
        if self.demo_mode:
            return PlatformMetrics(
                platform="linkedin",
                period_days=days,
                followers_gained=120,
                posts_published=15,
                total_reach=18000,
                total_impressions=35000,
                total_likes=680,
                total_comments=95,
                engagement_rate=3.8,
                best_posting_times=["08:00", "10:00", "12:00", "17:00"],
            )
        return PlatformMetrics(platform="linkedin", period_days=days)

    def _demo_account(self) -> PlatformAccount:
        return PlatformAccount(
            platform="linkedin",
            account_id="demo_li_123",
            username="my-business-profile",
            display_name="העסק שלי",
            bio="מומחה בתחום | ישראל | LinkedIn Top Voice",
            followers_count=890,
            following_count=400,
            is_connected=True,
            is_business_account=True,
        )
