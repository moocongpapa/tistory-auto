"""
Central Scheduler for Multi-Blog Automated Posting Pipeline with Live Trends
"""

import os
import random
import logging
import yaml
from datetime import datetime
from typing import Dict, Any, List, Optional
import requests
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from core.database import DatabaseManager
from core.gemini_client import GeminiClient
from core.thumbnail import ThumbnailGenerator
from core.tistory_bot import TistoryBot
from core.trend_collector import TrendCollector
from core.adsense import AdSenseManager
from core.coupang_partners import CoupangPartnersManager
from core.google_indexing import GoogleIndexingManager
from core.internal_linker import InternalLinker

logger = logging.getLogger(__name__)

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", "config.yaml")

class MultiBlogScheduler:
    def __init__(self, config_path: str = CONFIG_PATH, use_background: bool = True):
        self.config_path = config_path
        self.config = self._load_config()
        self.db = DatabaseManager()
        self.gemini = GeminiClient()
        self.thumbnail_gen = ThumbnailGenerator()
        self.trend_collector = TrendCollector()
        self.internal_linker = InternalLinker(self.db)
        headless = self.config.get("publishing", {}).get("headless", True)
        self.bot = TistoryBot(headless=headless)
        self.use_background = use_background
        self.scheduler = BackgroundScheduler(timezone="Asia/Seoul") if use_background else BlockingScheduler(timezone="Asia/Seoul")

    def _load_config(self) -> Dict[str, Any]:
        with open(self.config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def run_blog_pipeline(self, blog_id: str, is_draft_override: Optional[bool] = None) -> Dict[str, Any]:
        """Full execution pipeline for a single blog: Trends -> Topic -> Article -> Thumbnail -> Post."""
        blogs = {b["id"]: b for b in self.config.get("blogs", [])}
        blog_cfg = blogs.get(blog_id)
        if not blog_cfg:
            logger.error(f"Blog ID {blog_id} not found in configuration.")
            return {"success": False, "error": "Blog not found"}

        blog_name = blog_cfg.get("name", "블로그")
        subdomain = blog_cfg.get("subdomain")
        themes = blog_cfg.get("themes", [])
        if not themes:
            logger.error(f"No themes defined for blog {blog_id}")
            return {"success": False, "error": "No themes"}

        logger.info(f"=== Starting Auto-Posting Pipeline for [{blog_name} ({subdomain})] ===")

        # 1. Smart Round-Robin Theme Rotation based on DB history
        last_posts = self.db.get_posts_by_blog(blog_id, limit=1)
        if last_posts and themes:
            last_theme_name = last_posts[0].get("theme")
            theme_names = [t.get("name") for t in themes]
            if last_theme_name in theme_names:
                curr_idx = theme_names.index(last_theme_name)
                next_idx = (curr_idx + 1) % len(themes)
                theme = themes[next_idx]
            else:
                theme = themes[0]
        else:
            theme = random.choice(themes)

        theme_name = theme.get("name")
        keywords = theme.get("keywords", [])
        logger.info(f"선택된 순환 카테고리/테마: [{theme_name}]")

        # 2. Fetch live real-time trend keywords
        trend_keywords = self.trend_collector.get_trend_keywords_list(limit=8)

        # 3. Get recent topics to prevent duplicates
        previous_topics = self.db.get_recent_topics(blog_id=blog_id, limit=15)

        # 4. Discover fresh topic with Gemini (combining trends + static keywords)
        logger.info(f"Discovering fresh topic for theme: {theme_name}...")
        model_name = self.config.get("ai", {}).get("text_model", "gemini-3.6-flash")
        topic_info = self.gemini.discover_topic(
            blog_name=blog_name,
            theme_name=theme_name,
            keywords=keywords,
            previous_topics=previous_topics,
            trend_keywords=trend_keywords,
            model=model_name
        )
        selected_keyword = topic_info.get("keyword", "핵심 주제")
        selected_topic = topic_info.get("topic", f"{theme_name} 포스팅")
        logger.info(f"Selected Keyword: {selected_keyword} | Topic: {selected_topic}")

        # 5. Generate SEO Article
        logger.info("Generating SEO-optimized HTML article with Gemini...")
        quality_cfg = self.config.get("publishing", {})
        article = self.gemini.generate_article(
            theme_name=theme_name,
            keyword=selected_keyword,
            topic=selected_topic,
            model=model_name,
            quality_config=quality_cfg
        )
        title = article.get("title", f"{selected_keyword} 완벽 가이드")
        summary = article.get("summary", "")
        content_html = article.get("content_html", "")
        tags = article.get("tags", [selected_keyword])
        image_prompt = article.get("thumbnail_image_prompt", "")

        # 5-1. Inject Google AdSense Ads (Top, Mid, Bottom)
        adsense_cfg = self.config.get("adsense", {})
        if adsense_cfg.get("enabled", True):
            ads_mgr = AdSenseManager(
                pub_id=adsense_cfg.get("pub_id", "ca-pub-9856782529784947"),
                enabled=adsense_cfg.get("enabled", True)
            )
            content_html = ads_mgr.inject_ads(content_html, slots=adsense_cfg)

        # 5-2. Inject Coupang Partners Affiliate Product Recommendations (if configured)
        coupang_mgr = CoupangPartnersManager()
        if coupang_mgr.is_configured():
            product_box = coupang_mgr.generate_product_box_html(selected_keyword)
            if product_box:
                content_html += product_box
                logger.info(f"쿠팡 파트너스 추천 상품 박스 자동 주입 완료: '{selected_keyword}'")

        # 5-3. Inject Internal Links (Related Posts for Higher Pageviews & Ad Impressions)
        link_count = self.config.get("seo", {}).get("internal_link_count", 2)
        if link_count > 0:
            content_html = self.internal_linker.inject_internal_links(
                html_content=content_html,
                blog_id=blog_id,
                current_keyword=selected_keyword,
                count=link_count
            )
            logger.info(f"내부 관련 글 링크 박스 자동 주입 완료 (blog: {blog_id})")

        # 6. Generate Clean High-Res Photo Thumbnail (Curated Preset Pool)
        thumbnail_path = None
        if self.config.get("publishing", {}).get("generate_thumbnail", True):
            thumbnail_path = self.thumbnail_gen.create_thumbnail(
                title=title,
                theme_name=theme_name,
                blog_id=blog_id,
                filename_prefix=f"{blog_id}_thumb"
            )

        # 7. Publish to Tistory
        default_status = self.config.get("publishing", {}).get("default_status", "PUBLIC")
        is_draft = is_draft_override if is_draft_override is not None else (default_status.upper() == "DRAFT")

        logger.info(f"Posting to Tistory ({'DRAFT' if is_draft else 'PUBLIC'})...")
        post_result = self.bot.post_article(
            subdomain=subdomain,
            title=title,
            content_html=content_html,
            tags=tags,
            thumbnail_path=thumbnail_path,
            category_name=theme_name,
            is_draft=is_draft
        )

        # 8. Record into Database
        relative_thumb = None
        if thumbnail_path:
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            try:
                relative_thumb = os.path.relpath(thumbnail_path, project_root).replace("\\", "/")
            except Exception:
                relative_thumb = os.path.basename(thumbnail_path)

        post_id = self.db.record_post(
            blog_id=blog_id,
            theme=theme_name,
            keyword=selected_keyword,
            title=title,
            summary=summary,
            tags=tags,
            content_html=content_html,
            thumbnail_path=relative_thumb,
            status=post_result.get("status", "PUBLISHED"),
            post_url=post_result.get("url")
        )

        # 9. Google Indexing API Fast Submission (if published)
        if post_result.get("status") == "PUBLISHED" and post_result.get("url"):
            indexing_mgr = GoogleIndexingManager()
            indexing_mgr.request_indexing(post_result["url"])

        logger.info(f"Successfully completed! DB Post ID: {post_id}, URL: {post_result.get('url')}")
        return {
            "success": True,
            "post_id": post_id,
            "title": title,
            "keyword": selected_keyword,
            "url": post_result.get("url"),
            "status": post_result.get("status")
        }

    def ping_self(self):
        """Send a keep-alive heartbeat ping every 5 minutes to prevent Render from sleeping."""
        try:
            external_url = (os.environ.get("RENDER_EXTERNAL_URL") or os.environ.get("APP_URL") or "").rstrip("/")
            target_url = f"{external_url}/api/health" if external_url else "http://127.0.0.1:8000/api/health"
            resp = requests.get(target_url, timeout=10)
            logger.info(f"💓 [Keep-Alive Heartbeat] Sent 5-min ping to {target_url} -> Status {resp.status_code}")
        except Exception as e:
            logger.debug(f"[Keep-Alive Heartbeat] Ping note: {e}")

    def register_jobs(self):
        """Register cron schedules for all enabled blogs and keep-alive heartbeat."""
        blogs = self.config.get("blogs", [])
        for b in blogs:
            if not b.get("enabled", True):
                continue
            blog_id = b["id"]
            blog_name = b.get("name", blog_id)
            schedule_times = b.get("schedule_times", ["07:00", "13:00", "19:00"])

            for st in schedule_times:
                hour, minute = st.split(":")
                trigger = CronTrigger(hour=int(hour), minute=int(minute))
                self.scheduler.add_job(
                    self.run_blog_pipeline,
                    trigger=trigger,
                    args=[blog_id],
                    id=f"{blog_id}_{hour}_{minute}",
                    name=f"[{blog_name}] 매일 {st}",
                    replace_existing=True
                )
                logger.info(f"Scheduled [{blog_name}] for daily execution at {st}")

        # Add 5-minute Keep-Alive Ping Job for Render free-tier sleep prevention
        self.scheduler.add_job(
            self.ping_self,
            trigger=IntervalTrigger(minutes=5),
            id="keep_alive_ping",
            name="[Render Keep-Alive] 5분 주기 서버 활성 핑",
            replace_existing=True
        )
        logger.info("Registered 5-minute Keep-Alive Heartbeat job for Render sleep prevention.")

    def get_scheduled_jobs_info(self) -> List[Dict[str, Any]]:
        jobs = []
        for job in self.scheduler.get_jobs():
            next_run = job.next_run_time.strftime("%Y-%m-%d %H:%M:%S") if job.next_run_time else "-"
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run": next_run
            })
        return sorted(jobs, key=lambda x: x["next_run"])

    def get_daily_post_count(self) -> int:
        """Returns the current configured daily post count per blog (3, 4, or 5)."""
        return int(self.config.get("publishing", {}).get("daily_post_count", 3))

    def update_daily_post_count(self, count: int) -> Dict[str, Any]:
        """Update schedule times for 3, 4, or 5 daily posts per blog and reschedule jobs."""
        if count not in [3, 4, 5]:
            count = 3

        # Preset schedule time maps for 3, 4, 5 posts per blog
        SCHEDULE_PRESETS = {
            3: {
                "blog_1": ["06:30", "11:30", "17:30"],
                "blog_2": ["06:45", "11:45", "17:45"],
                "blog_3": ["07:00", "12:00", "18:00"],
                "blog_4": ["07:15", "12:15", "18:15"],
                "blog_5": ["07:30", "12:30", "18:30"],
            },
            4: {
                "blog_1": ["06:30", "11:30", "15:30", "20:30"],
                "blog_2": ["06:45", "11:45", "15:45", "20:45"],
                "blog_3": ["07:00", "12:00", "16:00", "21:00"],
                "blog_4": ["07:15", "12:15", "16:15", "21:15"],
                "blog_5": ["07:30", "12:30", "16:30", "21:30"],
            },
            5: {
                "blog_1": ["06:30", "10:00", "13:30", "17:00", "21:00"],
                "blog_2": ["06:45", "10:15", "13:45", "17:15", "21:15"],
                "blog_3": ["07:00", "10:30", "14:00", "17:30", "21:30"],
                "blog_4": ["07:15", "10:45", "14:15", "17:45", "21:45"],
                "blog_5": ["07:30", "11:00", "14:30", "18:00", "22:00"],
            }
        }

        preset = SCHEDULE_PRESETS.get(count, SCHEDULE_PRESETS[3])

        # Update in-memory config
        if "publishing" not in self.config:
            self.config["publishing"] = {}
        self.config["publishing"]["daily_post_count"] = count

        for b in self.config.get("blogs", []):
            b_id = b.get("id")
            if b_id in preset:
                b["schedule_times"] = preset[b_id]

        # Save to config.yaml file
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                yaml.safe_dump(self.config, f, allow_unicode=True, sort_keys=False)
            logger.info(f"config.yaml 파일에 일일 {count}회 포스팅 스케줄 저장 완료")
        except Exception as e:
            logger.error(f"config.yaml 저장 실패: {e}")

        # Reschedule jobs in APScheduler
        try:
            self.scheduler.remove_all_jobs()
            self.register_jobs()
            logger.info(f"스케줄러 작업 전체 재등록 완료 (일일 블로그당 {count}회, 총 {count * len(self.config.get('blogs', []))}회)")
        except Exception as e:
            logger.error(f"스케줄러 재등록 실패: {e}")

        return {
            "success": True,
            "daily_post_count": count,
            "total_daily_target": count * len(self.config.get("blogs", [])),
            "jobs_count": len(self.scheduler.get_jobs())
        }

    def start(self):
        self.register_jobs()
        self.scheduler.start()

