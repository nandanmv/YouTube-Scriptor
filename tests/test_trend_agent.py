import importlib.util
import sys
import types
import unittest
from unittest.mock import patch

from pathlib import Path

from youtube_utils import YouTubeUtility

ROOT = Path(__file__).resolve().parents[1]


def _load_module(module_name: str, path: Path):
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


if "agents" not in sys.modules:
    agents_pkg = types.ModuleType("agents")
    agents_pkg.__path__ = [str(ROOT / "agents")]
    sys.modules["agents"] = agents_pkg

_load_module("agents.base", ROOT / "agents" / "base.py")
trend_agent_module = _load_module("agents.trend_agent", ROOT / "agents" / "trend_agent.py")
TrendAgent = trend_agent_module.TrendAgent


class TrendAgentTests(unittest.TestCase):
    @patch("agents.trend_agent.config.TREND_MIN_VIEWS", 500)
    @patch("agents.trend_agent.config.TREND_MIN_VIEWS_PER_DAY", 50)
    @patch.object(YouTubeUtility, "search_recent")
    def test_custom_seed_mode_only_returns_requested_seed_labels(self, mock_search_recent):
        shared_video = {
            "id": "shared",
            "title": "Hermes agent tools for builders",
            "description": "Hermes agent tools and workflows",
            "channel": "Builder Lab",
            "view_count": 3600,
            "upload_date": "20260513",
        }
        claude_video = {
            "id": "claude-only",
            "title": "Claude Code setup guide",
            "description": "Claude Code for local coding",
            "channel": "Code Lab",
            "view_count": 22000,
            "upload_date": "20260513",
        }
        low_signal_video = {
            "id": "tiny",
            "title": "Hermes agent tiny demo",
            "description": "Hermes tools",
            "channel": "Tiny Lab",
            "view_count": 14,
            "upload_date": "20260513",
        }
        mock_search_recent.side_effect = [
            [shared_video, claude_video, low_signal_video],
            [shared_video, low_signal_video],
        ]

        agent = TrendAgent()
        result = agent.run(
            seeds=["hermes agent", "agent tools"],
            lookback_days=30,
            max_videos_per_seed=5,
            ai_only=True,
            max_terms=12,
        )

        labels = [item["term"] for item in result["terms"]]
        self.assertTrue(result["custom_seed_mode"])
        self.assertEqual(set(labels), {"Hermes Agent", "Agent Tools"})
        self.assertNotIn("Claude Code", labels)
        self.assertEqual(result["videos_analyzed"], 2)

        hermes_bucket = next(item for item in result["terms"] if item["term"] == "Hermes Agent")
        tools_bucket = next(item for item in result["terms"] if item["term"] == "Agent Tools")
        self.assertEqual(hermes_bucket["mentions"], 1)
        self.assertEqual(tools_bucket["mentions"], 1)
        self.assertEqual(hermes_bucket["sample_videos"][0]["id"], "shared")
        self.assertEqual(tools_bucket["sample_videos"][0]["id"], "shared")

    @patch("agents.trend_agent.config.TREND_MIN_VIEWS", 500)
    @patch("agents.trend_agent.config.TREND_MIN_VIEWS_PER_DAY", 50)
    @patch.object(YouTubeUtility, "search_recent")
    def test_whole_window_candidate_selection_prefers_stronger_older_video(self, mock_search_recent):
        older_strong = {
            "id": "older-strong",
            "title": "Hermes agent release recap",
            "description": "Hermes agent tooling",
            "channel": "Launch Channel",
            "view_count": 50000,
            "upload_date": "20260424",
        }
        newer_weaker = {
            "id": "newer-weaker",
            "title": "Hermes agent quick note",
            "description": "Hermes agent tooling",
            "channel": "Launch Channel",
            "view_count": 600,
            "upload_date": "20260513",
        }
        mock_search_recent.return_value = [older_strong, newer_weaker]

        agent = TrendAgent()
        result = agent.run(
            seeds=["hermes agent"],
            lookback_days=30,
            max_videos_per_seed=1,
            ai_only=True,
            max_terms=12,
        )

        bucket = result["terms"][0]
        self.assertEqual(bucket["sample_videos"][0]["id"], "older-strong")
        self.assertEqual(result["videos_analyzed"], 1)

    @patch("agents.trend_agent.config.TREND_MIN_VIEWS", 500)
    @patch("agents.trend_agent.config.TREND_MIN_VIEWS_PER_DAY", 50)
    @patch.object(YouTubeUtility, "search_recent")
    def test_default_mode_still_uses_global_taxonomy(self, mock_search_recent):
        mock_search_recent.side_effect = [
            [{
                "id": "hermes-video",
                "title": "Hermes Agent powered by local models",
                "description": "Hermes workflows",
                "channel": "Local AI Lab",
                "view_count": 3200,
                "upload_date": "20260513",
            }],
            [{
                "id": "claude-video",
                "title": "Claude Code v2 setup",
                "description": "Claude Code for teams",
                "channel": "Code Lab",
                "view_count": 24000,
                "upload_date": "20260513",
            }],
            [{
                "id": "workflow-video",
                "title": "AI workflow automation stack",
                "description": "AI workflow automation",
                "channel": "Ops Lab",
                "view_count": 12000,
                "upload_date": "20260513",
            }],
        ]

        agent = TrendAgent()
        result = agent.run(seeds=None, lookback_days=30, max_videos_per_seed=5, ai_only=True, max_terms=12)

        labels = {item["term"] for item in result["terms"]}
        self.assertFalse(result["custom_seed_mode"])
        self.assertIn("Hermes", labels)
        self.assertIn("Claude Code", labels)


class YouTubeUtilityPaginationTests(unittest.TestCase):
    @patch.object(YouTubeUtility, "_youtube_api_enabled", return_value=True)
    @patch.object(YouTubeUtility, "_youtube_api_get")
    def test_search_videos_api_paginates_beyond_fifty_results(self, mock_api_get, _mock_enabled):
        first_page = {
            "items": [{"id": {"videoId": f"video-{idx}"}} for idx in range(50)],
            "nextPageToken": "next-page",
        }
        second_page = {
            "items": [{"id": {"videoId": f"video-{idx}"}} for idx in range(50, 75)],
        }
        mock_api_get.side_effect = [first_page, second_page]

        rows = YouTubeUtility._search_videos_api("hermes agent", 75, order="date")

        self.assertEqual(len(rows), 75)
        self.assertEqual(mock_api_get.call_count, 2)
        first_params = mock_api_get.call_args_list[0].args[1]
        second_params = mock_api_get.call_args_list[1].args[1]
        self.assertEqual(first_params["maxResults"], 50)
        self.assertEqual(second_params["pageToken"], "next-page")
        self.assertEqual(second_params["maxResults"], 25)


if __name__ == "__main__":
    unittest.main()
