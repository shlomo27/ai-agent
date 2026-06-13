"""
LinkedIn platform integration.
API Docs: https://learn.microsoft.com/en-us/linkedin/
"""
from __future__ import annotations
import logging
from datetime import datetime
from typing import List, Dict, Any

import base64

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

    async def _introspect_token(self, client: Any) -> str:
        """Return granted scopes string, or error message, for diagnostics."""
        if not config.LINKEDIN_CLIENT_ID or not config.LINKEDIN_CLIENT_SECRET:
            return "client_id/secret not configured"
        creds = base64.b64encode(
            f"{config.LINKEDIN_CLIENT_ID}:{config.LINKEDIN_CLIENT_SECRET}".encode()
        ).decode()
        try:
            r = await client.post(
                "https://www.linkedin.com/oauth/v2/introspectToken",
                headers={"Authorization": f"Basic {creds}"},
                data={"token": self.access_token},
            )
            if r.status_code != 200:
                return f"introspection HTTP {r.status_code}: {r.text[:200]}"
            d = r.json()
            if not d.get("active"):
                return f"token inactive/revoked — raw: {r.text[:200]}"
            return d.get("scope", "no scope field in response")
        except Exception as e:
            return f"introspection failed: {e}"

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

    async def _upload_image_to_linkedin(self, client, image_url: str, author: str) -> str | None:
        """Upload an image to LinkedIn and return the asset URN, or None on failure."""
        try:
            import httpx as _httpx
            # 1. Download the image
            img_resp = await client.get(image_url, timeout=15.0, follow_redirects=True)
            if img_resp.status_code != 200:
                logger.warning(f"[linkedin] failed to fetch image {image_url}: {img_resp.status_code}")
                return None
            image_bytes = img_resp.content
            content_type = img_resp.headers.get("content-type", "image/png").split(";")[0].strip()

            # 2. Register upload
            register_payload = {
                "registerUploadRequest": {
                    "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
                    "owner": author,
                    "serviceRelationships": [{"relationshipType": "OWNER", "identifier": "urn:li:userGeneratedContent"}],
                }
            }
            reg_headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
                "X-Restli-Protocol-Version": "2.0.0",
            }
            reg_resp = await client.post(
                f"{self.BASE_URL}/assets?action=registerUpload",
                json=register_payload,
                headers=reg_headers,
            )
            if reg_resp.status_code not in (200, 201):
                logger.warning(f"[linkedin] registerUpload failed: {reg_resp.status_code} {reg_resp.text[:200]}")
                return None
            reg_data = reg_resp.json()
            upload_url = reg_data["value"]["uploadMechanism"]["com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"]["uploadUrl"]
            asset_urn = reg_data["value"]["asset"]

            # 3. Upload binary
            upload_headers = {"Authorization": f"Bearer {self.access_token}", "Content-Type": content_type}
            up_resp = await client.put(upload_url, content=image_bytes, headers=upload_headers, timeout=30.0)
            if up_resp.status_code not in (200, 201):
                logger.warning(f"[linkedin] image upload failed: {up_resp.status_code}")
                return None
            return asset_urn
        except Exception as e:
            logger.warning(f"[linkedin] image upload exception: {e}")
            return None

    async def post_content(
        self,
        text: str,
        media_urls: List[str] = None,
        target_id: str = None,
        **kwargs,
    ) -> SocialPost:
        """Post an update to LinkedIn using the new Posts API (ugcPosts is deprecated for new apps)."""
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

        import httpx as _httpx
        from platforms.base import PlatformError
        async with _httpx.AsyncClient(timeout=30.0) as client:
            # Try to upload image if provided
            asset_urn = None
            if media_urls:
                asset_urn = await self._upload_image_to_linkedin(client, media_urls[0], author)

            # 1) Try ugcPosts first — works with w_member_social + "Share on LinkedIn" product
            legacy_url = f"{self.BASE_URL}/ugcPosts"
            if asset_urn:
                share_content = {
                    "shareCommentary": {"text": text},
                    "shareMediaCategory": "IMAGE",
                    "media": [{"status": "READY", "media": asset_urn}],
                }
            else:
                share_content = {
                    "shareCommentary": {"text": text},
                    "shareMediaCategory": "NONE",
                }
            legacy_payload = {
                "author": author,
                "lifecycleState": "PUBLISHED",
                "specificContent": {"com.linkedin.ugc.ShareContent": share_content},
                "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
            }
            legacy_headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
                "X-Restli-Protocol-Version": "2.0.0",
                "LinkedIn-Version": "202503",
            }
            r1 = await client.post(legacy_url, json=legacy_payload, headers=legacy_headers)
            if r1.status_code in (200, 201):
                data = r1.json() if r1.text else {}
                return SocialPost(
                    platform="linkedin",
                    platform_post_id=data.get("id", ""),
                    content=text,
                    posted_at=datetime.now(),
                )
            if r1.status_code == 403 and "ugcPosts.CREATE" in r1.text:
                granted_scopes = await self._introspect_token(client)
                logger.error("LinkedIn ugcPosts.CREATE 403 — granted scopes: %s", granted_scopes)
                raise PlatformError(
                    "linkedin",
                    f"LinkedIn posting blocked (ugcPosts.CREATE 403). "
                    f"Granted scopes: [{granted_scopes}]. "
                    f"Needs w_member_social + 'Share on LinkedIn' product in Developer Portal. "
                    f"Raw error: {r1.text[:200]}",
                    403,
                )
            ugc_error = f"HTTP {r1.status_code}: {r1.text[:200]}"

            # 2) Fallback: new versioned REST API (quarterly versions: 03/06/09/12)
            _REST_VERSIONS = [
                "202503", "202412", "202409", "202406",
                "202403", "202312", "202309", "202306",
            ]
            rest_url = "https://api.linkedin.com/rest/posts"
            rest_payload: Dict[str, Any] = {
                "author": author,
                "commentary": text,
                "visibility": "PUBLIC",
                "distribution": {
                    "feedDistribution": "MAIN_FEED",
                    "targetEntities": [],
                    "thirdPartyDistributionChannels": [],
                },
                "lifecycleState": "PUBLISHED",
                "isReshareDisableForOperator": False,
            }
            rest_last_error = ""
            for version in _REST_VERSIONS:
                headers = {
                    "Authorization": f"Bearer {self.access_token}",
                    "LinkedIn-Version": version,
                    "Content-Type": "application/json",
                }
                r = await client.post(rest_url, json=rest_payload, headers=headers)
                if r.status_code in (400, 426):
                    rest_last_error = r.text[:200]
                    continue  # wrong version — try next
                if r.status_code == 403:
                    rest_last_error = r.text[:200]
                    break  # access denied — no point trying more versions
                if r.status_code not in (200, 201):
                    raise PlatformError("linkedin", f"HTTP {r.status_code}: {r.text[:300]}", r.status_code)
                post_id = r.headers.get("x-restli-id", "")
                return SocialPost(
                    platform="linkedin",
                    platform_post_id=post_id,
                    content=text,
                    post_url=f"https://www.linkedin.com/feed/update/{post_id}" if post_id else "https://www.linkedin.com/feed/",
                    posted_at=datetime.now(),
                )

            granted_scopes = await self._introspect_token(client)
            logger.error("LinkedIn all posting attempts failed — granted scopes: %s", granted_scopes)
            raise PlatformError(
                "linkedin",
                f"LinkedIn posting failed. Granted scopes: [{granted_scopes}]. "
                f"ugcPosts: {ugc_error} | REST/posts: {rest_last_error or 'not tried'}",
                403,
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
