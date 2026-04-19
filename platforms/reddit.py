"""
Reddit platform integration.
API Docs: https://www.reddit.com/dev/api
"""
from __future__ import annotations
import logging
from datetime import datetime
from typing import List, Dict, Any

from config import config
from models.platform import PlatformAccount, SocialPost, DiscoveredUser, DiscoveredGroup, PlatformMetrics
from platforms.base import BasePlatform

logger = logging.getLogger(__name__)


class RedditPlatform(BasePlatform):
    """Reddit integration via Reddit OAuth2 API."""

    platform_name = "reddit"
    BASE_URL = "https://oauth.reddit.com"

    def __init__(self, access_token: str = ""):
        token = access_token or getattr(config, 'REDDIT_ACCESS_TOKEN', '')
        super().__init__(
            access_token=token,
            demo_mode=False if access_token else config.DEMO_MODE,
        )
        self._username: str = ""

    def _get_default_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "User-Agent": "ilmariai-advertising-agent/1.0",
        }

    async def connect(self) -> PlatformAccount:
        if self.demo_mode:
            return self._demo_account()
        url = f"{self.BASE_URL}/api/v1/me"
        data = await self._request("GET", url)
        self._username = data.get("name", "")
        return PlatformAccount(
            platform="reddit",
            account_id=str(data.get("id", "")),
            username=self._username,
            display_name=self._username,
            followers_count=data.get("total_karma", 0),
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
        """Submit a self (text) post to a subreddit."""
        if self.demo_mode:
            return SocialPost(
                platform="reddit",
                platform_post_id=f"demo_reddit_{datetime.now().timestamp():.0f}",
                content=text,
                post_url="https://reddit.com/r/test/comments/demo",
                posted_at=datetime.now(),
            )
        subreddit = target_id or kwargs.get("subreddit", "test")
        title = kwargs.get("title") or text[:300]
        url = f"{self.BASE_URL}/api/submit"
        payload = {
            "sr": subreddit,
            "kind": "self",
            "title": title,
            "text": text,
            "api_type": "json",
            "resubmit": True,
        }
        data = await self._request("POST", url, json=payload)
        post_data = data.get("json", {}).get("data", {})
        return SocialPost(
            platform="reddit",
            platform_post_id=post_data.get("id", ""),
            content=text,
            post_url=post_data.get("url", ""),
            posted_at=datetime.now(),
        )

    async def find_relevant_users(self, keywords: List[str], limit: int = 20) -> List[DiscoveredUser]:
        if self.demo_mode:
            return [
                DiscoveredUser(
                    platform="reddit",
                    user_id=f"demo_reddit_user_{i}",
                    username=f"u/reddit_user_{i}",
                    display_name=f"Reddit User {i+1}",
                    bio=f"Active in r/{keywords[0] if keywords else 'business'} | {(i+1)*500} karma",
                    followers_count=(i + 1) * 500,
                    topics=keywords,
                    relevance_score=0.78 - (i * 0.04),
                )
                for i in range(min(limit, 8))
            ]
        return []

    async def find_relevant_groups(self, keywords: List[str], limit: int = 10) -> List[DiscoveredGroup]:
        if self.demo_mode:
            return [
                DiscoveredGroup(
                    platform="reddit",
                    group_id=f"r/{kw.replace(' ', '')}",
                    name=f"r/{kw.replace(' ', '')}",
                    description=f"Reddit community for {kw}",
                    members_count=50000 + i * 10000,
                    posts_per_day=50,
                    topics=[kw],
                    relevance_score=0.72 - (i * 0.05),
                )
                for i, kw in enumerate(keywords[:limit])
            ]
        results = []
        for kw in keywords[:limit]:
            url = f"{self.BASE_URL}/subreddits/search"
            params = {"q": kw, "limit": 5, "type": "sr"}
            try:
                data = await self._request("GET", url, params=params)
                for sr in data.get("data", {}).get("children", []):
                    d = sr.get("data", {})
                    results.append(DiscoveredGroup(
                        platform="reddit",
                        group_id=d.get("name", ""),
                        name=d.get("display_name_prefixed", ""),
                        description=d.get("public_description", ""),
                        members_count=d.get("subscribers", 0),
                        topics=[kw],
                        relevance_score=0.65,
                    ))
            except Exception:
                pass
        return results[:limit]

    async def follow_user(self, user_id: str) -> bool:
        if self.demo_mode:
            logger.info(f"[DEMO] Followed Reddit user {user_id}")
            return True
        return False

    async def comment_on_post(self, post_id: str, comment: str) -> bool:
        if self.demo_mode:
            logger.info(f"[DEMO] Commented on Reddit post {post_id}")
            return True
        url = f"{self.BASE_URL}/api/comment"
        payload = {"thing_id": post_id, "text": comment, "api_type": "json"}
        data = await self._request("POST", url, json=payload)
        return bool(data.get("json", {}).get("data", {}).get("things"))

    async def like_post(self, post_id: str) -> bool:
        if self.demo_mode:
            logger.info(f"[DEMO] Upvoted Reddit post {post_id}")
            return True
        url = f"{self.BASE_URL}/api/vote"
        payload = {"id": post_id, "dir": 1}
        await self._request("POST", url, json=payload)
        return True

    async def get_feed(self, limit: int = 20) -> List[SocialPost]:
        if self.demo_mode:
            return [
                SocialPost(
                    platform="reddit",
                    platform_post_id=f"demo_reddit_feed_{i}",
                    content=f"Reddit post #{i+1} — trending discussion",
                    likes_count=100 + i * 50,
                    comments_count=20 + i * 5,
                    posted_at=datetime.now(),
                )
                for i in range(min(limit, 5))
            ]
        return []

    async def get_metrics(self, days: int = 30) -> PlatformMetrics:
        if self.demo_mode:
            return PlatformMetrics(
                platform="reddit",
                period_days=days,
                followers_gained=45,
                posts_published=12,
                total_reach=8000,
                total_likes=320,
                total_comments=85,
                engagement_rate=4.2,
                best_posting_times=["09:00", "12:00", "17:00", "21:00"],
            )
        return PlatformMetrics(platform="reddit", period_days=days)

    def _demo_account(self) -> PlatformAccount:
        return PlatformAccount(
            platform="reddit",
            account_id="demo_reddit_123",
            username="ilmariai_bot",
            display_name="ilmariai_bot",
            bio="AI-powered advertising bot | karma: 1,200",
            followers_count=1200,
            is_connected=True,
        )
