from agents.base import BaseAgent
from agents.script_generation_utils import ScriptGenerationUtils
from agents.prompts import SCRIPTWRITER_SYSTEM, SCRIPTWRITER_QUALITY_GUIDE
import config

class ScriptAgent(BaseAgent):
    """Write complete video script with B-roll and effects"""

    def __init__(self, use_database: bool = False, ai_model: str = None):
        super().__init__(use_database=use_database, ai_model=ai_model)
        self.model = ai_model or config.SCRIPT_MODEL

    def _build_web_research_handoff_text(self, selected_title: str = None, selected_topics: list = None,
                                         research_packet: dict = None) -> str:
        """Render the web-selected research handoff as a prompt section."""
        if not (selected_title or selected_topics or research_packet):
            return ""

        lines = ["WEB RESEARCH HANDOFF (treat this as the source of truth):"]

        if selected_title:
            lines.append(f"- Chosen title: {selected_title}")

        if selected_topics:
            lines.append("- Chosen topics:")
            for item in selected_topics:
                if isinstance(item, dict):
                    label = item.get("title") or item.get("name") or item.get("text") or str(item)
                else:
                    label = str(item)
                lines.append(f"  - {label}")

        if research_packet and isinstance(research_packet, dict):
            summary = research_packet.get("research_summary", {})
            supporting_material = research_packet.get("supporting_material", [])
            if summary:
                lines.append("- Research summary:")
                if summary.get("main_discussion"):
                    lines.append(f"  - Main discussion: {summary.get('main_discussion')}")
                if summary.get("recommended_story_spine"):
                    lines.append(f"  - Recommended story spine: {summary.get('recommended_story_spine')}")
                for point in summary.get("strongest_evidence", [])[:5]:
                    lines.append(f"  - Evidence: {point}")
            if supporting_material:
                lines.append("- Supporting material:")
                for item in supporting_material[:5]:
                    lines.append(
                        f"  - {item.get('title', '')} ({item.get('source', '')}) {item.get('url', '')}".rstrip()
                    )

        return "\n".join(lines)

    def run(self, topic: str, angles: list, hook: dict, trailer: dict,
            structure: dict, research_insights: dict, notes: str, outro: str = None,
            regeneration_feedback: dict = None, previous_script: str = None,
            duration: int = None, youtube_sources: list = None,
            selected_title: str = None, selected_topics: list = None,
            research_packet: dict = None,
            selected_hook_script: str = None,
            talking_points: dict = None,
            shorts_segments: list = None,
            selected_thumbnail: dict = None) -> str:
        """
        Generate complete word-for-word script.

        Args:
            topic: Video topic
            angles: List of selected angles
            hook: Selected hook
            trailer: Selected trailer/intro
            structure: Content structure with engagement devices
            research_insights: Web research insights from WebSearchAgent
            notes: User's rough notes
            outro: Optional outro text
            regeneration_feedback: Feedback from previous regeneration attempt
            previous_script: Previous script for improvement
            duration: Target duration in minutes (defaults to config.DEFAULT_SCRIPT_DURATION)
            youtube_sources: List of YouTube outlier sources for citation

        Returns:
            Complete script with production notes section at end
        """
        # Set default duration
        if duration is None:
            duration = config.DEFAULT_SCRIPT_DURATION

        print(f"[*] ScriptAgent writing complete script (target: {duration} min)...")

        script = self._write_script(topic, angles, hook, trailer, structure, research_insights, notes, outro,
                                    regeneration_feedback, previous_script, duration, youtube_sources,
                                    selected_title, selected_topics, research_packet,
                                    selected_hook_script, talking_points, shorts_segments, selected_thumbnail)

        word_count = len(script.split())
        estimated_duration = word_count / config.SCRIPT_WORDS_PER_MINUTE
        print(f"[+] Script complete ({word_count} words, ~{estimated_duration:.1f} min)")
        return script

    def _write_script(self, topic, angles, hook, trailer, structure, research_insights, notes, outro,
                     regeneration_feedback, previous_script, duration, youtube_sources,
                     selected_title, selected_topics, research_packet,
                     selected_hook_script=None, talking_points=None, shorts_segments=None,
                     selected_thumbnail=None) -> str:
        """Generate full script with duration control and source citations"""

        import json

        # Calculate target word count based on duration
        target_words = duration * config.SCRIPT_WORDS_PER_MINUTE

        # Build regeneration feedback section
        regeneration_section = ""
        if regeneration_feedback and previous_script:
            regeneration_section = ScriptGenerationUtils.build_regeneration_section(
                previous_script=previous_script,
                previous_scores=regeneration_feedback['category_scores'],
                improvement_suggestions=regeneration_feedback.get('improvement_suggestions', []),
                previous_overall_score=regeneration_feedback.get('previous_score')
            )
        elif regeneration_feedback:
            low_scores = {k: v for k, v in regeneration_feedback['category_scores'].items() if v < 8}
            regeneration_section = f"""
REGENERATION: Previous script scored {regeneration_feedback['previous_score']}/100.
Fix these: {json.dumps(low_scores)}
Suggestions: {'; '.join(regeneration_feedback['improvement_suggestions'])}
"""

        # Build YouTube sources with actual URLs
        youtube_sources_text = ""
        if youtube_sources and len(youtube_sources) > 0:
            youtube_sources_text = "\nYouTube videos analyzed (reference by number [1], [2], etc.):\n"
            for i, source in enumerate(youtube_sources[:10], 1):
                url = source.get('url', '')
                youtube_sources_text += f"{i}. \"{source['title']}\" by {source['channel']} ({source['views']:,} views) - {url}\n"

        # Build structure context as readable text, not raw JSON
        structure_text = ""
        structured_subtopics = structure.get('structured_subtopics', [])
        if structured_subtopics:
            structure_text = "Content flow:\n"
            for i, sub in enumerate(structured_subtopics, 1):
                title = sub.get('title', '') if isinstance(sub, dict) else str(sub)
                desc = sub.get('description', '') if isinstance(sub, dict) else ''
                structure_text += f"{i}. {title}"
                if desc:
                    structure_text += f" - {desc}"
                structure_text += "\n"

        # Add engagement devices as readable text
        curiosity_gaps = structure.get('curiosity_gaps', [])
        open_loops = structure.get('open_loops', [])
        if curiosity_gaps or open_loops:
            structure_text += "\nEngagement devices to weave in:\n"
            for gap in curiosity_gaps:
                structure_text += f"- Curiosity gap: \"{gap.get('text', '')}\" ({gap.get('placement', '')})\n"
            for loop in open_loops:
                structure_text += f"- Open loop: \"{loop.get('setup', '')}\" (payoff at: {loop.get('payoff_at', '')})\n"

        # Build research insights as readable text
        research_text = ""
        if research_insights and isinstance(research_insights, dict):
            for subtopic_name, insights in research_insights.items():
                if insights:
                    research_text += f"\nResearch on '{subtopic_name}':\n"
                    if isinstance(insights, list):
                        for insight in insights[:3]:
                            if isinstance(insight, dict):
                                research_text += f"- {insight.get('text', '')} (Source: {insight.get('source_title', '')})\n"
                            else:
                                research_text += f"- {insight}\n"
                    else:
                        research_text += f"- {insights}\n"

        research_handoff_text = self._build_web_research_handoff_text(
            selected_title=selected_title,
            selected_topics=selected_topics,
            research_packet=research_packet,
        )

        # Build talking points blueprint when provided from Hooks & Talking Points step
        talking_points_text = ""
        if talking_points and isinstance(talking_points, dict):
            sections = talking_points.get("sections", [])
            if sections:
                lines = ["APPROVED TALKING POINTS OUTLINE (follow this structure exactly):"]
                for sec in sections:
                    lines.append(f"\n## {sec.get('title', 'Section')}")
                    for sub in sec.get("subsections", []):
                        lines.append(f"  ### {sub.get('title', 'Subsection')}")
                        for b in sub.get("bullets", []):
                            lines.append(f"    - {b}")
                talking_points_text = "\n".join(lines)

        hook_open = selected_hook_script or hook.get('text', '')
        outro_text = outro or "Ask viewers to subscribe, comment with questions, and mention consulting services if relevant to speaker's notes."

        # Build thumbnail context section
        thumbnail_context = ""
        if selected_thumbnail and isinstance(selected_thumbnail, dict):
            thumbnail_context = (
                "THUMBNAIL CONCEPT (use this to align the hook's visual language and opening energy):\n"
                f"  Visual: {selected_thumbnail.get('visual_concept', '')}\n"
                f"  Text overlay: {selected_thumbnail.get('text_overlay', '')}\n"
                f"  Color/mood: {selected_thumbnail.get('color_scheme', '')}\n"
                f"  Emotion target: {selected_thumbnail.get('emotion_target', '')}"
            )

        # Build transcript grounding section from outlier video excerpts
        transcript_grounding = ""
        if youtube_sources:
            lines = ["OUTLIER VIDEO TRANSCRIPTS (ground your examples, data points, and stories in these real videos):"]
            for i, src in enumerate(youtube_sources[:8], 1):
                title = src.get("title", f"Video {i}")
                views = src.get("views", 0)
                excerpt = src.get("transcript_excerpt", "").strip()
                subtopics = src.get("subtopics_covered", "").strip()
                insights = src.get("reusable_insights", "").strip()
                lines.append(f"\n--- Video {i}: \"{title}\" ({views:,} views)")
                if subtopics:
                    lines.append(f"Subtopics covered: {subtopics}")
                if insights:
                    lines.append(f"Reusable insights: {insights}")
                if excerpt:
                    lines.append(f"Transcript excerpt:\n{excerpt[:1500]}")
                lines.append("---")
            transcript_grounding = "\n".join(lines)

        # Build shorts segments guide from HTP output
        shorts_guide = ""
        if shorts_segments:
            lines = [f"SHORTS TO EXTRACT ({len(shorts_segments)} planned — embed these in the main script using [SHORT START]/[SHORT END] markers):"]
            for i, seg in enumerate(shorts_segments, 1):
                lines.append(f"\nShort {i}: \"{seg.get('title', '')}\"")
                lines.append(f"  Source section: {seg.get('source_section', '')}")
                lines.append(f"  Opening hook: {seg.get('hook_line', '')}")
                lines.append(f"  Script: {seg.get('script', '')[:500]}")
            shorts_guide = "\n".join(lines)
        else:
            shorts_guide = "SHORTS: Include 2-3 self-contained [SHORT START: \"Title\"] ... [SHORT END] segments within the main script."

        # Load checklist
        checklist_text = json.dumps({
            "Hook": ["Grabs attention in 3-5 seconds", "Creates curiosity gap", "Relevant to topic"],
            "Structure": ["Clear flow", "Smooth section transitions", "Curiosity gaps placed strategically", "Payoffs delivered", "Strong conclusion"],
            "Content": ["Factually accurate", "Easy to understand", "Value-dense", "No fluff", "No repetitions"],
            "Engagement": ["Pattern interrupts every 60 seconds", "Open loops resolved", "Maintains energy", "Optimized for retention", "Social proof elements"],
            "Production": ["B-roll suggestions clear", "SFX appropriate", "Pacing varies"],
            "CTA": ["Clear call-to-action", "Natural placement", "Compelling reason"],
        }, indent=2)
        try:
            import os as _os
            checklist_path = _os.path.join(_os.path.dirname(_os.path.dirname(__file__)), "checklists", "script_checklist.json")
            with open(checklist_path) as _f:
                checklist_text = _f.read()
        except Exception:
            pass

        prompt = f"""Write a complete, word-for-word YouTube script for "{topic}".

CONSTRAINTS:
- Duration: HARD MAXIMUM {duration} minutes (~{target_words} words of spoken content)
- Audience: Business professionals
- Reading level: 10th grade — short sentences, concrete examples, zero jargon
- Shorts: 2-3 self-contained clips must be embeddable using [SHORT START]/[SHORT END] markers

FINAL VIDEO TITLE:
{selected_title or topic}

THE CREATOR'S NOTES (write in THEIR voice — preserve their stories, examples, and personality):
{notes or "None provided."}

HOOK / OPENING (use this word-for-word as your opening — do NOT rewrite it):
{hook_open}

{thumbnail_context}

{talking_points_text if talking_points_text else structure_text}

{transcript_grounding}

{shorts_guide}

{research_handoff_text}
{youtube_sources_text}
OUTRO (use this word-for-word):
{outro_text}
{regeneration_section}

QUALITY CHECKLIST (every section must satisfy these — score yourself against each category before finishing):
{checklist_text}

SCRIPT FORMAT:
- Section headers with timestamps: "## SECTION TITLE (0:00)"
- [SHORT START: "Short Title"] ... [SHORT END] — each short must be 60 seconds max, fully self-contained (no "as I mentioned")
- Energy markers: [ENERGY: HIGH/MEDIUM/LOW]
- Pattern interrupt every ~60 seconds: [PATTERN INTERRUPT: camera switch / text overlay / pause]
- B-roll inline: [B-ROLL: description]
- After the complete spoken script, add these SEPARATE sections (not spoken):
  1. SHORTS SUMMARY — title, hook, why it works as a short
  2. PRODUCTION NOTES — B-roll, SFX, camera directions

Keep production notes and shorts summary OUT of the spoken script body — append them at the end only."""

        try:
            return ScriptGenerationUtils.call_litellm(prompt, model=self.model,
                                                       system_prompt=SCRIPTWRITER_SYSTEM)
        except Exception as e:
            print(f"[!] Script generation failed: {e}")
            print(f"[*] Using fallback script generator...")
            return self._generate_fallback_script(topic, hook, trailer, structure, outro, youtube_sources)

    def _generate_fallback_script(self, topic, hook, trailer, structure, outro, youtube_sources=None) -> str:
        """Generate basic script if API fails"""
        script = f"""[00:00] {hook['text']}
[SFX: intro music]

[00:05] {trailer['text']}
[B-ROLL: Title card with topic "{topic}"]

[00:20] Let me break this down for you.
[B-ROLL: Animated list appearing]

"""

        # Add subtopics
        time_offset = 30
        subtopics = structure.get('structured_subtopics', [])

        for i, subtopic in enumerate(subtopics, 1):
            mins = time_offset // 60
            secs = time_offset % 60

            script += f"""[{mins:02d}:{secs:02d}] First, let's talk about {subtopic.get('title', f'point {i}')}.
[B-ROLL: Show relevant visuals]

{subtopic.get('description', 'Important concept here.')}
[PAUSE]

"""
            time_offset += 60

        # Add outro
        mins = time_offset // 60
        secs = time_offset % 60
        script += f"""[{mins:02d}:{secs:02d}] {outro or "Thanks for watching! Like and subscribe for more."}
[B-ROLL: End screen with subscribe button]
[SFX: outro music]

## SOURCES & REFERENCES

"""

        # Add YouTube sources if available
        if youtube_sources:
            script += "\n### YouTube Outliers Analyzed:\n"
            for i, source in enumerate(youtube_sources[:10], 1):
                script += f"{i}. \"{source['title']}\" by {source['channel']} - {source['url']}\n"

        return script
