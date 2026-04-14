from __future__ import annotations

import glob
import json
import os
import re
import subprocess
import sys
import tempfile
from typing import Any, Dict, List, Optional

import litellm
import requests

import config
from agents.base import BaseAgent, parse_json_response
from agents.prompts import RESEARCH_SYSTEM
from youtube_utils import YouTubeUtility

try:
    from youtube_transcript_api import YouTubeTranscriptApi
except ImportError:  # pragma: no cover - optional dependency
    YouTubeTranscriptApi = None


class ResearcherAgent(BaseAgent):
    """Synthesize transcripts and social discussion into script-ready research options."""

    def __init__(self, use_database: bool = False, ai_model: str = None):
        super().__init__(use_database=use_database, ai_model=ai_model)
        self.model = ai_model or config.RESEARCH_MODEL
        self.google_api_key = os.getenv("GOOGLE_SEARCH_API_KEY")
        self.search_engine_id = os.getenv("GOOGLE_SEARCH_ENGINE_ID")

    def run(
        self,
        topic: str,
        videos: Optional[List[Dict[str, Any]]] = None,
        theme_data: Optional[Dict[str, Any]] = None,
        custom_links: str = "",
        custom_notes: str = "",
    ) -> Dict[str, Any]:
        source_videos = videos or []
        transcript_sources = [self._build_transcript_source(video) for video in source_videos[:10]]
        discussions = self._search_discussions(topic, theme_data=theme_data or {})
        notes = (custom_notes or "").strip()
        synthesized = self._synthesize(
            topic,
            transcript_sources,
            discussions,
            notes,
        )
        synthesized["topic"] = topic
        synthesized["video_count"] = len(source_videos)
        synthesized["transcript_sources"] = transcript_sources
        synthesized["discussion_sources"] = discussions
        synthesized["custom_notes"] = notes
        synthesized["research_packet"] = {
            "topic": topic,
            "transcript_sources": transcript_sources,
            "discussion_sources": discussions,
            "custom_notes": notes,
        }
        return synthesized

    def _build_transcript_source(self, video: Dict[str, Any]) -> Dict[str, Any]:
        title = video.get("title")
        url = video.get("url")
        transcript_excerpt = self._fetch_transcript_excerpt(url)
        # Fall back to description if transcript is unavailable (e.g. IP block)
        if not transcript_excerpt:
            description = video.get("description", "") or ""
            if not description and url:
                # Fetch full metadata — flat search results don't include description
                try:
                    details = YouTubeUtility.get_video_details(url)
                    description = details.get("description", "") or ""
                except Exception:
                    pass
            transcript_excerpt = description[:2500].strip()
        return {
            "title": title,
            "url": url,
            "channel": video.get("channel"),
            "views": video.get("views"),
            "ratio": video.get("ratio"),
            "transcript_excerpt": transcript_excerpt,
            # Pre-analyzed AI insights — used directly when available
            "success_criteria": video.get("success_criteria", ""),
            "subtopics_covered": video.get("subtopics_covered", ""),
            "reusable_insights": video.get("reusable_insights", ""),
            "ultimate_titles": video.get("ultimate_titles", ""),
            "alternate_hooks": video.get("alternate_hooks", ""),
        }

    def _fetch_transcript_excerpt(self, video_url: Optional[str]) -> str:
        video_id = YouTubeUtility._extract_video_id(video_url)
        if not video_id:
            return ""

        # Try youtube_transcript_api first (with optional cookie support)
        if YouTubeTranscriptApi is not None:
            cookies_file = os.getenv("YOUTUBE_COOKIES_FILE", "").strip() or None
            try:
                api_kwargs: Dict[str, Any] = {}
                if cookies_file and os.path.isfile(cookies_file):
                    api_kwargs["cookies"] = cookies_file
                api = YouTubeTranscriptApi(**api_kwargs)
                for lang_opts in (["en", "en-US", "en-GB"], None):
                    try:
                        if lang_opts is not None:
                            fetched = api.fetch(video_id, languages=lang_opts)
                        else:
                            fetched = api.fetch(video_id)
                        snippets = list(fetched)[:30]
                        parts = [s.text.strip() for s in snippets if s.text and s.text.strip()]
                        text = " ".join(parts)[:2500]
                        if text:
                            return text
                    except Exception:
                        continue
            except Exception:
                pass  # Fall through to yt-dlp

        # Fallback: use yt-dlp to download auto-generated subtitles
        return self._fetch_transcript_via_ytdlp(video_id)

    def _fetch_transcript_via_ytdlp(self, video_id: str) -> str:
        """Download subtitles via yt-dlp as a fallback for IP-blocked transcript API."""
        url = f"https://www.youtube.com/watch?v={video_id}"
        cookies_file = os.getenv("YOUTUBE_COOKIES_FILE", "").strip() or None
        cookies_browser = os.getenv("YOUTUBE_COOKIES_BROWSER", "").strip() or None

        with tempfile.TemporaryDirectory() as tmpdir:
            out_template = os.path.join(tmpdir, "sub_%(id)s.%(ext)s")
            base_cmd = [
                sys.executable, "-m", "yt_dlp",
                "--skip-download",
                "--write-auto-subs",
                "--write-subs",
                "--sub-lang", "en",
                "--sub-format", "vtt",
                "--quiet",
                "--no-warnings",
                "-o", out_template,
                url,
            ]
            # Build cookie variants to try in order
            cookie_variants: List[List[str]] = []
            if cookies_file and os.path.isfile(cookies_file):
                cookie_variants.append(["--cookies", cookies_file])
            if cookies_browser:
                cookie_variants.append(["--cookies-from-browser", cookies_browser])
            # Always try without cookies last (may work on non-blocked IPs)
            cookie_variants.append([])

            for cookie_args in cookie_variants:
                try:
                    cmd = base_cmd[:-1] + cookie_args + [url]
                    subprocess.run(cmd, capture_output=True, text=True, timeout=45)
                    vtt_files = glob.glob(os.path.join(tmpdir, "*.vtt"))
                    if not vtt_files:
                        continue
                    with open(vtt_files[0], "r", encoding="utf-8", errors="ignore") as f:
                        raw = f.read()
                    result = self._parse_vtt(raw)
                    if result:
                        return result
                except Exception:
                    continue
        return ""

    @staticmethod
    def _parse_vtt(raw: str) -> str:
        """Extract plain text from a VTT subtitle file, deduplicating repeated lines."""
        lines: List[str] = []
        seen: set = set()
        for line in raw.splitlines():
            line = line.strip()
            if not line or line.startswith("WEBVTT") or "-->" in line or re.match(r"^\d+$", line):
                continue
            # Strip VTT tags like <c>, <00:00:00.000>
            line = re.sub(r"<[^>]+>", "", line).strip()
            if line and line not in seen:
                seen.add(line)
                lines.append(line)
            if len(lines) >= 60:
                break
        return " ".join(lines)[:2500]

    def _parse_custom_sources(self, custom_links: Optional[str]) -> List[Dict[str, Any]]:
        if not custom_links:
            return []

        sources: List[Dict[str, Any]] = []
        url_pattern = re.compile(r"https?://[^\s\])>\"']+")

        for raw_line in custom_links.splitlines():
            line = raw_line.strip()
            if not line:
                continue

            line = re.sub(r"^[\-\*\u2022]\s*", "", line)
            line = re.sub(r"^\d+[\.\)]\s*", "", line)
            match = url_pattern.search(line)
            if not match:
                continue

            url = match.group(0).rstrip(".,;")
            label = ""

            if "|" in line:
                left, right = [part.strip() for part in line.split("|", 1)]
                if url in right:
                    label = left
                else:
                    label = right or left
            else:
                label = line.replace(url, "").strip(" -:") or url

            sources.append(
                {
                    "title": label or url,
                    "label": label,
                    "url": url,
                    "raw": raw_line.strip(),
                }
            )

        return sources

    def _search_discussions(self, topic: str, theme_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        if not self.google_api_key or not self.search_engine_id:
            return []

        # Use topic only — adding open_gaps/viewer_desires bloats the query and returns off-topic results
        queries = [
            ("Reddit", f'"{topic}" site:reddit.com'),
            ("X", f'"{topic}" (site:x.com OR site:twitter.com)'),
        ]

        # ALL meaningful topic words must appear (not just one) to prevent weak matches
        topic_keywords = [w.lower() for w in re.split(r'\W+', topic) if len(w) >= 4]

        discussions: List[Dict[str, Any]] = []
        seen_urls = set()
        for source_name, query in queries:
            count = 0
            for item in self._google_search(query, num_results=8):
                if count >= 3:
                    break
                url = item.get("url")
                if not url or url in seen_urls:
                    continue
                # Require ALL topic keywords to appear (not just one)
                text = f"{item.get('title', '')} {item.get('snippet', '')}".lower()
                if topic_keywords and not all(kw in text for kw in topic_keywords):
                    continue
                seen_urls.add(url)
                discussions.append({
                    "source": source_name,
                    "title": item.get("title"),
                    "url": url,
                    "snippet": item.get("snippet"),
                })
                count += 1
        return discussions

    def _google_search(self, query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": self.google_api_key,
            "cx": self.search_engine_id,
            "q": query,
            "num": min(num_results, 10),
            "dateRestrict": "m3",
        }
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            return [
                {
                    "title": item.get("title"),
                    "url": item.get("link"),
                    "snippet": item.get("snippet"),
                }
                for item in data.get("items", [])
            ]
        except Exception:
            return []

    @staticmethod
    def _parse_subtopic_bullets(raw: str) -> List[str]:
        """Parse a bullet-point subtopics string into a list of clean strings."""
        items: List[str] = []
        for line in re.split(r'\n', raw or ""):
            item = re.sub(r'^[\s•·\-\*]+', '', line).strip()
            if len(item) >= 5:
                items.append(item)
        return items

    def _build_cross_video_map(self, transcript_sources: List[Dict[str, Any]]) -> str:
        """Build a per-video content map combining pre-analyzed subtopics + raw transcript excerpts."""
        lines: List[str] = []
        for i, src in enumerate(transcript_sources, 1):
            title = src.get("title", f"Video {i}")
            ratio = src.get("ratio", 0)
            bullets = self._parse_subtopic_bullets(src.get("subtopics_covered", ""))
            excerpt = (src.get("transcript_excerpt") or "").strip()

            # Skip completely empty entries
            if not bullets and not excerpt:
                continue

            lines.append(f"\nVideo {i} ({ratio:.1f}x outlier): \"{title}\"")
            if bullets:
                lines.append("  Pre-analyzed subtopics:")
                for b in bullets:
                    lines.append(f"    • {b}")
            if excerpt:
                # Provide enough content for granular extraction without overwhelming the prompt
                lines.append("  Raw transcript/description (extract specific subtopics from this):")
                for chunk_line in excerpt[:1200].splitlines():
                    stripped = chunk_line.strip()
                    if stripped:
                        lines.append(f"    {stripped}")
        return "\n".join(lines)

    def _synthesize(
        self,
        topic: str,
        transcript_sources: List[Dict[str, Any]],
        discussions: List[Dict[str, Any]],
        custom_notes: str = "",
    ) -> Dict[str, Any]:

        proven_titles_list = "\n".join(
            f"  {i+1}. \"{s['title']}\" ({s.get('ratio', 0):.1f}x outlier)"
            for i, s in enumerate(transcript_sources)
        )

        cross_video_map = self._build_cross_video_map(transcript_sources)

        # Pass hook/insight data for title generation
        title_context = [
            {
                "proven_title": s["title"],
                "ratio": s.get("ratio", 0),
                "title_ideas": s.get("ultimate_titles", ""),
                "success_criteria": s.get("success_criteria", ""),
            }
            for s in transcript_sources
            if s.get("title")
        ]

        discussion_summary = ""
        if discussions:
            discussion_summary = f"""
AUDIENCE PULSE — REDDIT / X (use only for research_summary, NOT for titles or topics):
{json.dumps(discussions, indent=2)}
"""

        prompt = f"""
You are analyzing proven outlier YouTube videos to extract the best titles and topics for a new video about "{topic}".

═══ PROVEN OUTLIER TITLES (ranked by performance) ═══
{proven_titles_list}

═══ TITLE GENERATION CONTEXT (per-video success signals) ═══
{json.dumps(title_context, indent=2)}

═══ VIDEO CONTENT MAP (primary source for high_level_topics — use BOTH pre-analyzed subtopics AND raw transcript excerpts) ═══
{cross_video_map if cross_video_map else json.dumps([{"title": s["title"], "subtopics_covered": s.get("subtopics_covered", "")} for s in transcript_sources], indent=2)}
{discussion_summary}
USER NOTES:
{custom_notes or "None"}

Return this exact JSON:
{{
  "best_titles": [
    {{
      "title": "Adaptation of a proven outlier title — copy its format/angle, never invent from scratch",
      "thumbnails": [
        {{
          "visual_concept": "2-sentence description of what's visually shown — who/what is in frame, layout, any graphic elements",
          "text_overlay": "BOLD TEXT ≤5 WORDS",
          "color_scheme": "e.g. dark navy background, bright orange text",
          "emotion_target": "curiosity | shock | FOMO | aspiration | relief"
        }},
        {{
          "visual_concept": "Alternative thumbnail concept for the same title",
          "text_overlay": "DIFFERENT SHORT TEXT",
          "color_scheme": "contrasting option",
          "emotion_target": "different emotion"
        }}
      ]
    }},
    {{ "title": "...", "thumbnails": [{{}}, {{}}] }},
    {{ "title": "...", "thumbnails": [{{}}, {{}}] }},
    {{ "title": "...", "thumbnails": [{{}}, {{}}] }},
    {{ "title": "...", "thumbnails": [{{}}, {{}}] }}
  ],
  "high_level_topics": [
    {{
      "topic": "Concise topic name (3-6 words max)",
      "subtopics": ["specific subtopic from the video data", "another specific subtopic", "third specific subtopic"],
      "video_count": 3,
      "priority_score": 9
    }},
    ... at least 9 more ...
  ],
  "research_summary": {{
    "main_discussion": "What the proven outlier titles and subtopics show viewers actually care about",
    "strongest_evidence": ["cite specific outlier title + ratio", "cite specific subtopic pattern"],
    "recommended_story_spine": "How the script should flow based on what worked in the outliers"
  }}
}}

HARD RULES:
- best_titles: EXACTLY 5. Each title MUST be a direct adaptation of a proven outlier title — same format, same angle pattern. No generic titles.
- thumbnails: EXACTLY 2 per title. Visual concepts must be specific to that title's angle, not generic. Text overlay must be punchy, ≤5 words, ALL CAPS.
- high_level_topics: AT LEAST 10. Sort by video_count descending (topics in more videos first).
- video_count: count how many different videos in the content map mention this topic (semantic match — "setup" and "installation" are the same topic).
- subtopics: 3-5 SPECIFIC bullet points. Pull these from the raw transcript excerpts first — look for exact numbers, tool names, comparisons, step names, and concrete details (e.g. "$3/day vs $100/day", "checkpoint every 15 tool calls", "memory.md + SQLite session db"). Pre-analyzed bullets are a fallback only.
- high_level_topics MUST come from actual video content — do NOT invent topics or use generic descriptions.
- Do NOT use Reddit/X for titles or topics.
- User notes are supplementary only.
"""

        try:
            response = litellm.completion(
                model=self.model,
                messages=[
                    {"role": "system", "content": RESEARCH_SYSTEM},
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
                timeout=config.DEFAULT_API_TIMEOUT,
            )
            return parse_json_response(response.choices[0].message.content)
        except Exception as e:
            return {
                "best_titles": [],
                "high_level_topics": [],
                "research_summary": {
                    "main_discussion": f"Research synthesis failed: {e}" + (f" User notes: {custom_notes}" if custom_notes else ""),
                    "strongest_evidence": [],
                    "recommended_story_spine": "Review the selected outlier videos directly as fallback.",
                },
                "custom_notes": custom_notes,
            }
