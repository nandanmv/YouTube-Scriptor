from __future__ import annotations

import math
import re
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, Iterable, List, Optional

from agents.base import BaseAgent
from youtube_utils import YouTubeUtility


class TrendAgent(BaseAgent):
    """Mine recent tech videos and surface rising AI-related terms."""

    DEFAULT_SEEDS = [
        "artificial intelligence",
        "ai agents",
        "llm",
        "coding",
        "developer tools",
        "automation",
    ]

    TERM_PATTERNS = {
        "AI agents": [r"\bai agents?\b", r"\bagentic ai\b"],
        "MCP": [r"\bmcp\b", r"\bmodel context protocol\b"],
        "Claude Code": [r"\bclaude code\b"],
        "Cursor": [r"\bcursor\b"],
        "RAG": [r"\brag\b", r"\bretrieval augmented generation\b"],
        "LLMs": [r"\bllms?\b", r"\blarge language models?\b"],
        "Vibe coding": [r"\bvibe coding\b", r"\bvibecoding\b"],
        "n8n": [r"\bn8n\b"],
        "Browser automation": [r"\bbrowser automation\b", r"\bbrowser use\b", r"\bcomputer use\b"],
        "Coding agents": [r"\bcoding agents?\b", r"\bcode agents?\b", r"\bai coding\b"],
        "Local AI": [r"\blocal ai\b", r"\bon device ai\b"],
        "OpenAI": [r"\bopenai\b", r"\bchatgpt\b", r"\bgpt[- ]?5\b", r"\bgpt[- ]?4o\b"],
        "Anthropic": [r"\banthropic\b", r"\bclaude\b"],
        "Gemini": [r"\bgemini\b"],
        "DeepSeek": [r"\bdeepseek\b"],
        "LangChain": [r"\blangchain\b", r"\blanggraph\b"],
        "AI automation": [r"\bai automation\b", r"\bai workflow(s)?\b", r"\bautomation\b"],
    }

    def __init__(self, use_database: bool = False, progress_callback=None):
        super().__init__(use_database=use_database)
        self.progress_callback = progress_callback

    def _log(self, message: str):
        if self.progress_callback:
            self.progress_callback(message)
        else:
            print(message)

    def run(
        self,
        seeds: Optional[Iterable[str]] = None,
        lookback_days: int = 14,
        max_videos_per_seed: int = 15,
        ai_only: bool = True,
        max_terms: int = 12,
    ) -> Dict[str, Any]:
        seed_terms = [seed.strip() for seed in (seeds or self.DEFAULT_SEEDS) if str(seed).strip()]
        if not seed_terms:
            seed_terms = list(self.DEFAULT_SEEDS)

        cutoff = datetime.now() - timedelta(days=max(lookback_days, 1))
        unique_videos: Dict[str, Dict[str, Any]] = {}

        self._log(f"[*] TrendAgent scanning {len(seed_terms)} tech seed(s) across the last {lookback_days} day(s)...")
        for idx, seed in enumerate(seed_terms, 1):
            self._log(f"[*] Seed {idx}/{len(seed_terms)}: {seed}")
            rows = YouTubeUtility.search_recent(seed, max_videos_per_seed, logger=self._log)
            kept = 0
            for row in rows:
                video_id = row.get("id")
                if not video_id:
                    continue
                upload_date = self._parse_upload_date(row)
                if upload_date and upload_date < cutoff:
                    continue
                unique_videos.setdefault(video_id, row)
                kept += 1
            self._log(f"[+] Retained {kept} recent videos for seed '{seed}'.")

        videos = list(unique_videos.values())
        self._log(f"[*] Deduplicated to {len(videos)} unique recent videos.")
        ranked_terms = self._rank_terms(videos, lookback_days=lookback_days, ai_only=ai_only, max_terms=max_terms)
        self._log(f"[+] Trend mining complete. Ranked {len(ranked_terms)} AI term(s).")

        return {
            "seed_terms": seed_terms,
            "lookback_days": lookback_days,
            "videos_analyzed": len(videos),
            "unique_channels": len({video.get('channel') for video in videos if video.get('channel')}),
            "terms": ranked_terms,
            "generated_at": datetime.now().isoformat(),
            "note": "Trend scores are inferred from recent YouTube momentum, not an official YouTube trending feed.",
        }

    def _rank_terms(
        self,
        videos: List[Dict[str, Any]],
        lookback_days: int,
        ai_only: bool,
        max_terms: int,
    ) -> List[Dict[str, Any]]:
        term_buckets: Dict[str, Dict[str, Any]] = {}
        recent_cutoff = datetime.now() - timedelta(days=max(3, lookback_days // 2))

        for video in videos:
            matched_terms = self._match_terms(video, ai_only=ai_only)
            if not matched_terms:
                continue

            upload_date = self._parse_upload_date(video)
            age_days = max((datetime.now() - upload_date).days, 1) if upload_date else max(lookback_days // 2, 1)
            views = int(video.get("view_count") or 0)
            velocity = views / age_days

            sample_video = {
                "title": video.get("title"),
                "url": f"https://www.youtube.com/watch?v={video.get('id')}",
                "channel": video.get("channel"),
                "views": views,
                "upload_date": upload_date.strftime("%Y-%m-%d") if upload_date else None,
                "views_per_day": round(velocity, 1),
            }

            for term in matched_terms:
                bucket = term_buckets.setdefault(term, {
                    "term": term,
                    "mentions": 0,
                    "distinct_channels": set(),
                    "total_views": 0,
                    "total_velocity": 0.0,
                    "recent_mentions": 0,
                    "sample_videos": [],
                })
                bucket["mentions"] += 1
                bucket["distinct_channels"].add(video.get("channel") or "Unknown channel")
                bucket["total_views"] += views
                bucket["total_velocity"] += velocity
                if upload_date and upload_date >= recent_cutoff:
                    bucket["recent_mentions"] += 1
                bucket["sample_videos"].append(sample_video)

        if not term_buckets:
            return []

        max_mentions = max(bucket["mentions"] for bucket in term_buckets.values()) or 1
        max_channels = max(len(bucket["distinct_channels"]) for bucket in term_buckets.values()) or 1
        max_views = max(bucket["total_views"] for bucket in term_buckets.values()) or 1
        max_velocity = max(bucket["total_velocity"] for bucket in term_buckets.values()) or 1

        ranked_terms = []
        for bucket in term_buckets.values():
            mentions_norm = bucket["mentions"] / max_mentions
            channels_norm = len(bucket["distinct_channels"]) / max_channels
            views_norm = bucket["total_views"] / max_views
            velocity_norm = bucket["total_velocity"] / max_velocity
            trend_score = round(
                100 * (
                    0.30 * mentions_norm +
                    0.20 * channels_norm +
                    0.20 * views_norm +
                    0.30 * velocity_norm
                ),
                1,
            )
            recent_share = bucket["recent_mentions"] / max(bucket["mentions"], 1)
            if recent_share >= 0.7 and velocity_norm >= 0.45:
                momentum = "accelerating"
            elif velocity_norm >= 0.6:
                momentum = "hot"
            elif recent_share >= 0.45:
                momentum = "rising"
            else:
                momentum = "steady"

            sample_videos = sorted(
                bucket["sample_videos"],
                key=lambda item: (item.get("views_per_day") or 0, item.get("views") or 0),
                reverse=True,
            )[:3]

            ranked_terms.append({
                "term": bucket["term"],
                "trend_score": trend_score,
                "momentum": momentum,
                "mentions": bucket["mentions"],
                "distinct_channels": len(bucket["distinct_channels"]),
                "total_views": bucket["total_views"],
                "avg_views_per_day": round(bucket["total_velocity"] / max(bucket["mentions"], 1), 1),
                "sample_videos": sample_videos,
            })

        ranked_terms.sort(
            key=lambda item: (
                item["trend_score"],
                item["mentions"],
                item["distinct_channels"],
                item["total_views"],
            ),
            reverse=True,
        )
        return ranked_terms[:max_terms]

    def _match_terms(self, video: Dict[str, Any], ai_only: bool) -> List[str]:
        blob = self._normalize_text(f"{video.get('title', '')} {video.get('description', '')} {video.get('channel', '')}")
        matches = [
            canonical
            for canonical, patterns in self.TERM_PATTERNS.items()
            if any(re.search(pattern, blob) for pattern in patterns)
        ]
        if ai_only:
            return matches
        return matches or self._fallback_topic_terms(blob)

    def _fallback_topic_terms(self, blob: str) -> List[str]:
        phrases = []
        for phrase in ("developer tools", "automation", "startups", "programming", "software"):
            if phrase in blob:
                phrases.append(phrase.title())
        return phrases

    def _normalize_text(self, value: Any) -> str:
        return re.sub(r"\s+", " ", str(value or "").lower()).strip()

    def _parse_upload_date(self, video: Dict[str, Any]) -> Optional[datetime]:
        upload_date = video.get("upload_date")
        if upload_date:
            try:
                return datetime.strptime(str(upload_date), "%Y%m%d")
            except ValueError:
                return None
        timestamp = video.get("timestamp") or video.get("release_timestamp")
        if timestamp:
            try:
                return datetime.fromtimestamp(int(timestamp))
            except (TypeError, ValueError, OSError):
                return None
        return None
