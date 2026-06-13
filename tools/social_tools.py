"""
Social media action tools for the AI advertising agent.
These functions are called by the Claude agent when it decides to take social actions.
"""
from __future__ import annotations
import logging
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)

# Platform registry - populated by agent at runtime
_platform_registry: Dict[str, Any] = {}


def register_platform(name: str, platform_instance: Any):
    """Register a platform instance for use by tools."""
    _platform_registry[name] = platform_instance


def _get_platform(platform_name: str) -> Optional[Any]:
    return _platform_registry.get(platform_name.lower())


async def post_content(
    platforms: List[str],
    content: str,
    media_urls: List[str] = None,
    groups: List[str] = None,
    hashtags: List[str] = None,
) -> Dict[str, Any]:
    """
    Post content to one or more social media platforms.

    Args:
        platforms: List of platform names (facebook, instagram, twitter, linkedin, youtube, tiktok)
        content: The post text content
        media_urls: Optional list of image/video URLs to attach
        groups: Optional list of group IDs to post to
        hashtags: Optional hashtags to append to the post
    """
    results = {}
    full_content = content
    if hashtags:
        full_content += "\n\n" + " ".join(f"#{tag.lstrip('#')}" for tag in hashtags)

    # Auto-generate branded image if no media provided
    if not media_urls:
        try:
            import os
            from tools.advanced_tools import generate_post_image
            base_url = os.getenv("PUBLIC_API_URL", "").rstrip("/")
            platform_hint = platforms[0] if platforms else "linkedin"
            img_url = generate_post_image(content=full_content, platform=platform_hint, base_url=base_url)
            if img_url:
                media_urls = [img_url]
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"[post_content] image generation failed: {e}")

    for platform_name in platforms:
        platform = _get_platform(platform_name)
        if not platform:
            results[platform_name] = {"success": False, "error": f"Platform '{platform_name}' not connected"}
            continue

        # Platform exists but has no real token — don't fake success
        if getattr(platform, "demo_mode", True):
            results[platform_name] = {
                "success": False,
                "error": f"Platform '{platform_name}' not connected — please link your account first",
            }
            continue

        try:
            if groups:
                for group_id in groups:
                    post = await platform.post_content(full_content, media_urls or [], target_id=group_id)
                    results[f"{platform_name}:{group_id}"] = {
                        "success": True,
                        "post_id": post.platform_post_id,
                        "post_url": post.post_url,
                    }
            else:
                post = await platform.post_content(full_content, media_urls or [])
                results[platform_name] = {
                    "success": True,
                    "post_id": post.platform_post_id,
                    "post_url": post.post_url,
                    "message": f"Successfully posted to {platform_name}",
                }
        except Exception as e:
            err = str(e)
            logger.error(f"Failed to post to {platform_name}: {err}")
            # Distinguish between connection errors and API errors
            if "not connected" in err.lower() or "no token" in err.lower():
                results[platform_name] = {"success": False, "error": f"Platform not connected: {err}"}
            else:
                results[platform_name] = {"success": False, "error": f"API error (platform IS connected but posting failed): {err}"}

    return {
        "results": results,
        "total_platforms": len(platforms),
        "successful": sum(1 for r in results.values() if r.get("success")),
    }


async def find_relevant_users(
    platform: str,
    keywords: List[str],
    limit: int = 20,
) -> Dict[str, Any]:
    """
    Find users/accounts relevant to the given keywords on a platform.

    Args:
        platform: Platform name to search on
        keywords: Topics/keywords to search for
        limit: Maximum number of users to return
    """
    p = _get_platform(platform)
    if not p:
        return {"error": f"Platform '{platform}' not connected", "users": []}

    try:
        users = await p.find_relevant_users(keywords, limit)
        return {
            "platform": platform,
            "keywords": keywords,
            "users": [
                {
                    "user_id": u.user_id,
                    "username": u.username,
                    "display_name": u.display_name,
                    "bio": u.bio[:100] if u.bio else "",
                    "followers": u.followers_count,
                    "relevance_score": u.relevance_score,
                    "topics": u.topics[:5],
                }
                for u in users
            ],
            "total_found": len(users),
        }
    except Exception as e:
        logger.error(f"Failed to find users on {platform}: {e}")
        return {"error": str(e), "users": []}


async def find_relevant_groups(
    platform: str,
    keywords: List[str],
    limit: int = 10,
) -> Dict[str, Any]:
    """
    Find groups, communities, or hashtag communities relevant to keywords.

    Args:
        platform: Platform name to search on
        keywords: Topics/keywords to search for
        limit: Maximum number of groups to return
    """
    p = _get_platform(platform)
    if not p:
        return {"error": f"Platform '{platform}' not connected", "groups": []}

    try:
        groups = await p.find_relevant_groups(keywords, limit)
        return {
            "platform": platform,
            "keywords": keywords,
            "groups": [
                {
                    "group_id": g.group_id,
                    "name": g.name,
                    "description": g.description[:100] if g.description else "",
                    "members": g.members_count,
                    "is_public": g.is_public,
                    "relevance_score": g.relevance_score,
                    "topics": g.topics[:5],
                }
                for g in groups
            ],
            "total_found": len(groups),
        }
    except Exception as e:
        logger.error(f"Failed to find groups on {platform}: {e}")
        return {"error": str(e), "groups": []}


