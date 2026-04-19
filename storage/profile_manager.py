"""
Profile Manager - stores and retrieves business profiles.
Uses JSON files for persistence (no extra DB needed).
"""
from __future__ import annotations
import json
import os
import logging
from typing import Optional, Dict
from datetime import datetime
from pathlib import Path

from models.business_profile import BusinessProfile

logger = logging.getLogger(__name__)

PROFILES_DIR = Path(os.getenv("PROFILES_DIR", os.path.join(os.getenv("DATA_DIR", "/tmp"), "ai-agent-profiles")))
PROFILES_DIR.mkdir(parents=True, exist_ok=True)


class ProfileManager:
    """Manages business profiles per session."""

    _cache: Dict[str, BusinessProfile] = {}

    @classmethod
    def _profile_path(cls, session_id: str) -> Path:
        safe_id = session_id.replace("/", "_").replace("\\", "_")[:64]
        return PROFILES_DIR / f"{safe_id}.json"

    @classmethod
    def get(cls, session_id: str) -> Optional[BusinessProfile]:
        """Load profile from cache or disk."""
        if session_id in cls._cache:
            return cls._cache[session_id]

        path = cls._profile_path(session_id)
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                profile = BusinessProfile(**data)
                cls._cache[session_id] = profile
                return profile
            except Exception as e:
                logger.error(f"Failed to load profile {session_id}: {e}")
        return None

    @classmethod
    def save(cls, profile: BusinessProfile) -> bool:
        """Save profile to cache and disk."""
        try:
            profile.updated_at = datetime.now()
            cls._cache[profile.session_id] = profile
            path = cls._profile_path(profile.session_id)
            path.write_text(
                profile.model_dump_json(indent=2),
                encoding="utf-8"
            )
            return True
        except Exception as e:
            logger.error(f"Failed to save profile {profile.session_id}: {e}")
            return False

    @classmethod
    def get_or_create(cls, session_id: str) -> BusinessProfile:
        """Get existing profile or create a new empty one."""
        profile = cls.get(session_id)
        if not profile:
            profile = BusinessProfile(session_id=session_id)
            cls.save(profile)
        return profile

    @classmethod
    def update_field(cls, session_id: str, field: str, value) -> bool:
        """Update a single field in the profile."""
        profile = cls.get_or_create(session_id)
        if hasattr(profile, field):
            setattr(profile, field, value)
            return cls.save(profile)
        return False

    @classmethod
    def delete(cls, session_id: str) -> bool:
        """Delete a profile."""
        cls._cache.pop(session_id, None)
        path = cls._profile_path(session_id)
        if path.exists():
            path.unlink()
            return True
        return False
