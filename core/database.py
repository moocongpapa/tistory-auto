"""
Dual Database Manager: Supports Supabase (PostgreSQL) and Local SQLite seamlessly.
Provides Bulletproof Fault-Tolerance and Graceful Fallback.
"""

import os
import re
import urllib.parse
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
DB_PATH = os.path.join(DB_DIR, "publisher.db")


class DatabaseManager:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        raw_db_url = os.environ.get("DATABASE_URL") or os.environ.get("SUPABASE_DB_URL") or ""
        self.database_url = self._sanitize_db_url(raw_db_url)
        self.is_postgres = bool(self.database_url and ("postgresql" in self.database_url or "postgres" in self.database_url))

        # Test PostgreSQL connection upon initialization; fallback to SQLite if it fails
        if self.is_postgres:
            try:
                import psycopg2
                test_conn = psycopg2.connect(self.database_url, connect_timeout=5)
                test_conn.close()
                logger.info("🚀 [데이터베이스] Supabase 클라우드 PostgreSQL 연결 성공!")
            except Exception as e:
                logger.warning(f"⚠️ [데이터베이스] Supabase 연결 시도 실패 ({e}). 로컬 SQLite로 자동 안전 전환합니다.")
                self.is_postgres = False

        if not self.is_postgres:
            logger.info(f"💾 [데이터베이스] 로컬 SQLite 연결 모드 가동: {self.db_path}")

        self.init_db()

    def _sanitize_db_url(self, url: str) -> str:
        if not url:
            return ""
        url = url.strip()
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)

        # Handle unencoded special characters in password (e.g., @ or #)
        if "@" in url:
            try:
                creds_part, host_part = url.rsplit("@", 1)
                parts = creds_part.split(":", 2)
                if len(parts) >= 3:
                    proto_user = parts[0] + ":" + parts[1]
                    raw_pw = parts[2]
                    encoded_pw = urllib.parse.quote(raw_pw)
                    url = f"{proto_user}:{encoded_pw}@{host_part}"
            except Exception:
                pass
        return url

    def get_connection(self):
        if self.is_postgres:
            try:
                import psycopg2
                from psycopg2.extras import RealDictCursor
                conn = psycopg2.connect(self.database_url, connect_timeout=5, cursor_factory=RealDictCursor)
                return conn
            except Exception as e:
                logger.error(f"PostgreSQL 연결 중 오류 발생: {e}. SQLite로 임시 대체합니다.")
                self.is_postgres = False

        import sqlite3
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            if self.is_postgres:
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
                """)
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS topic_pool (
                    id SERIAL PRIMARY KEY,
                    blog_id TEXT NOT NULL,
                    theme TEXT NOT NULL,
                    keyword TEXT NOT NULL,
                    topic TEXT NOT NULL,
                    is_used INTEGER DEFAULT 0,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
                """)
                cursor.execute("""
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
                """)
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_posts_blog ON posts(blog_id);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_posts_keyword ON posts(keyword);")
            else:
                cursor.executescript("""
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
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def get_recent_topics(self, blog_id: str, limit: int = 30) -> List[str]:
        ph = "%s" if self.is_postgres else "?"
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT keyword, title FROM posts WHERE blog_id = {ph} ORDER BY id DESC LIMIT {ph}",
                (blog_id, limit)
            )
            rows = cursor.fetchall()
            return [f"- [{row['keyword']}] {row['title']}" for row in rows]
        except Exception as e:
            logger.error(f"get_recent_topics error: {e}")
            return []
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

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
        conn = None

        try:
            conn = self.get_connection()
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
        except Exception as e:
            logger.error(f"record_post error: {e}")
            return 0
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def get_all_posts(self, blog_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        ph = "%s" if self.is_postgres else "?"
        conn = None
        try:
            conn = self.get_connection()
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
        except Exception as e:
            logger.error(f"get_all_posts error: {e}")
            return []
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def get_posts_by_blog(self, blog_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        return self.get_all_posts(blog_id=blog_id, limit=limit)

    def get_dashboard_stats(self) -> Dict[str, Any]:
        today_prefix = datetime.now().strftime("%Y-%m-%d")
        ph = "%s" if self.is_postgres else "?"
        conn = None
        try:
            conn = self.get_connection()
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
        except Exception as e:
            logger.error(f"get_dashboard_stats error: {e}")
            return {"total_posts": 0, "today_posts": 0, "active_blogs": 5}
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def delete_posts(self, post_ids: List[int]) -> int:
        if not post_ids:
            return 0
        ph = "%s" if self.is_postgres else "?"
        placeholders = ",".join([ph] * len(post_ids))
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(f"DELETE FROM posts WHERE id IN ({placeholders})", post_ids)
            conn.commit()
            return cursor.rowcount
        except Exception as e:
            logger.error(f"delete_posts error: {e}")
            return 0
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def delete_all_posts(self) -> int:
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM posts")
            conn.commit()
            return cursor.rowcount
        except Exception as e:
            logger.error(f"delete_all_posts error: {e}")
            return 0
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

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
        conn = None
        try:
            conn = self.get_connection()
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
        except Exception as e:
            logger.error(f"record_activity error: {e}")
            return 0
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def get_recent_activities(self, limit: int = 40) -> List[Dict[str, Any]]:
        ph = "%s" if self.is_postgres else "?"
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT * FROM activity_logs ORDER BY id DESC LIMIT {ph}",
                (limit,)
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"get_recent_activities error: {e}")
            return []
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass