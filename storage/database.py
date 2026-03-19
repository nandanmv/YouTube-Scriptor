"""
SQLite persistence layer for the YouTube Analysis Platform.

This module provides structured storage replacing fragile markdown parsing.
Supports concurrent access, transactions, and query capabilities.
"""

import sqlite3
import json
from typing import List, Optional, Dict, Any
from datetime import datetime
from contextlib import contextmanager
import threading

from models.schemas import (
    OutlierResult,
    SearchJob,
    Video,
    Insight,
    JobStatus
)


class AnalysisStore:
    """
    SQLite-based storage for analysis results, jobs, and insights.

    Replaces markdown file parsing with structured queries.
    Thread-safe with connection pooling.
    """

    def __init__(self, db_path: str = "youtube_analysis.db"):
        """
        Initialize the storage layer.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._local = threading.local()
        self._init_schema()

    @property
    def conn(self) -> sqlite3.Connection:
        """Get thread-local database connection."""
        if not hasattr(self._local, 'conn'):
            self._local.conn = sqlite3.connect(
                self.db_path,
                check_same_thread=False
            )
            self._local.conn.row_factory = sqlite3.Row
        return self._local.conn

    @contextmanager
    def transaction(self):
        """Context manager for database transactions."""
        conn = self.conn
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise

    def _init_schema(self):
        """Create database tables if they don't exist."""
        with self.transaction() as conn:
            # Search jobs table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS search_jobs (
                    job_id TEXT PRIMARY KEY,
                    query TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    completed_at TEXT,
                    webhook_url TEXT,
                    error_message TEXT,
                    result_count INTEGER
                )
            """)

            # Outlier videos table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS outlier_videos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id TEXT NOT NULL,
                    url TEXT NOT NULL,
                    title TEXT NOT NULL,
                    views INTEGER NOT NULL,
                    median_views REAL NOT NULL,
                    ratio REAL NOT NULL,
                    channel TEXT NOT NULL,
                    subscribers INTEGER,
                    marked_for_analysis BOOLEAN DEFAULT 0,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (job_id) REFERENCES search_jobs(job_id),
                    UNIQUE(job_id, url)
                )
            """)

            # Create index for faster lookups
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_outlier_videos_url
                ON outlier_videos(url)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_outlier_videos_marked
                ON outlier_videos(marked_for_analysis)
            """)

            # Insights table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS insights (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    video_url TEXT NOT NULL UNIQUE,
                    video_title TEXT NOT NULL,
                    success_criteria TEXT,
                    reusable_insights TEXT,
                    ultimate_titles TEXT,
                    alternate_hooks TEXT,
                    generated_at TEXT NOT NULL
                )
            """)

            # Scripts table (for Phase 3)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS scripts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id TEXT NOT NULL UNIQUE,
                    video_url TEXT NOT NULL,
                    transcript TEXT,
                    hooks TEXT,
                    full_script TEXT,
                    estimated_duration TEXT,
                    key_points TEXT,
                    created_at TEXT NOT NULL
                )
            """)

    # ==================== Job Management ====================

    def save_job(self, job: SearchJob) -> None:
        """
        Save search job metadata.

        Args:
            job: SearchJob instance to save
        """
        with self.transaction() as conn:
            conn.execute("""
                INSERT INTO search_jobs
                (job_id, query, status, created_at, webhook_url)
                VALUES (?, ?, ?, ?, ?)
            """, (
                job.job_id,
                job.query,
                job.status.value,
                job.created_at.isoformat(),
                job.webhook_url
            ))

    def get_job(self, job_id: str) -> Optional[SearchJob]:
        """
        Get job by ID.

        Args:
            job_id: Job identifier

        Returns:
            SearchJob instance or None if not found
        """
        cursor = self.conn.execute("""
            SELECT * FROM search_jobs WHERE job_id = ?
        """, (job_id,))

        row = cursor.fetchone()
        if not row:
            return None

        return SearchJob(
            job_id=row["job_id"],
            query=row["query"],
            status=JobStatus(row["status"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            completed_at=datetime.fromisoformat(row["completed_at"]) if row["completed_at"] else None,
            webhook_url=row["webhook_url"],
            error_message=row["error_message"],
            result_count=row["result_count"]
        )

    def update_job_status(
        self,
        job_id: str,
        status: str,
        error_message: Optional[str] = None,
        result_count: Optional[int] = None
    ) -> None:
        """
        Update job status.

        Args:
            job_id: Job identifier
            status: New status (processing, completed, failed)
            error_message: Error message if failed
            result_count: Number of results if completed
        """
        with self.transaction() as conn:
            completed_at = datetime.now().isoformat() if status in ["completed", "failed"] else None

            conn.execute("""
                UPDATE search_jobs
                SET status = ?,
                    completed_at = ?,
                    error_message = ?,
                    result_count = ?
                WHERE job_id = ?
            """, (status, completed_at, error_message, result_count, job_id))

    def list_jobs(self, limit: int = 50) -> List[SearchJob]:
        """
        List recent jobs.

        Args:
            limit: Maximum number of jobs to return

        Returns:
            List of SearchJob instances
        """
        cursor = self.conn.execute("""
            SELECT * FROM search_jobs
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit,))

        return [
            SearchJob(
                job_id=row["job_id"],
                query=row["query"],
                status=JobStatus(row["status"]),
                created_at=datetime.fromisoformat(row["created_at"]),
                completed_at=datetime.fromisoformat(row["completed_at"]) if row["completed_at"] else None,
                webhook_url=row["webhook_url"],
                error_message=row["error_message"],
                result_count=row["result_count"]
            )
            for row in cursor.fetchall()
        ]

    # ==================== Outlier Management ====================

    def save_outliers(self, job_id: str, outliers: List[Dict[str, Any]]) -> None:
        """
        Save outlier videos for a job.

        Args:
            job_id: Job identifier
            outliers: List of outlier video dictionaries
        """
        with self.transaction() as conn:
            for outlier in outliers:
                # Handle both dict and OutlierResult types
                if isinstance(outlier, dict):
                    video = outlier.get("video", outlier)
                    url = video.get("url")
                    title = video.get("title")
                    views = video.get("views")
                    channel = video.get("channel")
                    subscribers = video.get("subscribers")
                    median_views = outlier.get("median_views", 0)
                    ratio = outlier.get("ratio", 0)
                else:
                    url = outlier.video.url
                    title = outlier.video.title
                    views = outlier.video.views
                    channel = outlier.video.channel
                    subscribers = outlier.video.subscribers
                    median_views = outlier.median_views
                    ratio = outlier.ratio

                try:
                    conn.execute("""
                        INSERT INTO outlier_videos
                        (job_id, url, title, views, median_views, ratio,
                         channel, subscribers, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        job_id,
                        url,
                        title,
                        views,
                        median_views,
                        ratio,
                        channel,
                        subscribers,
                        datetime.now().isoformat()
                    ))
                except sqlite3.IntegrityError:
                    # Duplicate URL for this job, skip
                    pass

    def get_outliers(self, job_id: str) -> List[Dict[str, Any]]:
        """
        Get outlier videos for a job.

        Args:
            job_id: Job identifier

        Returns:
            List of outlier dictionaries
        """
        cursor = self.conn.execute("""
            SELECT * FROM outlier_videos
            WHERE job_id = ?
            ORDER BY ratio DESC
        """, (job_id,))

        return [
            {
                "video": {
                    "url": row["url"],
                    "title": row["title"],
                    "views": row["views"],
                    "channel": row["channel"],
                    "subscribers": row["subscribers"]
                },
                "median_views": row["median_views"],
                "ratio": row["ratio"],
                "marked_for_analysis": bool(row["marked_for_analysis"])
            }
            for row in cursor.fetchall()
        ]

    def get_marked_videos(self) -> List[Dict[str, Any]]:
        """
        Get all videos marked for analysis.

        Replaces ShortlistAgent's markdown parsing!

        Returns:
            List of marked video dictionaries
        """
        cursor = self.conn.execute("""
            SELECT DISTINCT url, title, views, median_views, ratio, channel, subscribers
            FROM outlier_videos
            WHERE marked_for_analysis = 1
            ORDER BY ratio DESC
        """)

        return [
            {
                "video": {
                    "url": row["url"],
                    "title": row["title"],
                    "views": row["views"],
                    "channel": row["channel"],
                    "subscribers": row["subscribers"]
                },
                "median_views": row["median_views"],
                "ratio": row["ratio"],
                "marked_for_analysis": True
            }
            for row in cursor.fetchall()
        ]

    def mark_video(self, url: str, marked: bool = True) -> bool:
        """
        Mark or unmark video for analysis.

        Args:
            url: Video URL
            marked: True to mark, False to unmark

        Returns:
            True if video was found and updated
        """
        with self.transaction() as conn:
            cursor = conn.execute("""
                UPDATE outlier_videos
                SET marked_for_analysis = ?
                WHERE url = ?
            """, (1 if marked else 0, url))

            return cursor.rowcount > 0

    # ==================== Insight Management ====================

    def save_insight(self, insight: Insight) -> None:
        """
        Save AI-generated insight for a video.

        Args:
            insight: Insight instance to save
        """
        with self.transaction() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO insights
                (video_url, video_title, success_criteria, reusable_insights,
                 ultimate_titles, alternate_hooks, generated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                insight.video_url,
                insight.video_title,
                json.dumps(insight.success_criteria),
                json.dumps(insight.reusable_insights),
                json.dumps(insight.ultimate_titles),
                json.dumps(insight.alternate_hooks),
                insight.generated_at.isoformat()
            ))

    def get_insight(self, video_url: str) -> Optional[Insight]:
        """
        Get insight for a video.

        Args:
            video_url: Video URL

        Returns:
            Insight instance or None if not found
        """
        cursor = self.conn.execute("""
            SELECT * FROM insights WHERE video_url = ?
        """, (video_url,))

        row = cursor.fetchone()
        if not row:
            return None

        return Insight(
            video_url=row["video_url"],
            video_title=row["video_title"],
            success_criteria=json.loads(row["success_criteria"]),
            reusable_insights=json.loads(row["reusable_insights"]),
            ultimate_titles=json.loads(row["ultimate_titles"]),
            alternate_hooks=json.loads(row["alternate_hooks"]),
            generated_at=datetime.fromisoformat(row["generated_at"])
        )

    def list_insights(self, limit: int = 50) -> List[Insight]:
        """
        List recent insights.

        Args:
            limit: Maximum number of insights to return

        Returns:
            List of Insight instances
        """
        cursor = self.conn.execute("""
            SELECT * FROM insights
            ORDER BY generated_at DESC
            LIMIT ?
        """, (limit,))

        return [
            Insight(
                video_url=row["video_url"],
                video_title=row["video_title"],
                success_criteria=json.loads(row["success_criteria"]),
                reusable_insights=json.loads(row["reusable_insights"]),
                ultimate_titles=json.loads(row["ultimate_titles"]),
                alternate_hooks=json.loads(row["alternate_hooks"]),
                generated_at=datetime.fromisoformat(row["generated_at"])
            )
            for row in cursor.fetchall()
        ]

    # ==================== Script Management (Phase 3) ====================

    def save_script(self, job_id: str, video_url: str, script_data: Dict[str, Any]) -> None:
        """
        Save generated script (for Phase 3).

        Args:
            job_id: Job identifier
            video_url: Video URL
            script_data: Script data dictionary
        """
        with self.transaction() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO scripts
                (job_id, video_url, transcript, hooks, full_script,
                 estimated_duration, key_points, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                job_id,
                video_url,
                script_data.get("transcript"),
                json.dumps(script_data.get("hooks", [])),
                script_data.get("full_script"),
                script_data.get("estimated_duration"),
                json.dumps(script_data.get("key_points", [])),
                datetime.now().isoformat()
            ))

    def get_script(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get script by job ID.

        Args:
            job_id: Job identifier

        Returns:
            Script dictionary or None if not found
        """
        cursor = self.conn.execute("""
            SELECT * FROM scripts WHERE job_id = ?
        """, (job_id,))

        row = cursor.fetchone()
        if not row:
            return None

        return {
            "job_id": row["job_id"],
            "video_url": row["video_url"],
            "transcript": row["transcript"],
            "hooks": json.loads(row["hooks"]) if row["hooks"] else [],
            "full_script": row["full_script"],
            "estimated_duration": row["estimated_duration"],
            "key_points": json.loads(row["key_points"]) if row["key_points"] else [],
            "created_at": row["created_at"]
        }

    def close(self):
        """Close database connection."""
        if hasattr(self._local, 'conn'):
            self._local.conn.close()
            delattr(self._local, 'conn')
