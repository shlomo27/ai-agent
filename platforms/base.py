"""
Abstract base class for all social media platform integrations.
"""
from __future__ import annotations
import logging
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
import httpx

from models.platform import (
    PlatformAccount, SocialPost, DiscoveredUser, DiscoveredGroup, PlatformMetrics
)

logger = logging.getLogger(__name__)


class PlatformError(Exception):
    """Raised when a platform API call fails."""
    def __init__(self, platform: str, message: str, status_code: int = 0):
        self.platform = platform
        self.status_code = status_code
        super().__init__(f"[{platform}] {message}")


class BasePlatform(ABC):
    """
    Abstract base class for social media platform integrations.
    All platform implementations must inherit from this class.
    """

    platform_name: str = "base"

    def __init__(self, access_token: str = "", demo_mode: bool = True):
        self.access_token = access_token
        self.demo_mode = demo_mode
        self._client: Optional[httpx.AsyncClient] = None
        self.logger = logging.getLogger(f"platform.{self.platform_name}")

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=30.0,
                headers=self._get_default_headers(),
            )
        return self._client

    def _get_default_headers(self) -> Dict[str, str]:
        return {
            "Content-Type": "application/json",
            "User-Agent": "AIAdvertisingAgent/1.0",
        }

    async def _request(
        self,
        method: str,
        url: str,
        **kwargs,
    ) -> Dict[str, Any]:
        """Make an HTTP request to the platform API with error handling."""
        if self.demo_mode:
            return self._demo_response(method, url, **kwargs)

        client = await self._get_client()
        try:
            response = await client.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise PlatformError(
                self.platform_name,
                f"HTTP {e.response.status_code}: {e.response.text}",
                e.response.status_code,
            )
        except httpx.RequestError as e:
            raise PlatformError(self.platform_name, f"Request failed: {str(e)}")

    def _demo_response(self, method: str, url: str, **kwargs) -> Dict[str, Any]:
        """Return a realistic demo response for testing without real API credentials."""
        return {
            "id": "demo_12345",
            "success": True,
            "data": {
                "id": "demo_post_12345",
                "message": "Demo mode - no real API call made",
            },
        }

    @abstractmethod
    async def connect(self) -> PlatformAccount:
        """Connect to the platform and return account info."""
        ...

    @abstractmethod
    async def get_account_info(self) -> PlatformAccount:
        """Get current account information."""
        ...

    @abstractmethod
    async def post_content(
        self,
        text: str,
        media_urls: List[str] = None,
        target_id: str = None,
        **kwargs,
    ) -> SocialPost:
        """Post content to the platform."""
        ...

    @abstractmethod
    async def find_relevant_users(
        self,
        keywords: List[str],
        limit: int = 20,
    ) -> List[DiscoveredUser]:
        """Find users relevant to the given keywords."""
        ...

    @abstractmethod
    async def find_relevant_groups(
        self,
        keywords: List[str],
        limit: int = 10,
    ) -> List[DiscoveredGroup]:
        """Find groups/communities relevant to the given keywords."""
        ...

    @abstractmethod
    async def follow_user(self, user_id: str) -> bool:
        """Follow or connect with a user."""
        ...

    @abstractmethod
    async def comment_on_post(self, post_id: str, comment: str) -> bool:
        """Comment on a post."""
        ...

    @abstractmethod
    async def like_post(self, post_id: str) -> bool:
        """Like a post."""
        ...

    @abstractmethod
    async def get_feed(self, limit: int = 20) -> List[SocialPost]:
        """Get the latest posts from the feed."""
        ...

    @abstractmethod
    async def get_metrics(self, days: int = 30) -> PlatformMetrics:
        """Get platform performance metrics."""
        ...

    async def close(self):
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    def is_connected(self) -> bool:
        """Check if platform credentials are available."""
        return bool(self.access_token)
