import json
import litellm
import warnings
from typing import Dict, Any
from rich import print
import config
from youtube_utils import YouTubeUtility
from agents.base import BaseAgent
from agents.prompts import RESEARCH_SYSTEM

# Silence Pydantic serialization warnings from LiteLLM/Pydantic v2
warnings.filterwarnings("ignore", message="Expected `Union\[Choices, StreamingChoices\]` but got `Choices`", module="pydantic")

class InsightAgent(BaseAgent):
    """Agent that performs deep AI analysis on a specific video."""

    def __init__(self, use_database: bool = False, ai_model: str = None):
        """Initialize InsightAgent with optional database support and AI model."""
        super().__init__(use_database=use_database, ai_model=ai_model)
        self.model = ai_model or config.RESEARCH_MODEL

    def run(self, video_data: Dict[str, Any]) -> Dict[str, Any]:
        url = video_data.get('url')
        print(f"[*] InsightAgent analyzing with {self.model}: {video_data.get('title')}...")
        
        details = YouTubeUtility.get_video_details(url)
        title = details.get('title', video_data.get('title'))
        description = details.get('description', '')[:2000] # Limit context size
        
        prompt = f"""
        Analyze the following YouTube video content to extract viral mechanics and content ideas.

        Video Title: {title}
        Description: {description}

        Provide the following in a JSON format:
        1. "success_criteria": Why did this video perform significantly better than average?
        2. "reusable_insights": 1-2 core principles or information nuggets from the video.
        3. "ultimate_titles": 2-3 higher-CTR alternative titles.
        4. "alternate_hooks": 2 different ways to start this video to maximize retention.
        5. "subtopics_covered": List the key topics and subtopics covered in this video as bullet points (use • for bullets).

        JSON Structure:
        {{
            "success_criteria": "string",
            "reusable_insights": "string",
            "ultimate_titles": "string",
            "alternate_hooks": "string",
            "subtopics_covered": "• Topic 1\\n• Subtopic A\\n• Subtopic B\\n• Topic 2"
        }}
        """
        
        try:
            response = litellm.completion(
                model=self.model,
                messages=[
                    {"role": "system", "content": RESEARCH_SYSTEM},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                timeout=30
            )
            content = response.choices[0].message.content
            analysis = json.loads(content)
            
            # Map back to standard structure
            return {
                'title': title,
                'url': url,
                'success_criteria': analysis.get('success_criteria', 'N/A'),
                'reusable_insights': analysis.get('reusable_insights', 'N/A'),
                'ultimate_titles': analysis.get('ultimate_titles', 'N/A'),
                'alternate_hooks': analysis.get('alternate_hooks', 'N/A'),
                'subtopics_covered': analysis.get('subtopics_covered', 'N/A')
            }
        except Exception as e:
            print(f"[!] AI Analysis failed: {e}")
            return {
                'title': title,
                'url': url,
                'success_criteria': "Analysis failed",
                'reusable_insights': str(e),
                'ultimate_titles': "N/A",
                'alternate_hooks': "N/A",
                'subtopics_covered': "N/A"
            }
