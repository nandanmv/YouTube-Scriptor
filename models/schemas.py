"""
Pydantic data models for the YouTube Analysis Platform.

These models provide structured data validation and serialization
for API requests/responses and database operations.
"""

from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class JobStatus(str, Enum):
    """Job status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Video(BaseModel):
    """Video metadata"""
    url: str
    title: str
    views: int
    channel: str
    subscribers: Optional[int] = None

    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://youtube.com/watch?v=abc123",
                "title": "How to Build AI Agents",
                "views": 50000,
                "channel": "Tech Channel",
                "subscribers": 100000
            }
        }


class OutlierResult(BaseModel):
    """Outlier video detection result"""
    video: Video
    median_views: float
    ratio: float
    marked_for_analysis: bool = False

    class Config:
        json_schema_extra = {
            "example": {
                "video": {
                    "url": "https://youtube.com/watch?v=abc123",
                    "title": "How to Build AI Agents",
                    "views": 50000,
                    "channel": "Tech Channel",
                    "subscribers": 100000
                },
                "median_views": 5000.0,
                "ratio": 10.0,
                "marked_for_analysis": False
            }
        }


class SearchJob(BaseModel):
    """Search job metadata"""
    job_id: str
    query: str
    status: JobStatus
    created_at: datetime
    completed_at: Optional[datetime] = None
    webhook_url: Optional[str] = None
    error_message: Optional[str] = None
    result_count: Optional[int] = None

    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "123e4567-e89b-12d3-a456-426614174000",
                "query": "ai agents",
                "status": "completed",
                "created_at": "2024-01-01T12:00:00",
                "result_count": 15
            }
        }


class SearchRequest(BaseModel):
    """API request to start a search job"""
    query: str = Field(..., min_length=1, max_length=200)
    webhook_url: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "query": "ai agents",
                "webhook_url": "https://webhook.site/unique-id"
            }
        }


class SearchResponse(BaseModel):
    """API response for search job creation"""
    job_id: str
    status: JobStatus
    message: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "123e4567-e89b-12d3-a456-426614174000",
                "status": "processing",
                "message": "Search job started"
            }
        }


class JobStatusResponse(BaseModel):
    """API response for job status check"""
    job_id: str
    query: str
    status: JobStatus
    created_at: datetime
    completed_at: Optional[datetime] = None
    result_count: Optional[int] = None
    results: Optional[List[OutlierResult]] = None
    error_message: Optional[str] = None


class MarkVideoRequest(BaseModel):
    """Request to mark/unmark video for analysis"""
    url: str
    title: Optional[str] = None
    marked: bool = True


class Insight(BaseModel):
    """AI-generated insight for a video"""
    video_url: str
    video_title: str
    success_criteria: List[str]
    reusable_insights: List[str]
    ultimate_titles: List[str]
    alternate_hooks: List[str]
    generated_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "video_url": "https://youtube.com/watch?v=abc123",
                "video_title": "How to Build AI Agents",
                "success_criteria": ["Clear hook in first 10 seconds", "Strong CTA"],
                "reusable_insights": ["Pattern-based approach works well"],
                "ultimate_titles": ["Build AI Agents in 10 Minutes"],
                "alternate_hooks": ["What if I told you..."],
                "generated_at": "2024-01-01T12:00:00"
            }
        }


class WebhookPayload(BaseModel):
    """Webhook notification payload"""
    job_id: str
    status: JobStatus
    query: Optional[str] = None
    result_count: Optional[int] = None
    results_url: Optional[str] = None
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class DirectOutlierRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=200)
    limit: int = Field(default=10, ge=1, le=30)
    include_insights: bool = False


class DiscoveryRequest(BaseModel):
    terms: str = Field(..., min_length=1, max_length=500)


class ThemeRequest(BaseModel):
    topic: str = Field(..., min_length=1, max_length=200)
    videos: Optional[List[Dict[str, Any]]] = None


class AnglesRequest(BaseModel):
    topic: str = Field(..., min_length=1, max_length=200)
    videos: Optional[List[Dict[str, Any]]] = None


class CreateScriptRequest(BaseModel):
    topic: str = Field(..., min_length=1, max_length=200)
    notes: str = ""
    duration: Optional[int] = Field(default=None, ge=1, le=120)
    top_n_outliers: Optional[int] = Field(default=None, ge=1, le=50)
    strategy: Optional[str] = None
    selected_videos: Optional[List[Dict[str, Any]]] = None


class QuickScriptRequest(BaseModel):
    topic: str = Field(..., min_length=1, max_length=200)
    notes: str = Field(..., min_length=1)
    duration: int = Field(default=11, ge=1, le=120)
    reading_level: Optional[str] = None
    audience: Optional[str] = None
