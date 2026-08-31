"""
Central Scheduler for Multi-Blog Automated Posting Pipeline with Live Trends
"""

import os
import random
import logging
import yaml
from datetime import datetime
from typing import Dict, Any, List, Optional
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from core.database import DatabaseManager
from core.gemini_client import GeminiClient
from core.thumbnail import ThumbnailGenerator
from core.tistory_bot import TistoryBot
from core.trend_collector import TrendCollector

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

        # 1. Select theme (random or rotation)
        theme = random.choice(themes)
        theme_name = theme.get("name")
        keywords = theme.get("keywords", [])

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
        article = self.gemini.generate_article(
            theme_name=theme_name,
            keyword=selected_keyword,
            topic=selected_topic,
            model=model_name
        )
        title = article.get("title", f"{selected_keyword} 완벽 가이드")
        summary = article.get("summary", "")
        content_html = article.get("content_html", "")
        tags = article.get("tags", [selected_keyword])
        image_prompt = article.get("thumbnail_image_prompt", "")

        # 6. Generate Thumbnail Image
        thumbnail_path = None
        if self.config.get("publishing", {}).get("generate_thumbnail", True):
            base_ai_img = None
            if image_prompt:
                img_out = os.path.join("generated", "temp_ai_base.jpg")
                img_model = self.config.get("ai", {}).get("image_model", "imagen-3.0-generate-002")
                if self.gemini.generate_image_visual(image_prompt, img_out, model=img_model):
                    base_ai_img = img_out

            thumbnail_path = self.thumbnail_gen.create_thumbnail(
                title=title,
                badge_text=theme_name.split(" ")[0],
                base_image_path=base_ai_img,
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

        logger.info(f"Successfully completed! DB Post ID: {post_id}, URL: {post_result.get('url')}")
        return {
            "success": True,
            "post_id": post_id,
            "title": title,
            "keyword": selected_keyword,
            "url": post_result.get("url"),
            "status": post_result.get("status")
        }

    def register_jobs(self):
        """Register cron schedules for all enabled blogs."""
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

    def start(self):
        self.register_jobs()
        self.scheduler.start()
