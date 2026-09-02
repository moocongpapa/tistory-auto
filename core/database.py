"""
Dual Database Manager: Supports Supabase (PostgreSQL) and Local SQLite seamlessly.
If DATABASE_URL or SUPABASE_DB_URL is provided in environment variables, connects to Supabase PostgreSQL.
Otherwise, falls back to local SQLite (data/publisher.db).
"""

import os
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
DB_PATH = os.path.join(DB_DIR, "publisher.db")


class DatabaseManager:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.database_url = os.environ.get("DATABASE_URL") or os.environ.get("SUPABASE_DB_URL") or ""
        
        # Handle Render / Supabase postgres:// -> postgresql:// URL schema
        if self.database_url.startswith("postgres://"):
            self.database_url = self.database_url.replace("postgres://", "postgresql://", 1)

        self.is_postgres = bool(self.database_url and "postgresql" in self.database_url)

        if self.is_postgres:
            logger.info("🚀 [데이터베이스] Supabase 클라우드 PostgreSQL 연결 모드 가동!")
        else:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            logger.info(f"💾 [데이터베이스] 로컬 SQLite 연결 모드 가동: {self.db_path}")

        self.init_db()

    def get_connection(self):
        if self.is_postgres:
            import psycopg2
            from psycopg2.extras import RealDictCursor
            conn = psycopg2.connect(self.database_url, cursor_factory=RealDictCursor)
            return conn
        else:
            import sqlite3
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            return conn

    def init_db(self):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                if self.is_postgres:
                    # PostgreSQL DDL
                    cursor.execute("""
                    CREATE TABLE IF NOT EXISTS posts (
                        id SERIAL PRIMARY KEY,
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
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        published_at TEXT
                    );
                    CREATE TABLE IF NOT EXISTS topic_pool (
                        id SERIAL PRIMARY KEY,
                        blog_id TEXT NOT NULL,
                        theme TEXT NOT NULL,
                        keyword TEXT NOT NULL,
                        topic TEXT NOT NULL,
                        is_used INTEGER DEFAULT 0,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    );
                    CREATE TABLE IF NOT EXISTS activity_logs (
                        id SERIAL PRIMARY KEY,
                        level TEXT NOT NULL,
                        blog_id TEXT,
                        blog_name TEXT,
                        category TEXT,
                        title TEXT,
                        message TEXT,
                        url TEXT,
                        created_at TEXT
                    );
                    CREATE INDEX IF NOT EXISTS idx_posts_blog ON posts(blog_id);
                    CREATE INDEX IF NOT EXISTS idx_posts_keyword ON posts(keyword);
                    """)
                else:
                    # SQLite DDL
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
                    );
                    CREATE TABLE IF NOT EXISTS topic_pool (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        blog_id TEXT NOT NULL,
                        theme TEXT NOT NULL,
                        keyword TEXT NOT NULL,
                        topic TEXT NOT NULL,
                        is_used INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    CREATE TABLE IF NOT EXISTS activity_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        level TEXT NOT NULL,
                        blog_id TEXT,
                        blog_name TEXT,
                        category TEXT,
                        title TEXT,
                        message TEXT,
                        url TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    CREATE INDEX IF NOT EXISTS idx_posts_blog ON posts(blog_id);
                    CREATE INDEX IF NOT EXISTS idx_posts_keyword ON posts(keyword);
                    CREATE INDEX IF NOT EXISTS idx_activity_created ON activity_logs(created_at);
                    """)
                conn.commit()
                logger.info("✅ 데이터베이스 테이블 스키마 초기화 완료!")
        except Exception as e:
            logger.error(f"❌ 데이터베이스 초기화 실패: {e}")

    def get_recent_topics(self, blog_id: str, limit: int = 30) -> List[str]:
        ph = "%s" if self.is_postgres else "?"
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT keyword, title FROM posts WHERE blog_id = {ph} ORDER BY id DESC LIMIT {ph}",
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
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        tags_str = ",".join(tags) if isinstance(tags, list) else tags
        ph = "%s" if self.is_postgres else "?"

        with self.get_connection() as conn:
            cursor = conn.cursor()
            if self.is_postgres:
                cursor.execute(
                    f"""
                    INSERT INTO posts (
                        blog_id, theme, keyword, title, summary, tags, content_html,
                        thumbnail_path, status, post_url, published_at
                    ) VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph})
                    RETURNING id
                    """,
                    (blog_id, theme, keyword, title, summary, tags_str, content_html, thumbnail_path, status, post_url, now_str)
                )
                row = cursor.fetchone()
                post_id = row['id'] if isinstance(row, dict) else row[0]
            else:
                cursor.execute(
                    f"""
                    INSERT INTO posts (
                        blog_id, theme, keyword, title, summary, tags, content_html,
                        thumbnail_path, status, post_url, published_at
                    ) VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph})
                    """,
                    (blog_id, theme, keyword, title, summary, tags_str, content_html, thumbnail_path, status, post_url, now_str)
                )
                post_id = cursor.lastrowid

            conn.commit()
            return post_id

    def get_all_posts(self, blog_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        ph = "%s" if self.is_postgres else "?"
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if blog_id:
                cursor.execute(
                    f"SELECT * FROM posts WHERE blog_id = {ph} ORDER BY id DESC LIMIT {ph}",
                    (blog_id, limit)
                )
            else:
                cursor.execute(
                    f"SELECT * FROM posts ORDER BY id DESC LIMIT {ph}",
                    (limit,)
                )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_posts_by_blog(self, blog_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        return self.get_all_posts(blog_id=blog_id, limit=limit)

    def get_dashboard_stats(self) -> Dict[str, Any]:
        today_prefix = datetime.now().strftime("%Y-%m-%d")
        ph = "%s" if self.is_postgres else "?"
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM posts")
            row = cursor.fetchone()
            total_posts = (row['count'] if isinstance(row, dict) and 'count' in row else (list(row.values())[0] if isinstance(row, dict) else row[0])) or 0

            cursor.execute(f"SELECT COUNT(*) FROM posts WHERE published_at LIKE {ph}", (f"{today_prefix}%",))
            row = cursor.fetchone()
            today_posts = (row['count'] if isinstance(row, dict) and 'count' in row else (list(row.values())[0] if isinstance(row, dict) else row[0])) or 0

            cursor.execute("SELECT COUNT(DISTINCT blog_id) FROM posts")
            row = cursor.fetchone()
            active_blogs = (row['count'] if isinstance(row, dict) and 'count' in row else (list(row.values())[0] if isinstance(row, dict) else row[0])) or 0

            return {
                "total_posts": total_posts,
                "today_posts": today_posts,
                "active_blogs": active_blogs
            }

    def delete_posts(self, post_ids: List[int]) -> int:
        if not post_ids:
            return 0
        ph = "%s" if self.is_postgres else "?"
        placeholders = ",".join([ph] * len(post_ids))
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"DELETE FROM posts WHERE id IN ({placeholders})", post_ids)
            conn.commit()
            return cursor.rowcount

    def delete_all_posts(self) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM posts")
            conn.commit()
            return cursor.rowcount

    def record_activity(
        self,
        level: str,
        blog_id: str = "",
        blog_name: str = "",
        title: str = "",
        message: str = "",
        url: str = "",
        category: str = ""
    ) -> int:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ph = "%s" if self.is_postgres else "?"
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if self.is_postgres:
                cursor.execute(
                    f"""
                    INSERT INTO activity_logs (level, blog_id, blog_name, category, title, message, url, created_at)
                    VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph})
                    RETURNING id
                    """,
                    (level.upper(), blog_id, blog_name, category, title, message, url, now_str)
                )
                row = cursor.fetchone()
                act_id = row['id'] if isinstance(row, dict) else row[0]
            else:
                cursor.execute(
                    f"""
                    INSERT INTO activity_logs (level, blog_id, blog_name, category, title, message, url, created_at)
                    VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph})
                    """,
                    (level.upper(), blog_id, blog_name, category, title, message, url, now_str)
                )
                act_id = cursor.lastrowid

            conn.commit()
            return act_id

    def get_recent_activities(self, limit: int = 40) -> List[Dict[str, Any]]:
        ph = "%s" if self.is_postgres else "?"
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT * FROM activity_logs ORDER BY id DESC LIMIT {ph}",
                (limit,)
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]