"""
Twitter / X platform integration using Twitter API v2.
API Docs: https://developer.twitter.com/en/docs/twitter-api
"""
from __future__ import annotations
import logging
from datetime import datetime
from typing import List, Dict, Any

from config import config
from models.platform import PlatformAccount, SocialPost, DiscoveredUser, DiscoveredGroup, PlatformMetrics
from platforms.base import BasePlatform

logger = logging.getLogger(__name__)


class TwitterPlatform(BasePlatform):
    """Twitter / X integration via Twitter API v2."""

    platform_name = "twitter"
    BASE_URL = "https://api.twitter.com/2"

    def __init__(self):
        super().__init__(
            access_token=config.TWITTER_BEARER_TOKEN,
            demo_mode=config.DEMO_MODE,
        )
        self.api_key = config.TWITTER_API_KEY
        self.api_secret = config.TWITTER_API_SECRET
        self.user_access_token = config.TWITTER_ACCESS_TOKEN
        self.user_access_secret = config.TWITTER_ACCESS_SECRET
        self._user_id: str = ""

    def _get_default_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

    def _user_auth_headers(self) -> Dict[str, str]:
        """OAuth 1.0a headers for user-context endpoints."""
        # In production, implement OAuth 1.0a signing here
        return {
            "Authorization": f"OAuth oauth_token=\"{self.user_access_token}\"",
            "Content-Type": "application/json",
        }

    async def connect(self) -> PlatformAccount:
        if self.demo_mode:
            return self._demo_account()
        url = f"{self.BASE_URL}/users/me"
        params = {"user.fields": "id,name,username,description,public_metrics"}
        data = await self._request("GET", url, params=params)
        user = data.get("data", {})
        metrics = user.get("public_metrics", {})
        self._user_id = user.get("id", "")
        return PlatformAccount(
            platform="twitter",
            account_id=user.get("id", ""),
            username=user.get("username", ""),
            display_name=user.get("name", ""),
            bio=user.get("description", ""),
            followers_count=metrics.get("followers_count", 0),
            following_count=metrics.get("following_count", 0),
            posts_count=metrics.get("tweet_count", 0),
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
        """Post a tweet."""
        if self.demo_mode:
            return SocialPost(
                platform="twitter",
                platform_post_id=f"demo_tw_{datetime.now().timestamp():.0f}",
                content=text,
                media_urls=media_urls or [],
                post_url="https://x.com/i/status/demo",
                posted_at=datetime.now(),
            )
        url = f"{self.BASE_URL}/tweets"
        payload: Dict[str, Any] = {"text": text[:280]}  # Twitter char limit
        if target_id:
            payload["reply"] = {"in_reply_to_tweet_id": target_id}
        data = await self._request("POST", url, json=payload, headers=self._user_auth_headers())
        tweet = data.get("data", {})
        return SocialPost(
            platform="twitter",
            platform_post_id=tweet.get("id", ""),
            content=text,
            post_url=f"https://x.com/i/status/{tweet.get('id', '')}",
            posted_at=datetime.now(),
        )

    async def reply_to_tweet(self, tweet_id: str, text: str) -> SocialPost:
        """Reply to a tweet."""
        return await self.post_content(text, target_id=tweet_id)

    async def find_relevant_users(
        self,
        keywords: List[str],
        limit: int = 20,
    ) -> List[DiscoveredUser]:
        """Find Twitter users who tweet about relevant topics."""
        if self.demo_mode:
            return [
                DiscoveredUser(
                    platform="twitter",
                    user_id=f"demo_tw_user_{i}",
                    username=f"twitter_user_{i}",
                    display_name=f"משתמש טוויטר {i+1}",
                    bio=f"Tweeting about {', '.join(keywords[:2])} | {i*100}K followers",
                    followers_count=5000 + i * 1500,
                    topics=keywords,
                    relevance_score=0.82 - (i * 0.03),
                )
                for i in range(min(limit, 10))
            ]
        results = []
        for keyword in keywords[:2]:
            url = f"{self.BASE_URL}/tweets/search/recent"
            params = {
                "query": f"{keyword} lang:iw OR lang:he OR lang:en",
                "tweet.fields": "author_id",
                "user.fields": "id,name,username,description,public_metrics",
                "expansions": "author_id",
                "max_results": 10,
            }
            data = await self._request("GET", url, params=params)
            for user in data.get("includes", {}).get("users", []):
                metrics = user.get("public_metrics", {})
                results.append(DiscoveredUser(
                    platform="twitter",
                    user_id=user.get("id", ""),
                    username=user.get("username", ""),
                    display_name=user.get("name", ""),
                    bio=user.get("description", ""),
                    followers_count=metrics.get("followers_count", 0),
                    following_count=metrics.get("following_count", 0),
                    topics=keywords,
                    relevance_score=0.65,
                ))
        return results[:limit]

    async def find_relevant_groups(
        self,
        keywords: List[str],
        limit: int = 10,
    ) -> List[DiscoveredGroup]:
        """Twitter doesn't have groups - return trending hashtags as communities."""
        if self.demo_mode:
            return [
                DiscoveredGroup(
                    platform="twitter",
                    group_id=f"#{kw.replace(' ', '')}",
                    name=f"#{kw.replace(' ', '')}",
                    description=f"טרנד טוויטר - {kw}",
                    members_count=50000 + i * 10000,
                    posts_per_day=500,
                    topics=[kw],
                    relevance_score=0.75 - (i * 0.05),
                )
                for i, kw in enumerate(keywords[:limit])
            ]
        return [
            DiscoveredGroup(
                platform="twitter",
                group_id=f"#{kw.replace(' ', '')}",
                name=f"#{kw.replace(' ', '')}",
                description=f"Twitter hashtag: {kw}",
                topics=[kw],
                relevance_score=0.65,
            )
            for kw in keywords[:limit]
        ]

    async def follow_user(self, user_id: str) -> bool:
        """Follow a Twitter user."""
        if self.demo_mode:
            logger.info(f"[DEMO] Followed Twitter user {user_id}")
            return True
        if not self._user_id:
            await self.connect()
        url = f"{self.BASE_URL}/users/{self._user_id}/following"
        payload = {"target_user_id": user_id}
        data = await self._request("POST", url, json=payload, headers=self._user_auth_headers())
        return data.get("data", {}).get("following", False)

    async def comment_on_post(self, post_id: str, comment: str) -> bool:
        """Reply to a tweet."""
        result = await self.reply_to_tweet(post_id, comment)
        return bool(result.platform_post_id)

    async def like_post(self, post_id: str) -> bool:
        """Like a tweet."""
        if self.demo_mode:
            logger.info(f"[DEMO] Liked tweet {post_id}")
            return True
        if not self._user_id:
            await self.connect()
        url = f"{self.BASE_URL}/users/{self._user_id}/likes"
        payload = {"tweet_id": post_id}
        data = await self._request("POST", url, json=payload, headers=self._user_auth_headers())
        return data.get("data", {}).get("liked", False)

    async def get_feed(self, limit: int = 20) -> List[SocialPost]:
        """Get the home timeline."""
        if self.demo_mode:
            return [
                SocialPost(
                    platform="twitter",
                    platform_post_id=f"demo_tw_feed_{i}",
                    content=f"ציוץ לדוגמה #{i+1} #ישראל #טכנולוגיה",
                    likes_count=30 + i * 8,
                    comments_count=3 + i,
                    posted_at=datetime.now(),
                )
                for i in range(min(limit, 5))
            ]
        if not self._user_id:
            await self.connect()
        url = f"{self.BASE_URL}/users/{self._user_id}/timelines/reverse_chronological"
        params = {"max_results": min(limit, 100), "tweet.fields": "public_metrics,created_at"}
        data = await self._request("GET", url, params=params)
        return [
            SocialPost(
                platform="twitter",
                platform_post_id=t.get("id", ""),
                content=t.get("text", ""),
                likes_count=t.get("public_metrics", {}).get("like_count", 0),
                comments_count=t.get("public_metrics", {}).get("reply_count", 0),
                shares_count=t.get("public_metrics", {}).get("retweet_count", 0),
            )
            for t in data.get("data", [])
        ]

    async def get_metrics(self, days: int = 30) -> PlatformMetrics:
        if self.demo_mode:
            return PlatformMetrics(
                platform="twitter",
                period_days=days,
                followers_gained=85,
                posts_published=60,
                total_impressions=25000,
                total_likes=1200,
                total_comments=180,
                total_shares=320,
                engagement_rate=3.1,
                best_posting_times=["08:00", "13:00", "17:00", "20:00"],
            )
        return PlatformMetrics(platform="twitter", period_days=days)

    def _demo_account(self) -> PlatformAccount:
        return PlatformAccount(
            platform="twitter",
            account_id="demo_tw_123",
            username="my_business_tw",
            display_name="העסק שלי 🚀",
            bio="🇮🇱 עסק ישראלי | פתרונות חכמים | RT ≠ אישור",
            followers_count=2100,
            following_count=890,
            posts_count=450,
            is_connected=True,
        )
