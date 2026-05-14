import os
from dotenv import load_dotenv

load_dotenv()

# --- CONFIGURATION ---
SEARCH_TERM = "claude code"
SEARCH_LIMIT = 50        # How many search results to analyze
SHORTS_SEARCH_MULTIPLIER = int(os.getenv("SHORTS_SEARCH_MULTIPLIER", "4"))  # Expand search pool for Shorts filtering
SHORTS_MAX_DURATION_SECONDS = int(os.getenv("SHORTS_MAX_DURATION_SECONDS", "70"))
SHORTS_APP_DEFAULT_LIMIT = int(os.getenv("SHORTS_APP_DEFAULT_LIMIT", "12"))

# --- RESEARCH STRATEGY ---
# Strategy for finding videos to analyze: "top_performers" or "outliers"
RESEARCH_STRATEGY = os.getenv("RESEARCH_STRATEGY", "outliers")

# Top Performers Settings (alternative strategy)
TOP_PERFORMERS_COUNT = int(os.getenv("TOP_PERFORMERS_COUNT", "10"))
TOP_PERFORMERS_RECENCY_MONTHS = int(os.getenv("TOP_PERFORMERS_RECENCY_MONTHS", "3"))  # Last 3 months
TOP_PERFORMERS_MIN_VIEWS = int(os.getenv("TOP_PERFORMERS_MIN_VIEWS", "5000"))  # Minimum 5K views

# Outlier Settings (DEFAULT strategy for 'create' command)
CHANNEL_HISTORY = 50     # How many recent videos to fetch per channel for baseline
MIN_MEDIAN_VIEWS = 500   # Ignore channels with very low median views (too much noise)
OUTLIER_THRESHOLD = 3.0  # Keep only outliers (>x average)
MAX_SUBSCRIBERS = 200000  # Only include channels with fewer than this many subscribers
INSIGHT_TOP_N = 10       # Number of top outliers to analyze with AI insights

# AI Configuration
# Per-task model configuration (optional - falls back to DEFAULT_MODEL)
DEFAULT_MODEL = os.getenv("AI_MODEL", os.getenv("DEFAULT_MODEL", "openai/gpt-4o"))
ANGLE_MODEL = os.getenv("ANGLE_MODEL", DEFAULT_MODEL)
RESEARCH_MODEL = os.getenv("RESEARCH_MODEL", DEFAULT_MODEL)
SCRIPT_MODEL = os.getenv("SCRIPT_MODEL", DEFAULT_MODEL)
QUALITY_MODEL = os.getenv("QUALITY_MODEL", DEFAULT_MODEL)

# Backward compatibility
AI_MODEL = DEFAULT_MODEL

# Quality Control
QUALITY_THRESHOLD = int(os.getenv("QUALITY_THRESHOLD", "90"))
MAX_REGENERATIONS = int(os.getenv("MAX_REGENERATIONS", "3"))
MAX_RESEARCH_ITERATIONS = int(os.getenv("MAX_RESEARCH_ITERATIONS", "3"))

# API Timeouts (in seconds)
SCRIPT_GENERATION_TIMEOUT = int(os.getenv("SCRIPT_GENERATION_TIMEOUT", "300"))  # 5 minutes for full scripts
DEFAULT_API_TIMEOUT = int(os.getenv("DEFAULT_API_TIMEOUT", "120"))  # 2 minutes for other API calls

# Quick Script Settings
QUICK_SCRIPT_READING_LEVEL = os.getenv("QUICK_SCRIPT_READING_LEVEL", "10th grade")
QUICK_SCRIPT_TARGET_AUDIENCE = os.getenv("QUICK_SCRIPT_TARGET_AUDIENCE", "business person")
QUICK_SCRIPT_MAX_ITERATIONS = int(os.getenv("QUICK_SCRIPT_MAX_ITERATIONS", "3"))

# Script Duration Settings
DEFAULT_SCRIPT_DURATION = int(os.getenv("DEFAULT_SCRIPT_DURATION", "11"))  # Target duration in minutes
SCRIPT_WORDS_PER_MINUTE = int(os.getenv("SCRIPT_WORDS_PER_MINUTE", "150"))  # Average speaking pace
MIN_SCRIPT_DURATION = int(os.getenv("MIN_SCRIPT_DURATION", "10"))  # Minimum duration
MAX_SCRIPT_DURATION = int(os.getenv("MAX_SCRIPT_DURATION", "12"))  # Maximum duration

# Auto Research Settings
AUTO_RESEARCH_OUTLIER_COUNT = int(os.getenv("AUTO_RESEARCH_OUTLIER_COUNT", "10"))  # Number of top outliers to analyze automatically

# Trend Discovery Settings
TREND_SEARCH_POOL_MULTIPLIER = int(os.getenv("TREND_SEARCH_POOL_MULTIPLIER", "4"))
TREND_MAX_SEARCH_POOL = int(os.getenv("TREND_MAX_SEARCH_POOL", "100"))
TREND_MIN_VIEWS = int(os.getenv("TREND_MIN_VIEWS", "500"))
TREND_MIN_VIEWS_PER_DAY = int(os.getenv("TREND_MIN_VIEWS_PER_DAY", "50"))

# Web App Authentication
APP_LOGIN_PASSWORD = os.getenv("APP_LOGIN_PASSWORD", "").strip()
APP_SESSION_SECRET = os.getenv("APP_SESSION_SECRET", APP_LOGIN_PASSWORD).strip()
APP_SESSION_TTL_HOURS = int(os.getenv("APP_SESSION_TTL_HOURS", "24"))
APP_COOKIE_SECURE = os.getenv("APP_COOKIE_SECURE", "false").lower() in {"1", "true", "yes", "on"}
APP_COOKIE_NAME = os.getenv("APP_COOKIE_NAME", "yt_strategy_session").strip() or "yt_strategy_session"

# YouTube Data API v3
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "").strip()
YOUTUBE_API_TIMEOUT = int(os.getenv("YOUTUBE_API_TIMEOUT", "20"))
