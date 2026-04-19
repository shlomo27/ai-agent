"""
YouTube platform integration using YouTube Data API v3.
API Docs: https://developers.google.com/youtube/v3
"""
from __future__ import annotations
import logging
from datetime import datetime
from typing import List, Dict, Any

from config import config
from models.platform import PlatformAccount, SocialPost, DiscoveredUser, DiscoveredGroup, PlatformMetrics
from platforms.base import BasePlatform

logger = logging.getLogger(__name__)


class YoutubePlatform(BasePlatform):
    """YouTube integration via YouTube Data API v3."""

    platform_name = "youtube"
    BASE_URL = "https://www.googleapis.com/youtube/v3"

    def __init__(self, access_token: str = ""):
        token = access_token or getattr(config, 'YOUTUBE_API_KEY', '')
        super().__init__(
            access_token=token,
            demo_mode=False if access_token else config.DEMO_MODE,
        )
        self._oauth_mode = bool(access_token)  # True when user connected via OAuth
        self._channel_id: str = ""

    def _get_default_headers(self) -> Dict[str, str]:
        if self._oauth_mode:
            return {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
            }
        return {"Content-Type": "application/json"}

    def _auth_params(self) -> Dict[str, str]:
        if self._oauth_mode:
            return {}  # OAuth uses Bearer header, not API key param
        return {"key": self.access_token}

    async def connect(self) -> PlatformAccount:
        if self.demo_mode:
            return self._demo_account()
        url = f"{self.BASE_URL}/channels"
        params = {**self._auth_params(), "part": "snippet,statistics", "mine": "true"}
        data = await self._request("GET", url, params=params)
        channel = data.get("items", [{}])[0]
        snippet = channel.get("snippet", {})
        stats = channel.get("statistics", {})
        self._channel_id = channel.get("id", "")
        return PlatformAccount(
            platform="youtube",
            account_id=self._channel_id,
            username=snippet.get("customUrl", ""),
            display_name=snippet.get("title", ""),
            bio=snippet.get("description", ""),
            followers_count=int(stats.get("subscriberCount", 0)),
            posts_count=int(stats.get("videoCount", 0)),
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
        """Upload a video or post a community update."""
        if self.demo_mode:
            return SocialPost(
                platform="youtube",
                platform_post_id=f"demo_yt_{datetime.now().timestamp():.0f}",
                content=text,
                media_urls=media_urls or [],
                post_url="https://youtube.com/watch?v=demo",
                posted_at=datetime.now(),
            )
        if media_urls:
            title = kwargs.get("title") or (text[:100] if len(text) > 100 else text)
            return await self._upload_video_from_url(media_urls[0], title, text)
        logger.info("YouTube: no media URL provided, skipping post")
        return SocialPost(platform="youtube", content=text, posted_at=datetime.now())

    async def _upload_video_from_url(self, video_url: str, title: str, description: str) -> SocialPost:
        """Download video from URL and upload to YouTube via resumable upload API."""
        import httpx as _httpx
        from config import config as _cfg

        # Fix relative URLs (e.g. /uploads/...) by prepending the known agent base URL
        if video_url.startswith("/"):
            agent_base = getattr(_cfg, "PUBLIC_API_URL", "") or "https://ai-agent-production-bf7b.up.railway.app"
            video_url = agent_base.rstrip("/") + video_url

        # Step 1: download the video file
        async with _httpx.AsyncClient(timeout=120, follow_redirects=True) as client:
            dl = await client.get(video_url)
            if dl.status_code != 200:
                raise Exception(f"Failed to download video ({dl.status_code}): {video_url}")
            video_data = dl.content
            content_type = dl.headers.get("content-type", "video/mp4").split(";")[0]

        # Step 2: initialise YouTube resumable upload session
        metadata = {
            "snippet": {
                "title": title,
                "description": description,
                "categoryId": "22",
            },
            "status": {"privacyStatus": "public"},
        }
        init_url = "https://www.googleapis.com/upload/youtube/v3/videos"
        init_headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json; charset=UTF-8",
            "X-Upload-Content-Type": content_type,
            "X-Upload-Content-Length": str(len(video_data)),
        }
        async with _httpx.AsyncClient(timeout=30) as client:
            init_resp = await client.post(
                init_url,
                params={"uploadType": "resumable", "part": "snippet,status"},
                headers=init_headers,
                json=metadata,
            )
            if init_resp.status_code != 200:
                raise Exception(f"YouTube init upload failed ({init_resp.status_code}): {init_resp.text}")
            upload_url = init_resp.headers.get("Location")
            if not upload_url:
                raise Exception("YouTube did not return an upload URL")

            # Step 3: upload the video bytes
            up_resp = await client.put(
                upload_url,
                content=video_data,
                headers={"Content-Type": content_type, "Content-Length": str(len(video_data))},
                timeout=300,
            )
            if up_resp.status_code not in (200, 201):
                raise Exception(f"YouTube upload failed ({up_resp.status_code}): {up_resp.text}")
            video_id = up_resp.json().get("id", "")

        logger.info(f"YouTube video uploaded: {video_id}")
        return SocialPost(
            platform="youtube",
            platform_post_id=video_id,
            content=description,
            post_url=f"https://youtube.com/watch?v={video_id}",
            posted_at=datetime.now(),
        )

    async def upload_video(
        self,
        video_path: str,
        title: str,
        description: str,
        tags: List[str] = None,
        category_id: str = "22",
    ) -> SocialPost:
        """Upload a video to YouTube from a local file path."""
        if self.demo_mode:
            logger.info(f"[DEMO] Uploaded video '{title}' to YouTube")
            return SocialPost(
                platform="youtube",
                platform_post_id=f"demo_yt_video_{datetime.now().timestamp():.0f}",
                content=description,
                post_url="https://youtube.com/watch?v=demoVideoId",
                views_count=0,
                posted_at=datetime.now(),
            )
        from pathlib import Path as _Path
        video_data = _Path(video_path).read_bytes()
        ext = _Path(video_path).suffix.lower()
        content_type = "video/mp4" if ext in (".mp4", ".m4v") else "video/quicktime" if ext == ".mov" else "video/webm"
        import httpx as _httpx

        metadata = {
            "snippet": {"title": title, "description": description, "categoryId": category_id},
            "status": {"privacyStatus": "public"},
        }
        init_url = "https://www.googleapis.com/upload/youtube/v3/videos"
        init_headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json; charset=UTF-8",
            "X-Upload-Content-Type": content_type,
            "X-Upload-Content-Length": str(len(video_data)),
        }
        async with _httpx.AsyncClient(timeout=30) as client:
            init_resp = await client.post(
                init_url,
                params={"uploadType": "resumable", "part": "snippet,status"},
                headers=init_headers,
                json=metadata,
            )
            if init_resp.status_code != 200:
                raise Exception(f"YouTube init upload failed: {init_resp.text}")
            upload_url = init_resp.headers.get("Location")
            up_resp = await client.put(
                upload_url,
                content=video_data,
                headers={"Content-Type": content_type, "Content-Length": str(len(video_data))},
                timeout=300,
            )
            if up_resp.status_code not in (200, 201):
                raise Exception(f"YouTube upload failed: {up_resp.text}")
            video_id = up_resp.json().get("id", "")

        return SocialPost(
            platform="youtube",
            platform_post_id=video_id,
            content=description,
            post_url=f"https://youtube.com/watch?v={video_id}",
            posted_at=datetime.now(),
        )

    async def find_relevant_users(
        self,
        keywords: List[str],
        limit: int = 20,
    ) -> List[DiscoveredUser]:
        """Find YouTube channels related to keywords."""
        if self.demo_mode:
            return [
                DiscoveredUser(
                    platform="youtube",
                    user_id=f"demo_yt_channel_{i}",
                    username=f"channel_{i}",
                    display_name=f"ערוץ יוטיוב #{i+1} - {keywords[0] if keywords else 'תוכן'}",
                    bio=f"ערוץ על {', '.join(keywords[:2])} | {(i+1)*1000} מנויים",
                    followers_count=(i + 1) * 5000,
                    topics=keywords,
                    relevance_score=0.79 - (i * 0.04),
                )
                for i in range(min(limit, 8))
            ]
        url = f"{self.BASE_URL}/search"
        results = []
        for keyword in keywords[:2]:
            params = {
                **self._auth_params(),
                "part": "snippet",
                "q": keyword,
                "type": "channel",
                "maxResults": limit // 2,
                "relevanceLanguage": "iw",
            }
            data = await self._request("GET", url, params=params)
            for item in data.get("items", []):
                snippet = item.get("snippet", {})
                channel_id = item.get("id", {}).get("channelId", "")
                results.append(DiscoveredUser(
                    platform="youtube",
                    user_id=channel_id,
                    username=snippet.get("channelTitle", ""),
                    display_name=snippet.get("channelTitle", ""),
                    bio=snippet.get("description", ""),
                    topics=keywords,
                    relevance_score=0.65,
                ))
        return results[:limit]

    async def find_relevant_groups(
        self,
        keywords: List[str],
        limit: int = 10,
    ) -> List[DiscoveredGroup]:
        """Find YouTube playlists/communities as groups."""
        if self.demo_mode:
            return [
                DiscoveredGroup(
                    platform="youtube",
                    group_id=f"demo_yt_playlist_{i}",
                    name=f"פלייליסט {kw}",
                    description=f"אוסף סרטונים על {kw}",
                    members_count=2000 + i * 500,
                    topics=[kw],
                    relevance_score=0.7 - (i * 0.05),
                )
                for i, kw in enumerate(keywords[:limit])
            ]
        url = f"{self.BASE_URL}/search"
        params = {**self._auth_params(), "part": "snippet", "q": " ".join(keywords), "type": "playlist", "maxResults": limit}
        data = await self._request("GET", url, params=params)
        return [
            DiscoveredGroup(
                platform="youtube",
                group_id=item.get("id", {}).get("playlistId", ""),
                name=item.get("snippet", {}).get("title", ""),
                description=item.get("snippet", {}).get("description", ""),
                topics=keywords,
                relevance_score=0.6,
            )
            for item in data.get("items", [])
        ]

    async def follow_user(self, user_id: str) -> bool:
        """Subscribe to a YouTube channel."""
        if self.demo_mode:
            logger.info(f"[DEMO] Subscribed to YouTube channel {user_id}")
            return True
        url = f"{self.BASE_URL}/subscriptions"
        payload = {
            "snippet": {
                "resourceId": {
                    "kind": "youtube#channel",
                    "channelId": user_id,
                }
            }
        }
        data = await self._request("POST", url, json=payload)
        return bool(data.get("id"))

    async def comment_on_post(self, post_id: str, comment: str) -> bool:
        """Comment on a YouTube video."""
        if self.demo_mode:
            logger.info(f"[DEMO] Commented on YouTube video {post_id}")
            return True
        url = f"{self.BASE_URL}/commentThreads"
        payload = {
            "snippet": {
                "videoId": post_id,
                "topLevelComment": {
                    "snippet": {"textOriginal": comment}
                }
            }
        }
        data = await self._request("POST", url, json=payload)
        return bool(data.get("id"))

    async def like_post(self, post_id: str) -> bool:
        """Like a YouTube video."""
        if self.demo_mode:
            logger.info(f"[DEMO] Liked YouTube video {post_id}")
            return True
        url = f"{self.BASE_URL}/videos/rate"
        params = {**self._auth_params(), "id": post_id, "rating": "like"}
        await self._request("POST", url, params=params)
        return True

    async def get_feed(self, limit: int = 20) -> List[SocialPost]:
        if self.demo_mode:
            return [
                SocialPost(
                    platform="youtube",
                    platform_post_id=f"demo_yt_feed_{i}",
                    content=f"סרטון #{i+1} - תוכן מעניין",
                    views_count=1000 + i * 500,
                    likes_count=80 + i * 20,
                    comments_count=15 + i * 5,
                    posted_at=datetime.now(),
                )
                for i in range(min(limit, 5))
            ]
        if not self._channel_id:
            await self.connect()
        url = f"{self.BASE_URL}/search"
        params = {**self._auth_params(), "part": "snippet", "channelId": self._channel_id, "maxResults": limit, "order": "date"}
        data = await self._request("GET", url, params=params)
        return [
            SocialPost(
                platform="youtube",
                platform_post_id=item.get("id", {}).get("videoId", ""),
                content=item.get("snippet", {}).get("title", ""),
                post_url=f"https://youtube.com/watch?v={item.get('id', {}).get('videoId', '')}",
            )
            for item in data.get("items", [])
        ]

    async def get_metrics(self, days: int = 30) -> PlatformMetrics:
        if self.demo_mode:
            return PlatformMetrics(
                platform="youtube",
                period_days=days,
                followers_gained=45,
                posts_published=8,
                total_views=12000,
                total_impressions=35000,
                total_likes=580,
                total_comments=95,
                engagement_rate=6.2,
                best_posting_times=["10:00", "14:00", "20:00"],
            )
        return PlatformMetrics(platform="youtube", period_days=days)

    def _demo_account(self) -> PlatformAccount:
        return PlatformAccount(
            platform="youtube",
            account_id="demo_yt_channel_123",
            username="@my_business_channel",
            display_name="ערוץ היוטיוב שלנו",
            bio="סרטוני תוכן מקצועי | עדכונים שבועיים",
            followers_count=820,
            posts_count=42,
            is_connected=True,
        )
