"""
Session Manager for Kakao/Tistory Authentication
Supports:
1. Real-time Mobile QR Code Login (Canvas extraction -> Mobile scan -> Auto-capture)
2. Direct Credential Login (Email / Password automated entry)
3. Raw Session JSON Import / Export
4. Session Health & Validity Status Check
"""

import os
import time
import json
import uuid
import asyncio
import logging
import threading
from typing import Dict, Any, Optional
from datetime import datetime
from playwright.sync_api import sync_playwright
import requests

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SESSION_DIR = os.path.join(BASE_DIR, "session_data")
STORAGE_STATE_FILE = os.path.join(SESSION_DIR, "storage_state.json")

def run_in_isolated_thread(func, *args, **kwargs):
    """Executes a blocking/sync Playwright function in an isolated clean OS thread without asyncio loop."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        res = [None]
        err = [None]
        def _worker():
            try:
                asyncio.set_event_loop(None)
                res[0] = func(*args, **kwargs)
            except Exception as e:
                err[0] = e
        t = threading.Thread(target=_worker, daemon=True)
        t.start()
        t.join()
        if err[0]:
            raise err[0]
        return res[0]
    else:
        return func(*args, **kwargs)

class ActiveQRSession:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.created_at = time.time()
        self.expires_at = self.created_at + 150  # 2.5 minutes expiry
        self.status = "INITIALIZING" # INITIALIZING, READY, COMPLETED, EXPIRED, FAILED
        self.qr_image: Optional[str] = None
        self.error_message: Optional[str] = None
        self.storage_state_json: Optional[str] = None

        self.p = None
        self.browser = None
        self.context = None
        self.page = None
        self._lock = threading.Lock()

    def start(self):
        return run_in_isolated_thread(self._start_impl)

    def _start_impl(self):
        try:
            import base64
            self.p = sync_playwright().start()
            self.browser = self.p.chromium.launch(
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage"
                ]
            )
            self.context = self.browser.new_context(
                viewport={"width": 1280, "height": 850},
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
            )
            self.page = self.context.new_page()

            # Go directly to Kakao OAuth login URL (30x faster, skips intermediary redirects)
            kakao_direct_auth_url = (
                "https://accounts.kakao.com/login?continue="
                "https%3A%2F%2Fkauth.kakao.com%2Foauth%2Fauthorize"
                "%3Fclient_id%3D3e6ddd834b023f24221217e370daed18"
                "%26redirect_uri%3Dhttps%253A%252F%252Fwww.tistory.com%252Fauth%252Fkakao%252Fredirect"
                "%26response_type%3Dcode"
            )
            logger.info("카카오 OAuth 로그인 페이지 직접 연결 중...")
            self.page.goto(kakao_direct_auth_url, wait_until="domcontentloaded", timeout=25000)

            # Click QR Code tab with explicit wait
            try:
                qr_tab = self.page.locator("button:has-text('QR코드 로그인'), button:has-text('QR코드'), a:has-text('QR코드'), .btn_g:has-text('QR코드')").first
                qr_tab.wait_for(state="visible", timeout=8000)
                qr_tab.click()
            except Exception as ex:
                logger.warning(f"QR 버튼 대기 참고: {ex}")

            # Wait for QR Canvas
            canvas_loc = self.page.locator("canvas").first
            try:
                canvas_loc.wait_for(state="visible", timeout=15000)
                time.sleep(1) # Allow drawing to settle
            except Exception as ex:
                logger.warning(f"QR Canvas 대기 참고: {ex}")

            # Extract QR code data URL (Dual extraction: toDataURL + element screenshot fallback)
            qr_data = self.page.evaluate("""() => {
                const canvas = document.querySelector('canvas');
                if (canvas && canvas.width > 0 && canvas.height > 0) {
                    return canvas.toDataURL('image/png');
                }
                const img = document.querySelector('img.img_qr, .box_qr img, .area_qr img');
                if (img) return img.src;
                return null;
            }""")

            # Fallback to direct element screenshot if toDataURL returned empty
            if not qr_data and canvas_loc.is_visible():
                try:
                    shot_bytes = canvas_loc.screenshot()
                    if shot_bytes:
                        qr_data = "data:image/png;base64," + base64.b64encode(shot_bytes).decode("utf-8")
                        logger.info("스크린샷 캡처 방식으로 QR코드 이미지 추출 성공!")
                except Exception as sc_err:
                    logger.debug(f"QR 스크린샷 캡처 실패: {sc_err}")

            if qr_data:
                self.qr_image = qr_data
                self.status = "READY"
                logger.info(f"✅ 카카오 QR 코드 세션 준비 완료: ID={self.session_id}")
            else:
                self.status = "FAILED"
                self.error_message = "카카오 QR코드 이미지를 추출할 수 없습니다. (페이지 렌더링 지연)"
        except Exception as e:
            logger.error(f"QR 세션 생성 오류: {e}")
            self.status = "FAILED"
            self.error_message = str(e)

    def check_login(self) -> Dict[str, Any]:
        with self._lock:
            if self.status == "COMPLETED":
                return {
                    "status": "COMPLETED",
                    "message": "카카오 로그인이 완료되었습니다!",
                    "session_json": self.storage_state_json
                }

            if time.time() > self.expires_at:
                self.status = "EXPIRED"
                self.close()
                return {"status": "EXPIRED", "message": "QR코드 유효시간이 만료되었습니다. 다시 시도해주세요."}

            if not self.page:
                return {"status": self.status, "message": self.error_message or "세션이 종료되었습니다."}

            try:
                curr_url = self.page.url
                # Check if navigated back to Tistory and away from accounts.kakao.com
                if ("tistory.com" in curr_url) and ("/auth/login" not in curr_url) and ("accounts.kakao.com" not in curr_url) and ("kauth.kakao.com" not in curr_url):
                    logger.info(f"🎉 QR코드 로그인 성공 감지! URL: {curr_url}")
                    os.makedirs(SESSION_DIR, exist_ok=True)
                    self.context.storage_state(path=STORAGE_STATE_FILE)

                    # Read saved state
                    with open(STORAGE_STATE_FILE, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    self.storage_state_json = json.dumps(data)
                    self.status = "COMPLETED"

                    # Persist session to Database (Supabase) so it survives redeploys
                    try:
                        from core.database import DatabaseManager
                        DatabaseManager().set_setting("session_storage_state", self.storage_state_json)
                        logger.info("💾 [영구보존] 카카오 인증 세션이 클라우드 DB에 영구 저장되었습니다.")
                    except Exception as db_e:
                        logger.debug(f"DB 세션 저장 오류: {db_e}")

                    # Close browser
                    self.close()

                    return {
                        "status": "COMPLETED",
                        "message": "카카오 스마트폰 QR 로그인이 성공적으로 완료되었습니다!",
                        "session_json": self.storage_state_json
                    }

                return {
                    "status": "READY",
                    "remaining_seconds": max(0, int(self.expires_at - time.time()))
                }
            except Exception as e:
                logger.debug(f"QR 상태 체크 참고: {e}")
                return {"status": "READY", "remaining_seconds": max(0, int(self.expires_at - time.time()))}

    def close(self):
        try:
            if self.context:
                self.context.close()
            if self.browser:
                self.browser.close()
            if self.p:
                self.p.stop()
        except Exception:
            pass
        self.context = None
        self.browser = None
        self.page = None
        self.p = None


class SessionManager:
    def __init__(self):
        self.active_qr_sessions: Dict[str, ActiveQRSession] = {}
        self._cleanup_lock = threading.Lock()
        self.active_login_p = None
        self.active_login_browser = None
        self.active_login_context = None
        self.active_login_page = None
        self.manual_confirm_event = threading.Event()

    def get_session_info(self) -> Dict[str, Any]:
        """Check status of existing storage_state.json and auto-restore from DB if needed"""
        # 1. If file doesn't exist on disk or is empty, check DB persistent storage
        if not os.path.exists(STORAGE_STATE_FILE) or os.path.getsize(STORAGE_STATE_FILE) == 0:
            try:
                from core.database import DatabaseManager
                saved_json = DatabaseManager().get_setting("session_storage_state")
                if saved_json and saved_json.strip():
                    os.makedirs(SESSION_DIR, exist_ok=True)
                    with open(STORAGE_STATE_FILE, "w", encoding="utf-8") as f:
                        f.write(saved_json.strip())
                    logger.info("영구 저장소(DB)로부터 카카오 인증 세션을 성공적으로 자동 복원했습니다.")
            except Exception as e:
                logger.debug(f"DB 세션 복원 시도 참고: {e}")

        # 2. If still doesn't exist, check environment variable
        if not os.path.exists(STORAGE_STATE_FILE) or os.path.getsize(STORAGE_STATE_FILE) == 0:
            session_env = os.environ.get("SESSION_STORAGE_STATE", "").strip()
            if session_env:
                try:
                    os.makedirs(SESSION_DIR, exist_ok=True)
                    with open(STORAGE_STATE_FILE, "w", encoding="utf-8") as f:
                        f.write(session_env)
                    logger.info("환경변수로부터 카카오 인증 세션을 성공적으로 자동 복원했습니다.")
                except Exception:
                    pass

        if not os.path.exists(STORAGE_STATE_FILE) or os.path.getsize(STORAGE_STATE_FILE) == 0:
            return {
                "exists": False,
                "status_text": "인증 세션 없음 (로그인 또는 세션 등록 필요)",
                "is_valid": False,
                "last_modified": None,
                "cookie_count": 0,
                "session_json": ""
            }

        try:
            mtime = os.path.getmtime(STORAGE_STATE_FILE)
            last_mod_str = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")

            with open(STORAGE_STATE_FILE, "r", encoding="utf-8") as f:
                raw_content = f.read().strip()
                data = json.loads(raw_content)

            cookies = data.get("cookies", [])
            has_tistory = any("tistory.com" in c.get("domain", "") for c in cookies)
            has_kakao = any("kakao.com" in c.get("domain", "") for c in cookies)
            has_auth = any(c.get("name") in ("TSSESSION", "TSID", "_kawlt", "_T_", "_T_SECURE", "TI_SESSION") for c in cookies)
            is_valid = (has_tistory or has_kakao) and (has_auth or len(cookies) >= 3)

            formatted_json = json.dumps(data, ensure_ascii=False, indent=2)

            # Ensure DB is kept synchronized
            try:
                from core.database import DatabaseManager
                db_inst = DatabaseManager()
                if not db_inst.get_setting("session_storage_state"):
                    db_inst.set_setting("session_storage_state", formatted_json)
            except Exception:
                pass

            return {
                "exists": True,
                "is_valid": is_valid,
                "status_text": "세션 정상 가동 중 (인증 완료)" if is_valid else "세션 파일 등록됨",
                "last_modified": last_mod_str,
                "cookie_count": len(cookies),
                "has_tssession": any(c.get("name") == "TSSESSION" for c in cookies),
                "session_json": formatted_json
            }
        except Exception as e:
            return {
                "exists": False,
                "status_text": f"세션 파일 읽기 오류: {e}",
                "is_valid": False,
                "last_modified": None,
                "cookie_count": 0,
                "session_json": ""
            }

    def start_qr_session(self) -> Dict[str, Any]:
        """Start a new QR session in background thread and return QR code data URL"""
        self._cleanup_expired()

        session_id = str(uuid.uuid4())
        qr_sess = ActiveQRSession(session_id)
        qr_sess.start()

        if qr_sess.status == "READY":
            self.active_qr_sessions[session_id] = qr_sess
            return {
                "success": True,
                "session_id": session_id,
                "qr_image": qr_sess.qr_image,
                "expires_in": 150
            }
        else:
            qr_sess.close()
            return {
                "success": False,
                "error": qr_sess.error_message or "QR코드 생성에 실패했습니다."
            }

    def poll_qr_session(self, session_id: str) -> Dict[str, Any]:
        """Poll status of an active QR session"""
        qr_sess = self.active_qr_sessions.get(session_id)
        if not qr_sess:
            return {"status": "EXPIRED", "message": "만료되었거나 존재하지 않는 세션입니다."}

        res = qr_sess.check_login()
        if res.get("status") in ("COMPLETED", "EXPIRED", "FAILED"):
            # Can remove from active
            self.active_qr_sessions.pop(session_id, None)
        return res

    def direct_login(self, email: str, password: str) -> Dict[str, Any]:
        """Attempt direct automated login with Kakao email & password"""
        return run_in_isolated_thread(self._direct_login_impl, email, password)

    def _direct_login_impl(self, email: str, password: str) -> Dict[str, Any]:
        if not email or not password:
            return {"success": False, "error": "아이디와 비밀번호를 모두 입력해주세요."}

        p = None
        browser = None
        try:
            p = sync_playwright().start()
            browser = p.chromium.launch(
                headless=True,
                args=["--disable-blink-features=AutomationControlled"]
            )
            context = browser.new_context(
                viewport={"width": 1280, "height": 850},
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
            )
            page = context.new_page()

            # Register active session for manual confirmation from UI
            self.active_login_p = p
            self.active_login_browser = browser
            self.active_login_context = context
            self.active_login_page = page
            self.manual_confirm_event.clear()

            page.goto("https://www.tistory.com/auth/login", wait_until="domcontentloaded", timeout=45000)
            time.sleep(1)

            try:
                kakao_btn = page.locator("a.link_kakao_id, .btn_login.link_kakao_id, a:has-text('카카오계정으로 로그인')").first
                kakao_btn.wait_for(state="visible", timeout=15000)
                kakao_btn.click()
            except Exception as ex:
                logger.warning(f"카카오 로그인 버튼 대기 참고: {ex}")

            try:
                page.wait_for_url(lambda u: "accounts.kakao.com" in u, timeout=15000)
            except Exception:
                pass

            if "accounts.kakao.com" not in page.url:
                context.close()
                browser.close()
                p.stop()
                return {"success": False, "error": "카카오 로그인 페이지 접근에 실패했습니다."}

            # Fill inputs with wait
            id_input = page.locator("input[name='loginId'], #loginId, input#loginId--1").first
            pw_input = page.locator("input[name='password'], #password, input#password--2").first

            try:
                id_input.wait_for(state="visible", timeout=15000)
                pw_input.wait_for(state="visible", timeout=15000)
            except Exception:
                context.close()
                browser.close()
                p.stop()
                return {"success": False, "error": "카카오 로그인 입력창을 찾을 수 없습니다. ([📱 QR코드] 로그인을 이용해주세요)"}

            id_input.fill(email)
            time.sleep(0.3)
            pw_input.fill(password)
            time.sleep(0.3)

            # Submit
            submit_btn = page.locator("button[type='submit'], .btn_g.highlight.submit").first
            submit_btn.click()
            time.sleep(4)

            # Check for immediate Kakao error message (e.g. 해외 로그인 차단, 비밀번호 오류, CAPTCHA)
            page_error = page.evaluate("""() => {
                const errSelectors = ['.desc_error', '.info_error', 'p.error', '.txt_error', '.alert_error', '.wrap_error'];
                for (const s of errSelectors) {
                    const el = document.querySelector(s);
                    if (el && el.innerText && el.innerText.trim()) return el.innerText.trim();
                }
                const bodyText = document.body.innerText || '';
                if (bodyText.includes('비밀번호가 일치하지 않습니다') || bodyText.includes('아이디 또는 비밀번호')) return '아이디 또는 비밀번호가 일치하지 않습니다.';
                if (bodyText.includes('해외 로그인 차단')) return '카카오 계정에 [해외 로그인 차단]이 설정되어 있어 클라우드 로그인이 차단되었습니다.';
                if (bodyText.includes('자동입력 방지') || bodyText.includes('보안문자')) return '카카오 보안문자(CAPTCHA) 확인이 요구되었습니다.';
                if (bodyText.includes('보호조치')) return '카카오 계정 보호조치가 적용되었습니다.';
                return null;
            }""")
            if page_error:
                logger.warning(f"⚠️ [카카오 로그인 차단/오류 감지] {page_error}")
                context.close()
                browser.close()
                p.stop()
                return {
                    "success": False,
                    "error": f"{page_error} (카카오 보안 정책 우회를 위해 [📱 QR코드] 로그인을 이용해주세요!)"
                }

            # Try auto-clicking any '카카오톡으로 인증' or '인증 요청' button if Kakao requires triggering
            try:
                page.evaluate("""() => {
                    const allEls = Array.from(document.querySelectorAll('button, a, input[type="button"], input[type="submit"]'));
                    for (const el of allEls) {
                        const txt = (el.innerText || el.value || el.textContent || '').trim();
                        if (txt.includes('카카오톡으로 인증') || txt.includes('인증 요청') || txt.includes('인증요청') || txt.includes('기기 인증 요청')) {
                            el.click();
                            break;
                        }
                    }
                }""")
            except Exception:
                pass

            curr_url = page.url
            curr_title = ""
            try:
                curr_title = page.title()
            except Exception:
                pass

            # If not immediately on tistory.com, wait for user's mobile 2FA approval (up to 120 seconds)
            if ("tistory.com" not in curr_url) or ("accounts.kakao.com" in curr_url) or ("추가 사용자 확인" in curr_title) or ("penalty_verification" in curr_url):
                logger.info("🔔 [카카오 2단계 인증 대기] 스마트폰으로 카카오톡 인증 알림이 발송되었습니다. 폰에서 [확인]을 누르고, 웹 화면의 [승인 완료] 버튼을 누르셔도 됩니다! (최대 120초 대기 중...)")
                
                start_wait = time.time()
                wait_timeout = 120
                while time.time() - start_wait < wait_timeout:
                    # Automatically attempt to trigger or complete 2FA on webpage
                    try:
                        page.evaluate("""() => {
                            const allEls = Array.from(document.querySelectorAll('button, a, input[type="submit"], input[type="button"]'));
                            for (const el of allEls) {
                                const txt = (el.innerText || el.value || el.textContent || '').trim();
                                if (txt.includes('카카오톡으로 인증') || txt.includes('인증 요청') || txt.includes('인증요청')) {
                                    el.click();
                                    break;
                                }
                                if (txt.includes('인증 완료') || txt.includes('인증완료') || txt === '확인' || txt === '다음') {
                                    el.click();
                                    break;
                                }
                            }
                        }""")
                    except Exception:
                        pass

                    time.sleep(2.0)
                    curr_url = page.url
                    if ("tistory.com" in curr_url) and ("/auth/login" not in curr_url) and ("accounts.kakao.com" not in curr_url) and ("kauth.kakao.com" not in curr_url):
                        logger.info("🎉 [카카오 2단계 인증 성공] 사용자가 모바일에서 인증을 승인했습니다!")
                        break
                    rem = int(wait_timeout - (time.time() - start_wait))
                    if rem % 10 == 0 or rem <= 15:
                        logger.info(f"⏳ 스마트폰 카카오톡 인증 승인 대기 중... (남은 시간: {rem}초)")

            # Check if login succeeded
            curr_url = page.url
            if ("tistory.com" in curr_url) and ("/auth/login" not in curr_url) and ("accounts.kakao.com" not in curr_url):
                os.makedirs(SESSION_DIR, exist_ok=True)
                context.storage_state(path=STORAGE_STATE_FILE)
                with open(STORAGE_STATE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                session_str = json.dumps(data)

                # Persist to DB
                try:
                    from core.database import DatabaseManager
                    DatabaseManager().set_setting("session_storage_state", session_str)
                    logger.info("💾 [영구보존] 계정 직접 로그인 세션이 클라우드 DB에 영구 저장되었습니다.")
                except Exception as db_e:
                    logger.debug(f"DB 세션 저장 오류: {db_e}")

                context.close()
                browser.close()
                p.stop()
                return {
                    "success": True,
                    "message": "🎉 스마트폰 2단계 인증이 확인되어 카카오 로그인이 완벽히 완료되었습니다!",
                    "session_json": session_str
                }
            else:
                context.close()
                browser.close()
                p.stop()
                return {
                    "success": False,
                    "error": f"2단계 인증 승인 시간이 초과되었거나 취소되었습니다 (현재: {curr_title or curr_url}). 스마트폰 카카오톡 알림을 확인 후 다시 시도해주세요."
                }
        except Exception as e:
            try:
                if context:
                    context.close()
                if browser:
                    browser.close()
                if p:
                    p.stop()
            except Exception:
                pass
            return {"success": False, "error": str(e)}
        finally:
            self.active_login_page = None
            self.active_login_context = None
            self.active_login_browser = None
            self.active_login_p = None

    def confirm_2fa_manually(self) -> Dict[str, Any]:
        """Triggered when user clicks '스마트폰에서 승인 완료했습니다' button in the UI."""
        return run_in_isolated_thread(self._confirm_2fa_manually_impl)

    def _confirm_2fa_manually_impl(self) -> Dict[str, Any]:
        page = self.active_login_page
        if not page:
            info = self.get_session_info()
            if info.get("is_valid"):
                return {"success": True, "message": "카카오 인증이 이미 정상적으로 완료되었습니다!"}
            return {"success": False, "error": "현재 대기 중인 2단계 인증 세션이 없습니다. [서버에서 로그인 실행]을 먼저 눌러주세요."}

        logger.info("👆 [화면 승인 버튼 클릭 감지] 사용자가 [스마트폰에서 승인 완료했습니다] 버튼을 클릭했습니다. 브라우저 '인증 완료' 즉시 클릭...")
        self.manual_confirm_event.set()

        try:
            # Force click any confirm buttons on page
            page.evaluate("""() => {
                const allEls = Array.from(document.querySelectorAll('button, a, input[type="submit"]'));
                for (const el of allEls) {
                    const txt = (el.innerText || el.value || el.textContent || '').trim();
                    if (txt.includes('인증 완료') || txt.includes('인증완료') || txt.includes('확인') || txt === '다음') {
                        el.click();
                        break;
                    }
                }
            }""")
            time.sleep(3)
            curr_url = page.url
            if ("tistory.com" in curr_url) and ("/auth/login" not in curr_url) and ("accounts.kakao.com" not in curr_url):
                os.makedirs(SESSION_DIR, exist_ok=True)
                if self.active_login_context:
                    self.active_login_context.storage_state(path=STORAGE_STATE_FILE)
                    with open(STORAGE_STATE_FILE, "r", encoding="utf-8") as sf:
                        session_str = sf.read()
                    from core.database import DatabaseManager
                    DatabaseManager().set_setting("session_storage_state", session_str)
                logger.info("🎉 [수동 승인 성공] 카카오 2단계 인증 승인이 확인되어 세션이 영구 저장되었습니다!")
                return {"success": True, "message": "🎉 스마트폰 승인이 확인되어 카카오 로그인이 성공적으로 완료되었습니다!"}
            else:
                return {
                    "success": False,
                    "pending": True,
                    "message": "스마트폰 카카오톡 알림에서 [확인]을 누르셨는지 확인 후 2~3초 뒤 이 버튼을 다시 한번 눌러주세요."
                }
        except Exception as e:
            return {"success": False, "error": f"승인 처리 중 오류: {e}"}

    def import_session_json(self, session_json_str: str) -> Dict[str, Any]:
        """Validate and write raw JSON to storage_state.json"""
        if not session_json_str or not session_json_str.strip():
            return {"success": False, "error": "세션 JSON 문자열을 입력해주세요."}

        try:
            data = json.loads(session_json_str.strip())
            if not isinstance(data, dict):
                return {"success": False, "error": "올바른 JSON 객체 형식이 아닙니다."}

            if "cookies" not in data:
                return {"success": False, "error": "유효한 Playwright storage_state 형식이 아닙니다 (cookies 필드 누락)."}

            clean_json_str = json.dumps(data, ensure_ascii=False, indent=2)
            os.makedirs(SESSION_DIR, exist_ok=True)
            with open(STORAGE_STATE_FILE, "w", encoding="utf-8") as f:
                f.write(clean_json_str)

            # Persist to DB
            try:
                from core.database import DatabaseManager
                DatabaseManager().set_setting("session_storage_state", clean_json_str)
                logger.info("💾 [영구보존] 가져온 세션 데이터가 클라우드 DB에 영구 저장되었습니다.")
            except Exception as db_e:
                logger.debug(f"DB 세션 저장 오류: {db_e}")

            return {
                "success": True,
                "message": f"세션 데이터가 성공적으로 저장되었습니다! (쿠키 {len(data.get('cookies', []))}개)"
            }
        except Exception as e:
            return {"success": False, "error": f"JSON 파싱 실패: {e}"}

    def keep_alive_session(self) -> Dict[str, Any]:
        """
        Safety mechanism to extend session lifespan and prevent logout.
        1. Sends keep-alive request to Tistory to trigger sliding session extension.
        2. Captures any updated Set-Cookie headers from Tistory.
        3. If expired, attempts background silent OAuth re-authorization using long-term tokens.
        4. Persists renewed session to disk and Supabase DB.
        """
        if not os.path.exists(STORAGE_STATE_FILE) or os.path.getsize(STORAGE_STATE_FILE) == 0:
            self.get_session_info()

        if not os.path.exists(STORAGE_STATE_FILE) or os.path.getsize(STORAGE_STATE_FILE) == 0:
            return {"success": False, "message": "저장된 세션이 없습니다."}

        try:
            with open(STORAGE_STATE_FILE, "r", encoding="utf-8") as f:
                state_data = json.load(f)

            cookies = state_data.get("cookies", [])
            if not cookies:
                return {"success": False, "message": "세션 쿠키가 비어 있습니다."}

            req_session = requests.Session()
            req_session.headers.update({
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
            })
            for c in cookies:
                domain = c.get("domain", "").lstrip(".")
                req_session.cookies.set(c["name"], c["value"], domain=domain)

            # Ping Tistory member/blog with existing cookies
            resp = req_session.get("https://www.tistory.com/member/blog", allow_redirects=False, timeout=12)
            
            # Check if any new/updated cookies were returned by Tistory
            new_cookies_set = False
            for rc in req_session.cookies:
                for sc in cookies:
                    if sc.get("name") == rc.name and rc.value:
                        if sc.get("value") != rc.value:
                            sc["value"] = rc.value
                            new_cookies_set = True

            loc = resp.headers.get("Location", "")
            is_active = (resp.status_code == 200) or (resp.status_code == 302 and "/auth/login" not in loc and "accounts.kakao.com" not in loc)

            if is_active:
                if new_cookies_set:
                    state_data["cookies"] = cookies
                clean_json = json.dumps(state_data, ensure_ascii=False, indent=2)
                with open(STORAGE_STATE_FILE, "w", encoding="utf-8") as f:
                    f.write(clean_json)

                try:
                    from core.database import DatabaseManager
                    DatabaseManager().set_setting("session_storage_state", clean_json)
                except Exception as db_err:
                    logger.debug(f"세션 DB 갱신 동기화: {db_err}")

                logger.info("🛡️ [세션 안전장치] 티스토리 세션 수명 킵얼라이브 완료 (정상 유지 중)")
                return {
                    "success": True,
                    "renewed": True,
                    "message": "티스토리 세션 수명이 성공적으로 연장되었습니다!"
                }
            else:
                logger.info("🛡️ [세션 안전장치] 티스토리 세션 갱신 필요 감지 -> 백그라운드 자동 무인 갱신 시도...")
                return self._attempt_silent_renewal()
        except Exception as e:
            logger.debug(f"세션 킵얼라이브 실행 참고: {e}")
            return {"success": False, "error": str(e)}

    def _attempt_silent_renewal(self) -> Dict[str, Any]:
        """Attempt background re-authentication via Playwright using Kakao long-term token"""
        def _worker():
            try:
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
                    context = browser.new_context(
                        storage_state=STORAGE_STATE_FILE if os.path.exists(STORAGE_STATE_FILE) else None,
                        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
                    )
                    page = context.new_page()
                    oauth_url = "https://kauth.kakao.com/oauth/authorize?client_id=3e6ddd834b023f24221217e370daed18&redirect_uri=https%3A%2F%2Fwww.tistory.com%2Fauth%2Fkakao%2Fredirect&response_type=code"
                    try:
                        page.goto(oauth_url, wait_until="domcontentloaded", timeout=25000)
                        time.sleep(3)
                        curr_url = page.url
                        if ("tistory.com" in curr_url) and ("/auth/login" not in curr_url) and ("accounts.kakao.com" not in curr_url):
                            context.storage_state(path=STORAGE_STATE_FILE)
                            with open(STORAGE_STATE_FILE, "r", encoding="utf-8") as sf:
                                new_json = sf.read()
                            from core.database import DatabaseManager
                            DatabaseManager().set_setting("session_storage_state", new_json)
                            logger.info("🎉 [세션 안전장치] 카카오 백그라운드 무인 세션 자동 갱신 성공!")
                            return {"success": True, "renewed": True, "message": "카카오 장기 토큰을 통해 세션이 무인으로 자동 갱신되었습니다!"}
                    finally:
                        context.close()
                        browser.close()
            except Exception as e:
                logger.debug(f"무인 세션 복구 시도 참고: {e}")
            return {
                "success": False,
                "warning": True,
                "message": "카카오 세션이 만료되었습니다. 웹 대시보드 [카카오 세션 연동]에서 세션을 갱신해주세요."
            }

        return run_in_isolated_thread(_worker)

    def _cleanup_expired(self):
        with self._cleanup_lock:
            now = time.time()
            to_delete = []
            for sid, sess in self.active_qr_sessions.items():
                if now > sess.expires_at or sess.status in ("COMPLETED", "EXPIRED", "FAILED"):
                    sess.close()
                    to_delete.append(sid)
            for sid in to_delete:
                self.active_qr_sessions.pop(sid, None)

session_manager = SessionManager()
