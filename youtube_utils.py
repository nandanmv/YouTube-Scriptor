import json
import subprocess
import statistics
import sys
from typing import List, Dict, Any, Optional

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
    def _search_recent_full_metadata(query: str, limit: int) -> List[Dict[str, Any]]:
        cmd = [
            *YouTubeUtility._yt_dlp_command(),
            f"ytsearchdate{limit}:{query}",
            "--dump-json",
            "--quiet"
        ]
        return YouTubeUtility._run_json_command(cmd)

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
    def search_recent(query: str, limit: int, logger=None) -> List[Dict[str, Any]]:
        if logger:
            logger(f"[*] Searching recent videos for '{query}' (limit: {limit})...")
        else:
            print(f"[*] Searching recent videos for '{query}' (limit: {limit})...")
        return YouTubeUtility._search_recent_full_metadata(query, limit)

    @staticmethod
    def get_channel_info(channel_url: str) -> Dict[str, Any]:
        """Fetches channel metadata like subscriber count. 
        Uses --playlist-end 1 to ensure we get at least one video's metadata 
        which typically contains the channel stats."""
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
