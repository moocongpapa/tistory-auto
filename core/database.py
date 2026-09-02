"""
SQLite Database Manager for Post History and Duplicate Prevention
"""

import os
import sqlite3
from datetime import datetime
from typing import List, Dict, Any, Optional

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
DB_PATH = os.path.join(DB_DIR, "publisher.db")

class DatabaseManager:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                blog_id TEXT NOT NULL,
                theme TEXT NOT NULL,
                keyword TEXT NOT NULL,
                title TEXT NOT NULL,
                summary TEXT,
                tags TEXT,
                content_html TEXT,
                thumbnail_path TEXT,
                status TEXT DEFAULT 'PUBLISHED',
                post_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                published_at TIMESTAMP
            )
            """
            )
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS topic_pool (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                blog_id TEXT NOT NULL,
                theme TEXT NOT NULL,
                keyword TEXT NOT NULL,
                topic TEXT NOT NULL,
                is_used INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            )
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_posts_blog ON posts(blog_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_posts_keyword ON posts(keyword)")
            conn.commit()

    def get_recent_topics(self, blog_id: str, limit: int = 30) -> List[str]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT keyword, title FROM posts WHERE blog_id = ? ORDER BY id DESC LIMIT ?",
                (blog_id, limit)
            )
            rows = cursor.fetchall()
            return [f"- [{row['keyword']}] {row['title']}" for row in rows]

    def record_post(
        self,
        blog_id: str,
        theme: str,
        keyword: str,
        title: str,
        summary: str,
        tags: List[str],
        content_html: str,
        thumbnail_path: Optional[str] = None,
        status: str = "PUBLISHED",
        post_url: Optional[str] = None
    ) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO posts (
                    blog_id, theme, keyword, title, summary, tags, content_html,
                    thumbnail_path, status, post_url, published_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    blog_id,
                    theme,
                    keyword,
                    title,
                    summary,
                    ",".join(tags) if isinstance(tags, list) else tags,
                    content_html,
                    thumbnail_path,
                    status,
                    post_url,
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                )
            )
            conn.commit()
            return cursor.lastrowid

    def get_all_posts(self, blog_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if blog_id:
                cursor.execute(
                    "SELECT * FROM posts WHERE blog_id = ? ORDER BY id DESC LIMIT ?",
                    (blog_id, limit)
                )
            else:
                cursor.execute(
                    "SELECT * FROM posts ORDER BY id DESC LIMIT ?",
                    (limit,)
                )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_posts_by_blog(self, blog_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Fetch posts specifically for a single blog ID."""
        return self.get_all_posts(blog_id=blog_id, limit=limit)

    def get_dashboard_stats(self) -> Dict[str, Any]:
        today_prefix = datetime.now().strftime("%Y-%m-%d")
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM posts")
            total_posts = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM posts WHERE published_at LIKE ?", (f"{today_prefix}%",))
            today_posts = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(DISTINCT blog_id) FROM posts")
            active_blogs = cursor.fetchone()[0]

            return {
                "total_posts": total_posts,
                "today_posts": today_posts,
                "active_blogs": active_blogs
            }

    def delete_posts(self, post_ids: List[int]) -> int:
        """Delete specific posts by IDs."""
        if not post_ids:
            return 0
        placeholders = ",".join(["?"] * len(post_ids))
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"DELETE FROM posts WHERE id IN ({placeholders})", post_ids)
            conn.commit()
            return cursor.rowcount

    def delete_all_posts(self) -> int:
        """Delete all post history."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM posts")
            conn.commit()
            return cursor.rowcount
