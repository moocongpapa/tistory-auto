"""
Playwright-based Tistory Auto-Posting Bot with Persistent Session Support
"""

import os
import time
import logging
from typing import List, Optional, Dict, Any
from playwright.sync_api import sync_playwright, BrowserContext, Page

logger = logging.getLogger(__name__)

SESSION_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "session_data")

class TistoryBot:
    def __init__(self, session_dir: str = SESSION_DIR, headless: bool = True):
        self.session_dir = session_dir
        self.headless = headless
        os.makedirs(self.session_dir, exist_ok=True)

    def is_logged_in(self, test_subdomain: Optional[str] = None) -> bool:
        """Verify if the saved Kakao/Tistory session is active."""
        with sync_playwright() as p:
            context = p.chromium.launch_persistent_context(
                user_data_dir=self.session_dir,
                headless=True,
                viewport={"width": 1280, "height": 800},
                args=["--disable-blink-features=AutomationControlled"]
            )
            page = context.new_page()
            try:
                target_url = f"https://{test_subdomain}.tistory.com/manage" if test_subdomain else "https://www.tistory.com/"
                page.goto(target_url, wait_until="domcontentloaded", timeout=30000)
                time.sleep(2)
                # Check for login indicators or presence of user profile / write button
                current_url = page.url
                logged_in = "auth/login" not in current_url and ("manage" in current_url or page.locator(".link_profile, .area_user, .btn_write").count() > 0)
                return logged_in
            except Exception as e:
                logger.error(f"Error checking login status: {e}")
                return False
            finally:
                context.close()

    def post_article(
        self,
        subdomain: str,
        title: str,
        content_html: str,
        tags: List[str],
        thumbnail_path: Optional[str] = None,
        category_name: Optional[str] = None,
        is_draft: bool = False
    ) -> Dict[str, Any]:
        """
        Open Tistory Editor, set title, inject HTML content, add tags, set thumbnail, and publish.
        """
        with sync_playwright() as p:
            context = p.chromium.launch_persistent_context(
                user_data_dir=self.session_dir,
                headless=self.headless,
                viewport={"width": 1280, "height": 900},
                args=["--disable-blink-features=AutomationControlled"]
            )
            page = context.new_page()

            # Handle alert dialogs (e.g. "작성 중인 글이 있습니다")
            def handle_dialog(dialog):
                logger.info(f"Dialog detected: {dialog.message}")
                dialog.accept() # Or dismiss if restoring draft

            page.on("dialog", handle_dialog)

            editor_url = f"https://{subdomain}.tistory.com/manage/newpost/"
            logger.info(f"Opening Tistory editor: {editor_url}")
            page.goto(editor_url, wait_until="domcontentloaded", timeout=45000)
            time.sleep(3)

            # Check if redirected to login
            if "auth/login" in page.url or "accounts.kakao.com" in page.url:
                context.close()
                raise PermissionError("카카오 로그인이 필요합니다. 먼저 scripts/setup_login.py를 실행하여 로그인해주세요.")

            # 1. Input Title
            logger.info("Setting title...")
            title_input = page.locator("#post-title-inp, textarea.textarea_tit, input[name='title']").first
            title_input.wait_for(state="visible", timeout=15000)
            title_input.fill(title)
            time.sleep(1)

            # 2. Switch to HTML Mode & Inject Content
            logger.info("Switching to HTML mode and injecting content...")
            # Click mode switcher if present
            try:
                mode_btn = page.locator("#editor-mode-layer-btn-open, button:has-text('기본모드'), button.btn_mode").first
                if mode_btn.is_visible():
                    mode_btn.click()
                    time.sleep(1)
                    html_option = page.locator("#editor-mode-html, button:has-text('HTML'), li:has-text('HTML')").first
                    if html_option.is_visible():
                        html_option.click()
                        time.sleep(1)
            except Exception as e:
                logger.debug(f"Mode toggle button note: {e}")

            # Try direct HTML textarea injection or JS evaluate
            html_inserted = False
            html_textarea = page.locator("#editor-mode-html-textarea, textarea.mce-textbox, textarea.CodeMirror-textarea").first
            if html_textarea.is_visible():
                html_textarea.fill(content_html)
                html_inserted = True
                time.sleep(1)
            
            if not html_inserted:
                # Direct DOM injection fallback into editor body
                page.evaluate(
                    """(html) => {
                        const editor = document.querySelector('#editor-root') || document.querySelector('.mce-content-body') || document.querySelector('#content');
                        if (editor) {
                            editor.innerHTML = html;
                        }
                    }""",
                    content_html
                )

            # 3. Add Tags
            if tags:
                logger.info(f"Adding tags: {tags}")
                tag_input = page.locator("#tagText, input.tag_inp, input[placeholder*='태그']").first
                if tag_input.is_visible():
                    for tag in tags[:8]:
                        clean_tag = tag.strip().replace("#", "")
                        if clean_tag:
                            tag_input.fill(clean_tag)
                            tag_input.press("Enter")
                            time.sleep(0.3)

            # 4. Upload Thumbnail / Image (if available)
            if thumbnail_path and os.path.exists(thumbnail_path):
                logger.info(f"Attaching thumbnail image: {thumbnail_path}")
                try:
                    file_input = page.locator("input[type='file'][accept*='image']").first
                    if file_input.count() > 0:
                        file_input.set_input_files(thumbnail_path)
                        time.sleep(2)
                except Exception as e:
                    logger.warning(f"Thumbnail upload notice: {e}")

            # 5. Select Category (optional)
            if category_name:
                try:
                    cat_btn = page.locator("#category-btn, .btn_category").first
                    if cat_btn.is_visible():
                        cat_btn.click()
                        time.sleep(0.5)
                        target_cat = page.locator(f".item_category:has-text('{category_name}')").first
                        if target_cat.is_visible():
                            target_cat.click()
                            time.sleep(0.5)
                except Exception as e:
                    logger.debug(f"Category selection notice: {e}")

            # 6. Final Publish or Draft
            if is_draft:
                logger.info("Saving post as draft...")
                save_btn = page.locator("button:has-text('저장'), #temp-save-btn, button.btn_save").first
                save_btn.click()
                time.sleep(3)
                context.close()
                return {"status": "DRAFT_SAVED", "url": None}
            else:
                logger.info("Publishing post...")
                publish_layer_btn = page.locator("#publish-layer-btn, button:has-text('완료'), button.btn_complete").first
                publish_layer_btn.click()
                time.sleep(1.5)

                # Click final publish button in layer
                final_publish_btn = page.locator("#publish-btn, button:has-text('공개발행'), button.btn_publish").first
                final_publish_btn.click()
                time.sleep(5)

                # Extract post URL from redirected page
                published_url = page.url
                logger.info(f"Published successfully! URL: {published_url}")
                context.close()
                return {"status": "PUBLISHED", "url": published_url}
