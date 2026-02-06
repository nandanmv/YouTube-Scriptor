import json
import subprocess
import statistics
from typing import List, Dict, Any, Optional

class YouTubeUtility:
    """Utility class for all YouTube (yt-dlp) interactions."""
    
    @staticmethod
    def search(query: str, limit: int) -> List[Dict[str, Any]]:
        print(f"[*] Searching for '{query}' (limit: {limit})...")
        cmd = [
            "yt-dlp",
            f"ytsearch{limit}:{query}",
            "--dump-json",
            "--flat-playlist",
            "--quiet"
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            videos = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    videos.append(json.loads(line))
            return videos
        except Exception as e:
            print(f"[!] Search failed: {e}")
            return []

    @staticmethod
    def get_channel_info(channel_url: str) -> Dict[str, Any]:
        """Fetches channel metadata like subscriber count. 
        Uses --playlist-end 1 to ensure we get at least one video's metadata 
        which typically contains the channel stats."""
        cmd = [
            "yt-dlp",
            "--dump-json",
            "--playlist-end", "1",
            "--quiet",
            channel_url
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            if result.stdout:
                first_line = result.stdout.strip().split('\n')[0]
                return json.loads(first_line)
        except Exception as e:
            pass
        return {}

    @staticmethod
    def get_channel_baseline(channel_url: str, limit: int) -> Optional[float]:
        """Fetches last N videos and returns the median view count."""
        cmd = [
            "yt-dlp",
            f"--playlist-end", str(limit),
            "--dump-json",
            "--flat-playlist",
            "--quiet",
            channel_url
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            views = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    v = json.loads(line)
                    view_count = v.get('view_count') or 0
                    views.append(view_count)
            return statistics.median(views) if views else None
        except Exception:
            return None

    @staticmethod
    def get_video_details(video_url: str) -> Dict[str, Any]:
        """Fetches full video metadata including description."""
        cmd = [
            "yt-dlp",
            "--dump-json",
            "--quiet",
            video_url
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            if result.stdout:
                return json.loads(result.stdout)
        except Exception as e:
            print(f"[!] Failed to fetch video details: {e}")
        return {}
