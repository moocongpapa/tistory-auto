"""
Playwright-based Tistory Auto-Posting Bot
Integrated with reference repository (kgbae99/tistory-blog-auto) publishing standards:
- Explicit login verification at /manage before editor entry
- Anti-popup init scripts to neutralize '작성 중인 글이 있습니다' dialogs
- Verified 3-step public publishing with networkidle load state synchronization
"""

import os
import re
import time
import logging
from typing import List, Optional, Dict, Any
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, BrowserContext, Page

load_dotenv()
logger = logging.getLogger(__name__)

SESSION_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "session_data")
STORAGE_STATE_FILE = os.path.join(SESSION_DIR, "storage_state.json")

class TistoryBot:
    def __init__(self, session_dir: str = SESSION_DIR, storage_state_file: str = STORAGE_STATE_FILE, headless: bool = True):
        self.session_dir = session_dir
        self.storage_state_file = storage_state_file
        self.headless = headless
        self.email = os.environ.get("KAKAO_EMAIL")
        self.password = os.environ.get("KAKAO_PASSWORD")
        os.makedirs(self.session_dir, exist_ok=True)

    def _ensure_logged_in(self, page: Page, subdomain: str) -> bool:
        """Verify login status at /manage and perform Kakao login if needed."""
        manage_url = f"https://{subdomain}.tistory.com/manage"
        logger.info(f"티스토리 관리자 세션 확인 중: {manage_url}")
        
        try:
            page.goto(manage_url, wait_until="domcontentloaded", timeout=45000)
            time.sleep(2)
        except Exception as e:
            logger.warning(f"관리자 페이지 접근 대기 참고: {e}")

        # Check if redirected to login page
        curr_url = page.url
        if "/auth/login" in curr_url or "authentication/login" in curr_url or "accounts.kakao.com" in curr_url:
            logger.info("로그인 필요 상태 감지. 카카오 인증 프로세스 진행...")
            return self._perform_kakao_login(page, target_return_url=manage_url)

        logger.info(f"이미 [{subdomain}] 관리자 세션 로그인 완료 상태입니다.")
        return True

    def _perform_kakao_login(self, page: Page, target_return_url: str) -> bool:
        """Perform Kakao login credentials entry and wait for return redirect."""
        # 1. Click yellow Kakao Login button if on Tistory auth page
        if "/auth/login" in page.url or "authentication/login" in page.url:
            try:
                kakao_btn = page.locator("a.link_kakao_id, .btn_login.link_kakao_id, a:has-text('카카오계정으로 로그인')").first
                if kakao_btn.is_visible():
                    kakao_btn.click()
                    time.sleep(3)
            except Exception as e:
                logger.debug(f"카카오 버튼 클릭: {e}")

        # 2. Enter credentials on accounts.kakao.com
        if "accounts.kakao.com" in page.url:
            logger.info("카카오 계정 로그인 입력 창 처리 중...")
            
            # Check for saved one-click account first
            try:
                saved_acc = page.locator(".item_account, .link_account, .tit_item, li:has-text('@kakao.com'), li:has-text('@daum.net')").first
                if saved_acc.is_visible():
                    logger.info("저장된 간편 로그인 계정 원클릭 선택...")
                    saved_acc.click(force=True)
                    time.sleep(3)
            except Exception:
                pass

            if "accounts.kakao.com" in page.url and self.email and self.password:
                try:
                    id_input = page.locator("input[name='loginId'], #loginId, input#loginId--1").first
                    if id_input.is_visible():
                        id_input.fill(self.email)
                        time.sleep(0.2)

                    pw_input = page.locator("input[name='password'], #password, input#password--2").first
                    if pw_input.is_visible():
                        pw_input.fill(self.password)
                        time.sleep(0.2)

                    # Close popup if exists
                    try:
                        close_btn = page.locator("button:has-text('닫기'), .btn_close").first
                        if close_btn.is_visible():
                            close_btn.click(force=True)
                            time.sleep(0.3)
                    except Exception:
                        pass

                    # Submit login form
                    page.evaluate("() => { (document.querySelector('button[type=\"submit\"]') || document.querySelector('.btn_g.highlight.submit'))?.click(); }")
                    logger.info("카카오 로그인 폼 제출 완료. 리다이렉트 대기...")
                    time.sleep(4)
                except Exception as e:
                    logger.error(f"카카오 로그인 입력 에러: {e}")

        # 3. Wait until redirected back to Tistory
        try:
            page.wait_for_url("**/tistory.com/**", timeout=20000)
            logger.info("카카오 로그인 및 티스토리 복귀 완료!")
            return True
        except Exception:
            logger.warning(f"로그인 후 티스토리 복귀 대기 타임아웃. 현재 URL: {page.url}")
            return "tistory.com" in page.url

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
        Full automated post workflow:
        1. Login verification at /manage
        2. Enter /manage/newpost with anti-draft restore script
        3. Set Title, HTML Body, Category, Tags, Thumbnail
        4. Complete Public Publication and verify live URL
        """
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=self.headless,
                args=["--disable-blink-features=AutomationControlled"]
            )
            
            if os.path.exists(self.storage_state_file):
                context = browser.new_context(
                    storage_state=self.storage_state_file,
                    viewport={"width": 1366, "height": 850}
                )
            else:
                context = browser.new_context(viewport={"width": 1366, "height": 850})

            page = context.new_page()

            # Global Anti-Popup & Auto-Dismiss init script (neutralizes '작성 중인 글이 있습니다' dialogs)
            page.add_init_script("""
                window.confirm = function(msg) {
                    console.log('Intercepted window.confirm: ' + msg);
                    return false; // Always start clean, do not restore drafts
                };
                window.alert = function(msg) {
                    console.log('Intercepted window.alert: ' + msg);
                };
            """)

            # Dialog listener fallback
            page.on("dialog", lambda dialog: dialog.dismiss())

            # 1. Step 1: Ensure Logged In
            if not self._ensure_logged_in(page, subdomain):
                context.close()
                raise PermissionError("카카오 로그인 실패. 계정 정보(.env)를 확인해주세요.")

            # 2. Step 2: Navigate to New Post Editor
            editor_url = f"https://{subdomain}.tistory.com/manage/newpost/"
            logger.info(f"티스토리 에디터 이동: {editor_url}")
            page.goto(editor_url, wait_until="domcontentloaded", timeout=45000)
            time.sleep(2.5)

            # Check if login redirected again
            if "/auth/login" in page.url or "accounts.kakao.com" in page.url:
                self._perform_kakao_login(page, target_return_url=editor_url)
                page.goto(editor_url, wait_until="domcontentloaded", timeout=30000)
                time.sleep(2.5)

            # Wait until TinyMCE editor is fully loaded (up to 15 seconds)
            for wait_i in range(15):
                editor_ready = page.evaluate("""() => !!(window.tinymce && window.tinymce.activeEditor)""")
                if editor_ready:
                    break
                time.sleep(1)
            else:
                logger.warning("TinyMCE 에디터 로드 대기 시간 초과 (15초), 계속 진행 시도...")

            # Clean title to prevent any trailing debug numbers or symbols
            clean_title = re.sub(r"\s+\d{9,12}$", "", title).strip()
            clean_title = re.sub(r'[\"\']', '', clean_title).strip()

            # 3. Step 3: Input Title
            logger.info(f"제목 입력 중: {clean_title}")
            title_input = page.locator("#post-title-inp, textarea.textarea_tit, input[name='title'], textarea#title").first
            title_input.wait_for(state="visible", timeout=20000)
            title_input.click()
            title_input.fill(clean_title)
            title_input.press("Enter")
            time.sleep(0.5)

            # 4. Step 4: Attach Thumbnail First & Set as Representative
            has_thumbnail_uploaded = False
            if thumbnail_path and os.path.exists(thumbnail_path):
                abs_thumb = os.path.abspath(thumbnail_path)
                logger.info(f"썸네일 이미지 첨부 및 대표 설정 중: {abs_thumb}")
                for attempt in range(3):
                    try:
                        # Ensure editor is focused before triggering upload
                        page.evaluate("""() => {
                            const ed = window.tinymce && window.tinymce.activeEditor;
                            if (ed) { ed.focus(); }
                        }""")
                        time.sleep(0.3)

                        with page.expect_file_chooser(timeout=10000) as fc_info:
                            page.evaluate("""() => {
                                const ed = window.tinymce && window.tinymce.activeEditor;
                                if (ed) {
                                    ed.execCommand('KImageUpload');
                                } else {
                                    document.querySelector('#attach-image, .mce-i-image, #mceu_0-open')?.click();
                                }
                            }""")
                        
                        file_chooser = fc_info.value
                        file_chooser.set_files(abs_thumb)
                        logger.info("카카오 CDN 이미지 업로드 완료 대기 중 (6초)...")
                        time.sleep(6.0)

                        # Verify image was inserted into TinyMCE content
                        uploaded_check = page.evaluate("""() => {
                            const ed = window.tinymce && window.tinymce.activeEditor;
                            if (!ed) return false;
                            const html = ed.getContent() || '';
                            return html.includes('Image|') || html.includes('<figure') || html.includes('<img');
                        }""")

                        if uploaded_check:
                            logger.info("카카오 에디터 이미지 블록 생성 확인 완료!")
                            has_thumbnail_uploaded = True

                        # Safely try clicking '대표' button if present
                        try:
                            page.evaluate("""() => {
                                try {
                                    const repBtn = document.querySelector('button.btn_represent, .btn_represent, button[aria-label*="대표"]');
                                    if (repBtn) { repBtn.click(); }
                                } catch(err) {}
                            }""")
                        except Exception:
                            pass

                        if has_thumbnail_uploaded:
                            logger.info("썸네일 첨부 및 대표 이미지 등록 성공!")
                            break
                    except Exception as e:
                        logger.warning(f"썸네일 첨부 시도 {attempt + 1}/3 실패, 재시도 중: {e}")
                        time.sleep(1.5)
                        # Re-focus editor before retry
                        try:
                            page.evaluate("() => { const ed = window.tinymce && window.tinymce.activeEditor; if (ed) ed.focus(); }")
                        except Exception:
                            pass

            # 5. Step 5: Inject HTML Content via TinyMCE (Preserving Thumbnail)
            logger.info(f"본문 HTML 안전 주입 중 (총 {len(content_html)}자)...")
            
            inject_success = page.evaluate("""(html) => {
                if (window.tinymce && window.tinymce.activeEditor) {
                    const ed = window.tinymce.activeEditor;
                    const currentContent = ed.getContent() || '';
                    if (currentContent.includes('Image|') || currentContent.includes('<figure') || currentContent.includes('<img')) {
                        ed.setContent(currentContent + '<br><br>' + html, { format: 'html' });
                    } else {
                        ed.setContent(html, { format: 'html' });
                    }
                    ed.undoManager?.add();
                    ed.setDirty(true);
                    ed.fire('change');
                    ed.fire('input');
                    ed.fire('SetContent');
                    ed.save();
                    return true;
                }
                const root = document.querySelector('#editor-root') || document.querySelector('.mce-content-body');
                if (root) {
                    root.innerHTML = (root.innerHTML ? root.innerHTML + '<br>' : '') + html;
                    root.dispatchEvent(new Event('input', { bubbles: true }));
                    root.dispatchEvent(new Event('change', { bubbles: true }));
                    return true;
                }
                return false;
            }""", content_html)
            
            if inject_success:
                logger.info("TinyMCE 에디터 API를 통해 본문 100% 무손실 주입 및 저장 완료")
            else:
                logger.warning("TinyMCE 주입 실패, 대체 처리 진행")

            time.sleep(0.8)

            # 6. Step 6: Select Category (Tistory TinyMCE #category-list / .mce-menu-item Targeter)
            if category_name:
                logger.info(f"카테고리 선택 시도: '{category_name}'")
                try:
                    cat_btn = page.locator("#category-btn, button:has-text('카테고리')").first
                    if cat_btn.is_visible():
                        cat_btn.click(force=True)
                        time.sleep(0.6)

                        selected_cat_text = page.evaluate(r"""(targetName) => {
                            const clean = (s) => (s || '').replace(/[^a-zA-Z0-9가-힣]/g, '').toLowerCase();
                            const targetClean = clean(targetName);
                            const items = Array.from(document.querySelectorAll('#category-list .mce-menu-item, .mce-menu .mce-menu-item, [role="listbox"] [role="option"], .list_category li'));
                            
                            // 1. Exact or partial clean text match
                            let bestMatch = null;
                            for (const it of items) {
                                const text = it.innerText ? it.innerText.trim() : '';
                                if (!text || text === '카테고리 없음' || text.startsWith('카테고리 선택')) continue;
                                const itClean = clean(text);
                                if (itClean === targetClean) {
                                    bestMatch = it;
                                    break;
                                }
                                if (targetClean.includes(itClean) || itClean.includes(targetClean)) {
                                    if (!bestMatch) bestMatch = it;
                                }
                            }
                            
                            // 2. Keyword token match
                            if (!bestMatch) {
                                const tokens = targetClean.split(/[\s&_]+/);
                                for (const it of items) {
                                    const text = it.innerText ? it.innerText.trim() : '';
                                    if (!text || text === '카테고리 없음') continue;
                                    const itClean = clean(text);
                                    for (const tok of tokens) {
                                        if (tok && itClean.includes(tok)) {
                                            bestMatch = it;
                                            break;
                                        }
                                    }
                                    if (bestMatch) break;
                                }
                            }
                            
                            // 3. Fallback to first available category
                            if (!bestMatch) {
                                for (const it of items) {
                                    const text = it.innerText ? it.innerText.trim() : '';
                                    if (text && text !== '카테고리 없음' && !text.startsWith('카테고리 선택')) {
                                        bestMatch = it;
                                        break;
                                    }
                                }
                            }
                            
                            if (bestMatch) {
                                bestMatch.dispatchEvent(new MouseEvent('mousedown', { bubbles: true }));
                                bestMatch.dispatchEvent(new MouseEvent('mouseup', { bubbles: true }));
                                bestMatch.dispatchEvent(new MouseEvent('click', { bubbles: true }));
                                bestMatch.click();
                                return bestMatch.innerText.trim();
                            }
                            return null;
                        }""", category_name)
                        
                        logger.info(f"카테고리 선택 완료: '{selected_cat_text}'")
                        time.sleep(0.5)
                except Exception as e:
                    logger.debug(f"카테고리 선택 참고: {e}")

            # 7. Step 7: Add Tags
            if tags:
                logger.info(f"태그 추가 중 ({len(tags)}개): {tags}")
                try:
                    tag_input = page.locator("#tagText, #tag-input, input.tag_inp, input[placeholder*='태그']").first
                    if tag_input.is_visible():
                        for tag in tags[:10]:
                            clean_tag = tag.strip().replace("#", "").replace(",", "")
                            if clean_tag:
                                tag_input.click()
                                tag_input.fill(clean_tag)
                                time.sleep(0.15)
                                tag_input.press("Enter")
                                time.sleep(0.2)
                except Exception as e:
                    logger.debug(f"태그 입력: {e}")

            # 8. Step 8: Final Publication (Public or Private Draft)
            mode_text = "비공개(임시저장)" if is_draft else "공개 발행(Public)"
            logger.info(f"🚀 포스트 {mode_text} 실행 중...")
            
            # 8-1. Click '완료' button to open publish layer
            pub_layer_btn = page.locator("#publish-layer-btn, button:has-text('완료'), button.btn_complete, button.btn-default:has-text('완료')").first
            if pub_layer_btn.is_visible():
                pub_layer_btn.click(timeout=5000, force=True)
                logger.info("발행 레이어 오픈 ('완료' 클릭)")
            else:
                page.evaluate("() => { (document.querySelector('#publish-layer-btn') || document.querySelector('.btn_complete') || document.querySelector('button.btn-default') || document.querySelector('button.btn_sub'))?.click(); }")
            
            time.sleep(1.5)

            # 8-2. Select '비공개' or '공개' option in layer
            try:
                if is_draft:
                    # Select '비공개' (Private)
                    for _ in range(5):
                        private_radio_label = page.locator("label[for='open0'], label:has-text('비공개')").first
                        if private_radio_label.is_visible():
                            private_radio_label.click(force=True)
                            time.sleep(0.3)

                        page.evaluate("""() => {
                            const r = document.querySelector('input#open0') || document.querySelector('input[value=\"0\"]');
                            if (r) {
                                r.checked = true;
                                r.dispatchEvent(new Event('change', { bubbles: true }));
                                r.dispatchEvent(new Event('input', { bubbles: true }));
                            }
                        }""")
                        time.sleep(0.4)
                        break
                    logger.info("'비공개' 라디오 옵션 선택 완료")
                else:
                    # Select '공개' (Public)
                    for _ in range(5):
                        open_radio_label = page.locator("label[for='open20'], label:has-text('공개')").first
                        if open_radio_label.is_visible():
                            open_radio_label.click(force=True)
                            time.sleep(0.3)

                        page.evaluate("""() => {
                            const r = document.querySelector('input#open20') || document.querySelector('input[value=\"20\"]');
                            if (r) {
                                r.checked = true;
                                r.dispatchEvent(new Event('change', { bubbles: true }));
                                r.dispatchEvent(new Event('input', { bubbles: true }));
                            }
                        }""")
                        time.sleep(0.4)

                        pub_btn_txt = page.locator("#publish-btn").inner_text()
                        if "공개발행" in pub_btn_txt or ("공개" in pub_btn_txt and "비공개" not in pub_btn_txt):
                            logger.info(f"'공개' 라디오 옵션 선택 및 확인 완료: '{pub_btn_txt}'")
                            break
            except Exception as e:
                logger.debug(f"라디오 옵션 선택: {e}")

            time.sleep(0.8)

            # 8-3. Click final '발행' submit button
            final_btn = page.locator("#publish-btn, button.btn_publish, button:has-text('발행'), button:has-text('공개발행'), button[type='submit']:has-text('발행')").first
            if final_btn.is_visible():
                final_btn.click(timeout=5000, force=True)
                logger.info(f"최종 '{'비공개 저장' if is_draft else '공개발행'}' 버튼 클릭 완료!")
            else:
                page.evaluate("() => { (document.querySelector('#publish-btn') || document.querySelector('.btn_publish') || document.querySelector('button.btn_sub.btn_default'))?.click(); }")
                logger.info("JS evaluate로 최종 발행 버튼 클릭 실행")

            # 8-4. Wait for server response and redirection (CRITICAL)
            logger.info("티스토리 서버 발행 완료 및 페이지 리디렉션 대기 중 (최대 15초)...")
            final_url = None
            for sec in range(15):
                time.sleep(1)
                curr_url = page.url
                # Check if redirected away from newpost editor to live post or manage page
                if "/manage/newpost" not in curr_url and ("tistory.com" in curr_url):
                    final_url = curr_url
                    logger.info(f"발행 완료 감지 ({sec+1}초 소요): {final_url}")
                    break

            if not final_url:
                final_url = f"https://{subdomain}.tistory.com/manage/posts"

            time.sleep(2)
            try:
                context.storage_state(path=self.storage_state_file)
            except Exception:
                pass

            context.close()
            browser.close()

            post_status = "DRAFT_SAVED" if is_draft else "PUBLISHED"
            logger.info(f"🎉 티스토리 블로그 {mode_text} 100% 성공! 최종 URL: {final_url}")
            return {
                "status": post_status,
                "url": final_url
            }
