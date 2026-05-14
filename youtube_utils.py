import json
import re
import subprocess
import statistics
import sys
from typing import List, Dict, Any, Optional
from urllib.parse import parse_qs, urlparse

import requests
import config

class YouTubeUtility:
    """Utility class for all YouTube (yt-dlp) interactions."""

    @staticmethod
    def _yt_dlp_command() -> List[str]:
        """
        Run yt-dlp via the active Python environment.

        This avoids deploy issues where the `yt-dlp` shell binary is not on PATH
        even though the package is installed inside the current virtualenv.
        """
        return [sys.executable, "-m", "yt_dlp"]

    @staticmethod
    def _run_json_command(cmd: List[str], suppress_errors: bool = False) -> List[Dict[str, Any]]:
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            rows = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    rows.append(json.loads(line))
            return rows
        except Exception as e:
            if not suppress_errors:
                print(f"[!] yt-dlp command failed: {e}")
            return []

    @staticmethod
    def _youtube_api_enabled() -> bool:
        return bool(config.YOUTUBE_API_KEY)

    @staticmethod
    def _youtube_api_get(path: str, params: Dict[str, Any], suppress_errors: bool = False) -> Dict[str, Any]:
        if not YouTubeUtility._youtube_api_enabled():
            return {}

        try:
            response = requests.get(
                f"https://www.googleapis.com/youtube/v3/{path}",
                params={**params, "key": config.YOUTUBE_API_KEY},
                timeout=config.YOUTUBE_API_TIMEOUT,
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            if not suppress_errors:
                print(f"[!] YouTube Data API request failed ({path}): {e}")
            return {}

    @staticmethod
    def _extract_channel_id(channel_url: Optional[str]) -> Optional[str]:
        if not channel_url:
            return None
        match = re.search(r"/channel/([A-Za-z0-9_-]+)", channel_url)
        if match:
            return match.group(1)
        return None

    @staticmethod
    def _extract_video_id(video_url: Optional[str]) -> Optional[str]:
        if not video_url:
            return None
        parsed = urlparse(video_url)
        query_video_id = parse_qs(parsed.query).get("v")
        if query_video_id:
            return query_video_id[0]
        match = re.search(r"/(?:shorts|watch)/([A-Za-z0-9_-]+)", parsed.path)
        if match:
            return match.group(1)
        if parsed.path.strip("/"):
            tail = parsed.path.strip("/").split("/")[-1]
            if tail and tail != "watch":
                return tail
        return None

    @staticmethod
    def _optional_int(value: Any) -> Optional[int]:
        if value in (None, "", []):
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _get_videos_api(video_ids: List[str], parts: str = "snippet,statistics", suppress_errors: bool = False) -> List[Dict[str, Any]]:
        clean_ids = [video_id for video_id in video_ids if video_id]
        if not clean_ids or not YouTubeUtility._youtube_api_enabled():
            return []

        items: List[Dict[str, Any]] = []
        for start in range(0, len(clean_ids), 50):
            chunk = clean_ids[start:start + 50]
            data = YouTubeUtility._youtube_api_get(
                "videos",
                {"part": parts, "id": ",".join(chunk), "maxResults": len(chunk)},
                suppress_errors=suppress_errors,
            )
            items.extend(data.get("items", []))
        return items

    @staticmethod
    def _get_channels_api(channel_ids: List[str], parts: str = "statistics,contentDetails,snippet", suppress_errors: bool = False) -> List[Dict[str, Any]]:
        clean_ids = [channel_id for channel_id in channel_ids if channel_id]
        if not clean_ids or not YouTubeUtility._youtube_api_enabled():
            return []

        items: List[Dict[str, Any]] = []
        for start in range(0, len(clean_ids), 50):
            chunk = clean_ids[start:start + 50]
            data = YouTubeUtility._youtube_api_get(
                "channels",
                {"part": parts, "id": ",".join(chunk), "maxResults": len(chunk)},
                suppress_errors=suppress_errors,
            )
            items.extend(data.get("items", []))
        return items

    @staticmethod
    def _search_videos_api(query: str, limit: int, order: Optional[str] = None, published_after: Optional[str] = None, relevance_language: Optional[str] = None, suppress_errors: bool = False) -> List[Dict[str, Any]]:
        if not YouTubeUtility._youtube_api_enabled():
            return []

        remaining = max(int(limit or 0), 0)
        items: List[Dict[str, Any]] = []
        page_token: Optional[str] = None

        while remaining > 0:
            params: Dict[str, Any] = {
                "part": "snippet",
                "q": query,
                "type": "video",
                "maxResults": min(remaining, 50),
            }
            if order:
                params["order"] = order
            if published_after:
                params["publishedAfter"] = published_after
            if relevance_language:
                params["relevanceLanguage"] = relevance_language
            if page_token:
                params["pageToken"] = page_token

            data = YouTubeUtility._youtube_api_get("search", params, suppress_errors=suppress_errors)
            batch = data.get("items", [])
            if not batch:
                break

            items.extend(batch)
            remaining = max(limit - len(items), 0)
            page_token = data.get("nextPageToken")
            if not page_token:
                break

        return items[:limit]

    @staticmethod
    def _video_from_api_item(item: Dict[str, Any], channel_lookup: Optional[Dict[str, Dict[str, Any]]] = None) -> Dict[str, Any]:
        snippet = item.get("snippet", {})
        statistics = item.get("statistics", {})
        channel_id = snippet.get("channelId")
        channel_meta = (channel_lookup or {}).get(channel_id, {})
        channel_stats = channel_meta.get("statistics", {})
        channel_snippet = channel_meta.get("snippet", {})
        return {
            "id": item.get("id"),
            "title": snippet.get("title"),
            "description": snippet.get("description"),
            "channel": snippet.get("channelTitle"),
            "channel_id": channel_id,
            "channel_url": f"https://www.youtube.com/channel/{channel_id}" if channel_id else None,
            "view_count": int(statistics.get("viewCount", 0) or 0),
            "channel_follower_count": YouTubeUtility._optional_int(channel_stats.get("subscriberCount")) if not channel_stats.get("hiddenSubscriberCount") else None,
            "subscriber_count": YouTubeUtility._optional_int(channel_stats.get("subscriberCount")) if not channel_stats.get("hiddenSubscriberCount") else None,
            "upload_date": (snippet.get("publishedAt") or "").replace("-", "")[:8] or None,
            "timestamp": None,
            "uploader": channel_snippet.get("title") or snippet.get("channelTitle"),
            "uploader_url": f"https://www.youtube.com/channel/{channel_id}" if channel_id else None,
        }

    @staticmethod
    def _search_recent_api(query: str, limit: int, published_after: Optional[str] = None, suppress_errors: bool = False) -> List[Dict[str, Any]]:
        search_items = YouTubeUtility._search_videos_api(query, limit, order="date", published_after=published_after, relevance_language="en", suppress_errors=suppress_errors)
        video_ids = [item.get("id", {}).get("videoId") for item in search_items if item.get("id", {}).get("videoId")]
        if not video_ids:
            return []
        videos = YouTubeUtility._get_videos_api(video_ids, suppress_errors=suppress_errors)
        channel_ids = [item.get("snippet", {}).get("channelId") for item in videos if item.get("snippet", {}).get("channelId")]
        channels = {
            item.get("id"): item
            for item in YouTubeUtility._get_channels_api(channel_ids, parts="statistics,snippet", suppress_errors=suppress_errors)
        }
        return [YouTubeUtility._video_from_api_item(item, channel_lookup=channels) for item in videos]

    @staticmethod
    def _coerce_duration(video: Dict[str, Any]) -> Optional[float]:
        duration = video.get('duration')
        if duration is None:
            return None

        try:
            return float(duration)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _is_short(video: Dict[str, Any]) -> bool:
        duration = YouTubeUtility._coerce_duration(video)
        url = str(video.get('url') or video.get('webpage_url') or '')
        title = str(video.get('title') or '')

        if duration is not None and duration <= config.SHORTS_MAX_DURATION_SECONDS:
            return True
        if "/shorts/" in url:
            return True
        if "#shorts" in title.lower():
            return True
        return False

    @staticmethod
    def _build_channel_url(channel_url: str, short_only: bool = False) -> str:
        if not short_only:
            return channel_url

        normalized = channel_url.rstrip("/")
        for suffix in ("/videos", "/featured", "/streams"):
            if normalized.endswith(suffix):
                normalized = normalized[: -len(suffix)]
                break
        if normalized.endswith("/shorts"):
            return normalized

        return f"{normalized}/shorts"

    @staticmethod
    def _video_url(video_id: Optional[str]) -> Optional[str]:
        if not video_id:
            return None
        return f"https://www.youtube.com/watch?v={video_id}"

    @staticmethod
    def _merge_video_dicts(primary: Dict[str, Any], secondary: Dict[str, Any]) -> Dict[str, Any]:
        merged = dict(primary)
        for key, value in secondary.items():
            if merged.get(key) in (None, "", 0, []):
                merged[key] = value
        return merged

    @staticmethod
    def _search_full_metadata(query: str, limit: int) -> List[Dict[str, Any]]:
        cmd = [
            *YouTubeUtility._yt_dlp_command(),
            f"ytsearch{limit}:{query}",
            "--dump-json",
            "--quiet"
        ]
        return YouTubeUtility._run_json_command(cmd)

    @staticmethod
    def _search_recent_full_metadata(query: str, limit: int, published_after: Optional["datetime"] = None) -> List[Dict[str, Any]]:
        cmd = [
            *YouTubeUtility._yt_dlp_command(),
            f"ytsearchdate{limit}:{query}",
            "--dump-json",
            "--quiet",
        ]
        if published_after:
            from datetime import datetime as _dt
            date_str = published_after.strftime("%Y%m%d") if hasattr(published_after, "strftime") else str(published_after)
            cmd += ["--dateafter", date_str]
        rows = YouTubeUtility._run_json_command(cmd)
        # Post-filter for English when language metadata is available
        return [r for r in rows if not r.get("language") or r.get("language") == "en"]

    @staticmethod
    def _search_flat(query: str, limit: int) -> List[Dict[str, Any]]:
        cmd = [
            *YouTubeUtility._yt_dlp_command(),
            f"ytsearch{limit}:{query}",
            "--dump-json",
            "--flat-playlist",
            "--quiet"
        ]
        return YouTubeUtility._run_json_command(cmd)

    @staticmethod
    def search_shorts(query: str, limit: int) -> List[Dict[str, Any]]:
        queries = [query, f"{query} shorts", f"{query} #shorts"]
        results: List[Dict[str, Any]] = []
        seen_ids = set()

        for search_query in queries:
            rows = YouTubeUtility._search_full_metadata(search_query, limit)
            for row in rows:
                video_id = row.get("id")
                if not video_id or video_id in seen_ids:
                    continue
                if YouTubeUtility._is_short(row):
                    results.append(row)
                    seen_ids.add(video_id)
                if len(results) >= limit:
                    return results

        if results:
            return results

        fallback_rows = YouTubeUtility._search_flat(query, limit * 3)
        for row in fallback_rows:
            video_id = row.get("id")
            if not video_id or video_id in seen_ids:
                continue
            video_url = YouTubeUtility._video_url(video_id)
            if not video_url:
                continue
            details = YouTubeUtility.get_video_details(video_url)
            enriched = YouTubeUtility._merge_video_dicts(row, details)
            if YouTubeUtility._is_short(enriched):
                results.append(enriched)
                seen_ids.add(video_id)
            if len(results) >= limit:
                break

        return results
    
    @staticmethod
    def search(query: str, limit: int, short_only: bool = False, logger=None) -> List[Dict[str, Any]]:
        if logger:
            logger(f"[*] Searching for '{query}' (limit: {limit})...")
        else:
            print(f"[*] Searching for '{query}' (limit: {limit})...")
        if short_only:
            return YouTubeUtility.search_shorts(query, limit)
        return YouTubeUtility._search_flat(query, limit)

    @staticmethod
    def search_recent(query: str, limit: int, logger=None, published_after=None) -> List[Dict[str, Any]]:
        if logger:
            logger(f"[*] Searching recent videos for '{query}' (limit: {limit})...")
        else:
            print(f"[*] Searching recent videos for '{query}' (limit: {limit})...")
        published_after_iso = published_after.strftime("%Y-%m-%dT%H:%M:%SZ") if published_after else None
        api_rows = YouTubeUtility._search_recent_api(query, limit, published_after=published_after_iso, suppress_errors=True)
        if api_rows:
            return api_rows
        return YouTubeUtility._search_recent_full_metadata(query, limit, published_after=published_after)

    @staticmethod
    def get_channel_info(channel_url: str) -> Dict[str, Any]:
        """Fetches channel metadata like subscriber count. 
        Uses --playlist-end 1 to ensure we get at least one video's metadata 
        which typically contains the channel stats."""
        channel_id = YouTubeUtility._extract_channel_id(channel_url)
        if channel_id:
            items = YouTubeUtility._get_channels_api([channel_id], parts="statistics,snippet,contentDetails", suppress_errors=True)
            if items:
                item = items[0]
                statistics = item.get("statistics", {})
                snippet = item.get("snippet", {})
                return {
                    "id": item.get("id"),
                    "channel": snippet.get("title"),
                    "title": snippet.get("title"),
                    "channel_follower_count": YouTubeUtility._optional_int(statistics.get("subscriberCount")) if not statistics.get("hiddenSubscriberCount") else None,
                    "subscriber_count": YouTubeUtility._optional_int(statistics.get("subscriberCount")) if not statistics.get("hiddenSubscriberCount") else None,
                    "hiddenSubscriberCount": statistics.get("hiddenSubscriberCount"),
                    "uploads_playlist_id": item.get("contentDetails", {}).get("relatedPlaylists", {}).get("uploads"),
                    "video_count": YouTubeUtility._optional_int(statistics.get("videoCount")),
                }

        cmd = [
            *YouTubeUtility._yt_dlp_command(),
            "--dump-json",
            "--playlist-end", "1",
            "--quiet",
            channel_url
        ]
        rows = YouTubeUtility._run_json_command(cmd)
        if rows:
            return rows[0]
        return {}

    @staticmethod
    def get_channel_baseline(channel_url: str, limit: int, short_only: bool = False) -> Optional[float]:
        """Fetches last N videos and returns the median view count."""
        channel_id = YouTubeUtility._extract_channel_id(channel_url)
        if channel_id and not short_only and YouTubeUtility._youtube_api_enabled():
            channel_items = YouTubeUtility._get_channels_api([channel_id], parts="contentDetails", suppress_errors=True)
            if channel_items:
                uploads_playlist_id = (
                    channel_items[0]
                    .get("contentDetails", {})
                    .get("relatedPlaylists", {})
                    .get("uploads")
                )
                if uploads_playlist_id:
                    playlist_ids: List[str] = []
                    next_page_token: Optional[str] = None
                    while len(playlist_ids) < limit:
                        data = YouTubeUtility._youtube_api_get(
                            "playlistItems",
                            {
                                "part": "contentDetails",
                                "playlistId": uploads_playlist_id,
                                "maxResults": min(50, limit - len(playlist_ids)),
                                **({"pageToken": next_page_token} if next_page_token else {}),
                            },
                            suppress_errors=True,
                        )
                        items = data.get("items", [])
                        playlist_ids.extend(
                            item.get("contentDetails", {}).get("videoId")
                            for item in items
                            if item.get("contentDetails", {}).get("videoId")
                        )
                        next_page_token = data.get("nextPageToken")
                        if not next_page_token or not items:
                            break

                    video_items = YouTubeUtility._get_videos_api(playlist_ids[:limit], parts="statistics", suppress_errors=True)
                    views = [
                        int(item.get("statistics", {}).get("viewCount", 0) or 0)
                        for item in video_items
                        if int(item.get("statistics", {}).get("viewCount", 0) or 0) > 0
                    ]
                    if views:
                        return statistics.median(views)

        target_urls = [YouTubeUtility._build_channel_url(channel_url, short_only=short_only)]
        if short_only:
            target_urls.append(channel_url)

        rows: List[Dict[str, Any]] = []
        for target_url in target_urls:
            cmd = [
                *YouTubeUtility._yt_dlp_command(),
                f"--playlist-end", str(limit),
                "--dump-json",
                "--flat-playlist",
                "--quiet",
                target_url
            ]
            rows = YouTubeUtility._run_json_command(cmd, suppress_errors=short_only)
            if rows:
                break

        views = []
        for row in rows:
            if short_only and not YouTubeUtility._is_short(row):
                continue
            view_count = row.get('view_count') or 0
            if view_count > 0:
                views.append(view_count)
        return statistics.median(views) if views else None

    @staticmethod
    def get_video_details(video_url: str) -> Dict[str, Any]:
        """Fetches full video metadata including description."""
        video_id = YouTubeUtility._extract_video_id(video_url)
        if video_id:
            items = YouTubeUtility._get_videos_api([video_id], parts="snippet,statistics", suppress_errors=True)
            if items:
                item = items[0]
                snippet = item.get("snippet", {})
                channel_id = snippet.get("channelId")
                channel_lookup = {}
                if channel_id:
                    channel_items = YouTubeUtility._get_channels_api([channel_id], parts="statistics,snippet", suppress_errors=True)
                    if channel_items:
                        channel_lookup[channel_id] = channel_items[0]
                return YouTubeUtility._video_from_api_item(item, channel_lookup=channel_lookup)

        cmd = [
            *YouTubeUtility._yt_dlp_command(),
            "--dump-json",
            "--quiet",
            video_url
        ]
        rows = YouTubeUtility._run_json_command(cmd)
        if rows:
            return rows[0]
        return {}
