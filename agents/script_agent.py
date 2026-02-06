from agents.base import BaseAgent
from agents.script_generation_utils import ScriptGenerationUtils
from agents.prompts import SCRIPTWRITER_SYSTEM, SCRIPTWRITER_QUALITY_GUIDE
import config

class ScriptAgent(BaseAgent):
    """Write complete video script with B-roll and effects"""

    def __init__(self, use_database: bool = False, ai_model: str = None):
        super().__init__(use_database=use_database, ai_model=ai_model)
        self.model = ai_model or config.SCRIPT_MODEL

    def run(self, topic: str, angles: list, hook: dict, trailer: dict,
            structure: dict, research_insights: dict, notes: str, outro: str = None,
            regeneration_feedback: dict = None, previous_script: str = None,
            duration: int = None, youtube_sources: list = None) -> str:
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
                                    regeneration_feedback, previous_script, duration, youtube_sources)

        word_count = len(script.split())
        estimated_duration = word_count / config.SCRIPT_WORDS_PER_MINUTE
        print(f"[+] Script complete ({word_count} words, ~{estimated_duration:.1f} min)")
        return script

    def _write_script(self, topic, angles, hook, trailer, structure, research_insights, notes, outro,
                     regeneration_feedback, previous_script, duration, youtube_sources) -> str:
        """Generate full script with duration control and source citations"""

        import json

        # Calculate target word count based on duration
        target_words = duration * config.SCRIPT_WORDS_PER_MINUTE

        # Build angles text
        angles_text = "\n".join([
            f"- {a['angle_name']}: {a['description']}"
            for a in angles
        ])

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

        prompt = f"""Write a complete, word-for-word YouTube script for "{topic}".

CONSTRAINTS:
- Duration: {duration} minutes (~{target_words} words of spoken content)
- Audience: Business professionals
- Reading level: 10th grade (short sentences, clear examples, no jargon)

THE SPEAKER'S NOTES (write in THEIR voice — preserve their stories, examples, and personality):
{notes}

ANGLES TO BLEND:
{angles_text}

HOOK (open with this): {hook['text']}
INTRO (after hook): {trailer['text']}

{structure_text}
{research_text}
{youtube_sources_text}
OUTRO: {outro or "Ask viewers to subscribe, comment with questions, and mention consulting services if relevant to speaker's notes."}
{regeneration_section}
{SCRIPTWRITER_QUALITY_GUIDE}

SCRIPT FORMAT:
Write the script as the speaker would actually say it. Use section headers with timestamps (e.g., "HOOK (0:00-0:08)").

After the complete spoken script, add these SEPARATE sections at the end:
1. KEY URL SUGGESTIONS FOR B-ROLL - specific URLs and stock footage search terms
2. PRODUCTION NOTES - B-roll suggestions, SFX cues, camera directions, pacing notes, pattern interrupts

Keep production notes OUT of the spoken script body — they go at the end only."""

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
