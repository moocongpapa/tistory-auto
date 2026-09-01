"""
Internal Linker Module for Blog Posts
Automatically fetches related previous posts from SQLite DB and injects
a high-CTR 'Related Articles' box into the blog post HTML before publishing.
"""

import re
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class InternalLinker:
    def __init__(self, db_instance):
        self.db = db_instance

    def get_related_posts(self, blog_id: str, current_keyword: str = "", limit: int = 2) -> List[Dict[str, Any]]:
        """Fetch the most relevant recent published posts for the given blog."""
        try:
            posts = self.db.get_posts_by_blog(blog_id, limit=30)
            # Filter published posts with exact, valid individual post URLs (e.g. tistory.com/123 or tistory.com/entry/...)
            valid_posts = []
            for p in posts:
                url = (p.get("post_url") or "").strip()
                # Must not be a manage URL or general root domain
                if not url or url == "#" or "/manage" in url or "/newpost" in url:
                    continue
                # Must contain post number or entry slug
                if re.search(r"tistory\.com/\d+", url) or "/entry/" in url:
                    valid_posts.append(p)
            
            if not valid_posts:
                return []
            
            # Simple keyword overlap scoring, fallback to latest
            scored_posts = []
            kw_tokens = set(current_keyword.split()) if current_keyword else set()
            
            for p in valid_posts:
                score = 0
                title = p.get("title", "")
                p_kw = p.get("keyword", "")
                for token in kw_tokens:
                    if len(token) >= 2 and (token in title or token in p_kw):
                        score += 1
                scored_posts.append((score, p))
            
            scored_posts.sort(key=lambda x: x[0], reverse=True)
            return [p for _, p in scored_posts[:limit]]
        except Exception as e:
            logger.warning(f"Error fetching related posts for internal linking: {e}")
            return []

    def inject_internal_links(self, html_content: str, blog_id: str, current_keyword: str = "", count: int = 2) -> str:
        """Inject a modern, responsive 'Together Reading / Related Posts' box into the article."""
        related = self.get_related_posts(blog_id, current_keyword, limit=count)
        if not related:
            return html_content

        links_html = ""
        for post in related:
            title = post.get("title", "관련 추천 글")
            url = post.get("post_url", "").strip()
            if not url or "/manage" in url:
                continue
            theme = post.get("theme", "추천")
            links_html += f"""
<li style="margin-bottom: 10px; padding: 10px 14px; background: #f8fafc; border-radius: 8px; border-left: 3px solid #3b82f6; list-style: none;">
  <a href="{url}" style="color: #1e293b; text-decoration: none; font-weight: 600; font-size: 14px; display: flex; align-items: center; justify-content: space-between;" target="_blank">
    <span>📌 {title}</span>
    <span style="font-size: 11px; color: #3b82f6; font-weight: 700; margin-left: 8px; white-space: nowrap;">바로보기 &gt;</span>
  </a>
</li>
"""
        if not links_html.strip():
            return html_content

        related_box = f"""
<!-- Related Posts Internal Links Box (SEO & Pageview Booster) -->
<div class="related-posts-box" style="margin: 35px 0 25px 0; padding: 20px; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.04);">
  <h4 style="margin: 0 0 14px 0; font-size: 15px; font-weight: 800; color: #0f172a; display: flex; align-items: center; gap: 6px;">
    <span>함께 읽으면 수익 &amp; 도움 되는 추천 글</span>
  </h4>
  <ul style="margin: 0; padding: 0;">
    {links_html}
  </ul>
</div>
"""

        # Place before FAQ / conclusion if exists, or append at the end before bottom ad
        if "<div class=\"adsense-bottom\"" in html_content:
            return html_content.replace("<div class=\"adsense-bottom\"", f"{related_box}\n<div class=\"adsense-bottom\"")
        else:
            return html_content + related_box
