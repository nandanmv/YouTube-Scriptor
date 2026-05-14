from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Any, Dict, Iterable, List, Optional

import config
from agents.base import BaseAgent
from youtube_utils import YouTubeUtility


class TrendAgent(BaseAgent):
    """Mine recent tech videos and surface rising AI-related terms."""

    DEFAULT_SEEDS = [
        "artificial intelligence",
        "ai agents",
        "ai workflow",
    ]

    TERM_PATTERNS = {
        "AI agents": [
            r"\bai agents?\b",
            r"\bagentic ai\b",
            r"\bagentic\b",
            r"\bagents?\b",
            r"\bagent frameworks?\b",
            r"\bautonomous agents?\b",
        ],
        "MCP": [r"\bmcp\b", r"\bmodel context protocol\b"],
        "Claude Code": [r"\bclaude code\b"],
        "Cursor": [r"\bcursor\b"],
        "RAG": [
            r"\brag\b",
            r"\bretrieval augmented generation\b",
            r"\bretrieval[- ]augmented\b",
            r"\bvector (db|database|search)\b",
            r"\bsemantic search\b",
            r"\bhybrid search\b",
        ],
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
        "Hermes": [r"\bhermes\b", r"\bopenhermes\b", r"\bhermes agents?\b", r"\bhermes flow\b"],
        "AI automation": [r"\bai automation\b", r"\bai workflow(s)?\b"],
    }

    TERM_PRIORITY = [
        "Claude Code",
        "MCP",
        "Hermes",
        "Cursor",
        "RAG",
        "n8n",
        "Browser automation",
        "Coding agents",
        "Local AI",
        "OpenAI",
        "Anthropic",
        "Gemini",
        "DeepSeek",
        "LangChain",
        "Vibe coding",
        "AI agents",
        "LLMs",
        "AI automation",
    ]

    SEED_STOPWORDS = {
        "a", "an", "and", "for", "in", "of", "on", "or", "the", "to", "with",
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
        lookback_days: int = 30,
        max_videos_per_seed: int = 30,
        ai_only: bool = True,
        max_terms: int = 12,
    ) -> Dict[str, Any]:
        provided_seed_terms = [seed.strip() for seed in (seeds or []) if str(seed).strip()]
        custom_seed_mode = bool(provided_seed_terms)
        seed_terms = provided_seed_terms
        if not seed_terms:
            seed_terms = list(self.DEFAULT_SEEDS)

        cutoff = datetime.now() - timedelta(days=max(lookback_days, 1))
        search_limit = min(
            max(max_videos_per_seed, 1) * config.TREND_SEARCH_POOL_MULTIPLIER,
            config.TREND_MAX_SEARCH_POOL,
        )
        unique_videos: Dict[str, Dict[str, Any]] = {}
        seed_specs = self._build_seed_specs(seed_terms) if custom_seed_mode else []

        self._log(f"[*] TrendAgent scanning {len(seed_terms)} tech seed(s) across the last {lookback_days} day(s)...")
        for idx, seed in enumerate(seed_terms, 1):
            self._log(f"[*] Seed {idx}/{len(seed_terms)}: {seed}")
            rows = YouTubeUtility.search_recent(seed, search_limit, logger=self._log, published_after=cutoff)
            prepared_rows: List[Dict[str, Any]] = []
            for row in rows:
                prepared = self._prepare_video(row, cutoff=cutoff, lookback_days=lookback_days)
                if prepared:
                    prepared_rows.append(prepared)

            qualified_rows = [
                video for video in prepared_rows
                if self._passes_quality_floor(video)
            ]
            selected_rows = self._select_seed_candidates(qualified_rows, max_videos_per_seed)
            for row in selected_rows:
                unique_videos.setdefault(row["id"], row)

            self._log(
                f"[+] Seed '{seed}' fetched {len(prepared_rows)} recent candidates, "
                f"qualified {len(qualified_rows)}, selected {len(selected_rows)}."
            )

        videos = list(unique_videos.values())
        self._log(f"[*] Deduplicated to {len(videos)} unique recent videos.")
        if custom_seed_mode:
            ranked_terms = self._rank_custom_seed_terms(
                seed_specs=seed_specs,
                videos=videos,
                lookback_days=lookback_days,
                max_terms=max_terms,
            )
        else:
            ranked_terms = self._rank_terms(videos, lookback_days=lookback_days, ai_only=ai_only, max_terms=max_terms)
        self._log(f"[+] Trend mining complete. Ranked {len(ranked_terms)} term(s).")

        return {
            "seed_terms": seed_terms,
            "lookback_days": lookback_days,
            "videos_analyzed": len(videos),
            "unique_channels": len({video.get('channel') for video in videos if video.get('channel')}),
            "terms": ranked_terms,
            "custom_seed_mode": custom_seed_mode,
            "generated_at": datetime.now().isoformat(),
            "note": "Trend scores are inferred from recent YouTube momentum, not an official YouTube trending feed.",
        }

    def _prepare_video(
        self,
        video: Dict[str, Any],
        cutoff: datetime,
        lookback_days: int,
    ) -> Optional[Dict[str, Any]]:
        video_id = video.get("id")
        if not video_id:
            return None

        upload_date = self._parse_upload_date(video)
        if upload_date and upload_date < cutoff:
            return None

        prepared = dict(video)
        age_days = max((datetime.now() - upload_date).days, 1) if upload_date else max(lookback_days // 2, 1)
        views = int(prepared.get("view_count") or 0)
        prepared["_upload_date_dt"] = upload_date
        prepared["_age_days"] = age_days
        prepared["_views"] = views
        prepared["_velocity"] = views / age_days
        return prepared

    def _passes_quality_floor(self, video: Dict[str, Any]) -> bool:
        views = int(video.get("_views") or video.get("view_count") or 0)
        velocity = float(video.get("_velocity") or 0.0)
        return views >= config.TREND_MIN_VIEWS and velocity >= config.TREND_MIN_VIEWS_PER_DAY

    def _select_seed_candidates(self, videos: List[Dict[str, Any]], limit: int) -> List[Dict[str, Any]]:
        ranked = sorted(
            videos,
            key=lambda item: (
                item.get("_velocity") or 0.0,
                item.get("_views") or 0,
                item.get("_upload_date_dt") or datetime.min,
            ),
            reverse=True,
        )
        return ranked[:max(limit, 0)]

    def _build_seed_specs(self, seeds: List[str]) -> List[Dict[str, Any]]:
        return [self._build_seed_spec(seed) for seed in seeds]

    def _build_seed_spec(self, seed: str) -> Dict[str, Any]:
        normalized_seed = self._normalize_text(seed)
        token_groups = self._build_seed_token_groups(normalized_seed)
        patterns = []
        if token_groups:
            phrase_parts = [self._token_group_phrase(group) for group in token_groups]
            if phrase_parts:
                patterns.append(r"\b" + r"\W+".join(phrase_parts) + r"\b")

        for canonical, canonical_patterns in self.TERM_PATTERNS.items():
            canonical_normalized = self._normalize_text(canonical)
            if canonical_normalized in normalized_seed or normalized_seed in canonical_normalized:
                patterns.extend(canonical_patterns)

        return {
            "label": self._display_seed_label(seed),
            "patterns": patterns,
            "token_groups": token_groups,
        }

    def _build_seed_token_groups(self, normalized_seed: str) -> List[List[str]]:
        groups: List[List[str]] = []
        for token in re.findall(r"[a-z0-9]+", normalized_seed):
            if token in self.SEED_STOPWORDS:
                continue
            variants = {token}
            if token.endswith("s") and len(token) > 3:
                variants.add(token[:-1])
            elif len(token) > 2:
                variants.add(f"{token}s")
            groups.append(sorted(variants))
        return groups

    def _token_group_phrase(self, group: List[str]) -> str:
        escaped = [re.escape(token) for token in group]
        if len(escaped) == 1:
            return escaped[0]
        return "(?:" + "|".join(escaped) + ")"

    def _display_seed_label(self, seed: str) -> str:
        words = []
        for raw_word in seed.strip().split():
            lower = raw_word.lower()
            if lower in {"ai", "llm", "llms", "mcp", "rag"}:
                words.append(raw_word.upper())
            else:
                words.append(raw_word[:1].upper() + raw_word[1:])
        return " ".join(words)

    def _rank_custom_seed_terms(
        self,
        seed_specs: List[Dict[str, Any]],
        videos: List[Dict[str, Any]],
        lookback_days: int,
        max_terms: int,
    ) -> List[Dict[str, Any]]:
        buckets = {
            spec["label"]: self._empty_bucket(spec["label"])
            for spec in seed_specs
        }

        for spec in seed_specs:
            bucket = buckets[spec["label"]]
            for video in videos:
                if self._match_seed_spec(spec, video):
                    self._append_video_to_bucket(bucket, video, lookback_days=lookback_days)

        ranked_terms = self._finalize_buckets(list(buckets.values()), max_terms=max_terms, include_empty=True)
        return ranked_terms

    def _rank_terms(
        self,
        videos: List[Dict[str, Any]],
        lookback_days: int,
        ai_only: bool,
        max_terms: int,
    ) -> List[Dict[str, Any]]:
        term_buckets: Dict[str, Dict[str, Any]] = {}
        for video in videos:
            matched_terms = self._match_terms(video, ai_only=ai_only)
            if not matched_terms:
                continue
            primary_term = self._pick_primary_term(matched_terms)
            bucket = term_buckets.setdefault(primary_term, self._empty_bucket(primary_term))
            self._append_video_to_bucket(bucket, video, lookback_days=lookback_days)

        return self._finalize_buckets(list(term_buckets.values()), max_terms=max_terms)

    def _empty_bucket(self, label: str) -> Dict[str, Any]:
        return {
            "term": label,
            "mentions": 0,
            "distinct_channels": set(),
            "total_views": 0,
            "total_velocity": 0.0,
            "recent_mentions": 0,
            "sample_videos": [],
        }

    def _append_video_to_bucket(
        self,
        bucket: Dict[str, Any],
        video: Dict[str, Any],
        lookback_days: int,
    ) -> None:
        upload_date = video.get("_upload_date_dt") or self._parse_upload_date(video)
        views = int(video.get("_views") or video.get("view_count") or 0)
        velocity = float(video.get("_velocity") or 0.0)
        recent_cutoff = datetime.now() - timedelta(days=max(3, lookback_days // 2))

        sample_video = {
            "id": video.get("id"),
            "title": video.get("title"),
            "url": f"https://www.youtube.com/watch?v={video.get('id')}",
            "channel": video.get("channel"),
            "views": views,
            "upload_date": upload_date.strftime("%Y-%m-%d") if upload_date else None,
            "views_per_day": round(velocity, 1),
        }

        bucket["mentions"] += 1
        bucket["distinct_channels"].add(video.get("channel") or "Unknown channel")
        bucket["total_views"] += views
        bucket["total_velocity"] += velocity
        if upload_date and upload_date >= recent_cutoff:
            bucket["recent_mentions"] += 1
        bucket["sample_videos"].append(sample_video)

    def _finalize_buckets(
        self,
        buckets: List[Dict[str, Any]],
        max_terms: int,
        include_empty: bool = False,
    ) -> List[Dict[str, Any]]:
        active_buckets = buckets if include_empty else [bucket for bucket in buckets if bucket["mentions"] > 0]
        if not active_buckets:
            return []

        scoring_buckets = [bucket for bucket in active_buckets if bucket["mentions"] > 0]
        max_mentions = max((bucket["mentions"] for bucket in scoring_buckets), default=1) or 1
        max_channels = max((len(bucket["distinct_channels"]) for bucket in scoring_buckets), default=1) or 1
        max_views = max((bucket["total_views"] for bucket in scoring_buckets), default=1) or 1
        max_velocity = max((bucket["total_velocity"] for bucket in scoring_buckets), default=1) or 1

        ranked_terms = []
        for bucket in active_buckets:
            if bucket["mentions"] <= 0:
                trend_score = 0.0
                momentum = "steady"
            else:
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
                "avg_views_per_day": round(bucket["total_velocity"] / max(bucket["mentions"], 1), 1) if bucket["mentions"] else 0.0,
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

    def _pick_primary_term(self, matched_terms: List[str]) -> str:
        priority_rank = {term: idx for idx, term in enumerate(self.TERM_PRIORITY)}
        return sorted(
            matched_terms,
            key=lambda term: (priority_rank.get(term, len(self.TERM_PRIORITY)), term.lower())
        )[0]

    def _match_seed_spec(self, spec: Dict[str, Any], video: Dict[str, Any]) -> bool:
        blob = self._normalize_text(
            f"{video.get('title', '')} {video.get('description', '')} {video.get('channel', '')}"
        )
        if any(re.search(pattern, blob) for pattern in spec.get("patterns", [])):
            return True
        token_groups = spec.get("token_groups", [])
        return bool(token_groups) and all(
            any(re.search(rf"\b{re.escape(token)}\b", blob) for token in group)
            for group in token_groups
        )

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