async def follow_user(
    platform: str,
    user_id: str,
    username: str = "",
) -> Dict[str, Any]:
    """
    Follow or connect with a user on a platform.

    Args:
        platform: Platform name
        user_id: User ID to follow
        username: Username for logging
    """
    p = _get_platform(platform)
    if not p:
        return {"success": False, "error": f"Platform '{platform}' not connected"}

    try:
        success = await p.follow_user(user_id)
        return {
            "success": success,
            "platform": platform,
            "user_id": user_id,
            "username": username,
            "message": f"Successfully followed {username or user_id} on {platform}" if success else "Failed to follow",
        }
    except Exception as e:
        logger.error(f"Failed to follow {user_id} on {platform}: {e}")
        return {"success": False, "error": str(e)}


async def send_connection_request(
    platform: str,
    user_id: str,
    message: str = "",
    username: str = "",
) -> Dict[str, Any]:
    """
    Send a connection/friend request to a user.

    Args:
        platform: Platform name
        user_id: User ID to connect with
        message: Optional personalized message
        username: Username for reference
    """
    p = _get_platform(platform)
    if not p:
        return {"success": False, "error": f"Platform '{platform}' not connected"}

    try:
        # For most platforms this is the same as follow
        success = await p.follow_user(user_id)
        return {
            "success": success,
            "platform": platform,
            "user_id": user_id,
            "username": username,
            "message_sent": message,
            "action": "connection_request" if platform == "linkedin" else "follow",
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


async def comment_on_post(
    platform: str,
    post_id: str,
    comment: str,
) -> Dict[str, Any]:
    """
    Comment on a post on a social media platform.

    Args:
        platform: Platform name
        post_id: ID of the post to comment on
        comment: Comment text
    """
    p = _get_platform(platform)
    if not p:
        return {"success": False, "error": f"Platform '{platform}' not connected"}

    try:
        success = await p.comment_on_post(post_id, comment)
        return {
            "success": success,
            "platform": platform,
            "post_id": post_id,
            "comment": comment[:50] + "..." if len(comment) > 50 else comment,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


async def like_post(
    platform: str,
    post_id: str,
) -> Dict[str, Any]:
    """
    Like a post on a social media platform.

    Args:
        platform: Platform name
        post_id: ID of the post to like
    """
    p = _get_platform(platform)
    if not p:
        return {"success": False, "error": f"Platform '{platform}' not connected"}

    try:
        success = await p.like_post(post_id)
        return {"success": success, "platform": platform, "post_id": post_id}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def get_account_metrics(
    platform: str,
    days: int = 30,
) -> Dict[str, Any]:
    """
    Get performance metrics for a connected platform account.

    Args:
        platform: Platform name
        days: Number of days to look back
    """
    p = _get_platform(platform)
    if not p:
        return {"error": f"Platform '{platform}' not connected"}

    try:
        metrics = await p.get_metrics(days)
        return {
            "platform": platform,
            "period_days": days,
            "followers_gained": metrics.followers_gained,
            "posts_published": metrics.posts_published,
            "total_reach": metrics.total_reach,
            "total_impressions": metrics.total_impressions,
            "total_likes": metrics.total_likes,
            "total_comments": metrics.total_comments,
            "total_shares": metrics.total_shares,
            "engagement_rate": metrics.engagement_rate,
            "best_posting_times": metrics.best_posting_times,
        }
    except Exception as e:
        return {"error": str(e)}


async def search_hashtags(
    platform: str,
    topic: str,
    count: int = 15,
) -> Dict[str, Any]:
    """
    Search for relevant hashtags for a topic on a platform.

    Args:
        platform: Platform name
        topic: Topic to find hashtags for
        count: Number of hashtags to return
    """
    # Hashtag suggestions based on platform and topic
    base_hashtags = topic.replace(" ", "").lower()
    platform_hashtags = {
        "instagram": [f"#{base_hashtags}", f"#{base_hashtags}ישראל", "#ישראל", "#עסקים", "#שיווק", "#מותג", "#תוכן", "#יזמות", "#marketing", "#business"],
        "twitter": [f"#{base_hashtags}", "#ישראל", "#טכנולוגיה", "#עסקים", "#יזמות"],
        "tiktok": [f"#{base_hashtags}", "#viral", "#fyp", "#ישראל", "#foryou", "#trending"],
        "linkedin": [f"#{base_hashtags}", "#leadership", "#business", "#innovation", "#startup"],
        "youtube": [f"#{base_hashtags}", "#ישראל", "#tutorial", "#howto"],
        "facebook": [f"#{base_hashtags}", "#ישראל", "#עסקים"],
    }

    hashtags = platform_hashtags.get(platform, [f"#{base_hashtags}", "#ישראל", "#עסקים"])

    return {
        "platform": platform,
        "topic": topic,
        "hashtags": hashtags[:count],
        "recommended": hashtags[:5],
        "tip": f"Use 5-10 hashtags on {platform} for best reach",
    }


async def get_platform_feed(
    platform: str,
    limit: int = 10,
) -> Dict[str, Any]:
    """
    Get recent posts from a platform feed to engage with.

    Args:
        platform: Platform name
        limit: Number of posts to retrieve
    """
    p = _get_platform(platform)
    if not p:
        return {"error": f"Platform '{platform}' not connected", "posts": []}

    try:
        posts = await p.get_feed(limit)
        return {
            "platform": platform,
            "posts": [
                {
                    "post_id": post.platform_post_id,
                    "content": post.content[:150] if post.content else "",
                    "likes": post.likes_count,
                    "comments": post.comments_count,
                    "author": post.author_username,
                    "posted_at": post.posted_at.isoformat() if post.posted_at else None,
                }
                for post in posts
            ],
            "total": len(posts),
        }
    except Exception as e:
        return {"error": str(e), "posts": []}
