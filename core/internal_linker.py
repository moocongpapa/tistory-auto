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
                # Must not be a manage URL, admin page, or root domain
                if not url or url == "#" or "/manage" in url or "/newpost" in url or "m.tistory" in url:
                    continue
                # Strictly enforce exact public post URLs (e.g. https://domain.tistory.com/123 or https://domain.tistory.com/entry/slug)
                if re.match(r"^https?://[a-zA-Z0-9-]+\.tistory\.com/(\d+|entry/[^/]+)/?$", url):
                    # Exclude self if current_keyword is too similar to title
                    title = p.get("title", "")
                    if current_keyword and current_keyword.strip() in title:
                        continue
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

    def inject_internal_links(self, html_content: str, blog_id: str, current_keyword: str = "", count: int = 2, language: str = "ko") -> str:
        """Inject a modern, responsive 'Together Reading / Related Posts' box into the article."""
        related = self.get_related_posts(blog_id, current_keyword, limit=count)
        if not related:
            return html_content

        box_title = "📚 Helpful Related Guides & Recommended Reading" if language == "en" else "함께 읽으면 수익 &amp; 도움 되는 추천 글"
        btn_text = "Read More &gt;" if language == "en" else "바로보기 &gt;"

        links_html = ""
        for post in related:
            title = post.get("title", "Related Article" if language == "en" else "관련 추천 글")
            url = post.get("post_url", "").strip()
            if not url or "/manage" in url or not re.match(r"^https?://[a-zA-Z0-9-]+\.tistory\.com/(\d+|entry/[^/]+)/?$", url):
                continue
            links_html += f"""
<li style="margin-bottom: 10px; padding: 12px 16px; background: #f8fafc; border-radius: 8px; border-left: 3px solid #3b82f6; list-style: none;">
  <a href="{url}" style="color: #1e293b; text-decoration: none; font-weight: 600; font-size: 14px; display: flex; align-items: center; justify-content: space-between;" target="_blank" rel="noopener noreferrer">
    <span style="display: flex; align-items: center; gap: 6px;">📌 {title}</span>
    <span style="font-size: 12px; color: #2563eb; font-weight: 700; margin-left: 12px; white-space: nowrap;">{btn_text}</span>
  </a>
</li>
"""
        if not links_html.strip():
            return html_content

        related_box = f"""
<!-- Related Posts Internal Links Box (SEO & Pageview Booster) -->
<div class="related-posts-box" style="margin: 35px 0 25px 0; padding: 20px; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.04);">
  <h4 style="margin: 0 0 14px 0; font-size: 15px; font-weight: 800; color: #0f172a; display: flex; align-items: center; gap: 6px;">
    <span>{box_title}</span>
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
