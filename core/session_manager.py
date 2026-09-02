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
            self.p = sync_playwright().start()
            self.browser = self.p.chromium.launch(
                headless=True,
                args=["--disable-blink-features=AutomationControlled"]
            )
            self.context = self.browser.new_context(
                viewport={"width": 1280, "height": 850},
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
            )
            self.page = self.context.new_page()

            # Go to Tistory auth page
            self.page.goto("https://www.tistory.com/auth/login", wait_until="domcontentloaded", timeout=45000)
            time.sleep(2)

            # Click Kakao login button
            kakao_btn = self.page.locator("a.link_kakao_id, .btn_login.link_kakao_id, a:has-text('카카오계정으로 로그인')").first
            if kakao_btn.is_visible():
                kakao_btn.click()
                time.sleep(3)

            # Click QR Code tab
            qr_tab = self.page.locator("button:has-text('QR코드')").first
            if qr_tab.is_visible():
                qr_tab.click()
                time.sleep(2)

            # Extract QR code data URL from canvas
            qr_data = self.page.evaluate("""() => {
                const canvas = document.querySelector('canvas');
                return canvas ? canvas.toDataURL('image/png') : null;
            }""")

            if qr_data:
                self.qr_image = qr_data
                self.status = "READY"
                logger.info(f"QR 코드 세션 준비 완료: ID={self.session_id}")
            else:
                self.status = "FAILED"
                self.error_message = "카카오 QR코드 이미지를 추출할 수 없습니다."
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

    def get_session_info(self) -> Dict[str, Any]:
        """Check status of existing storage_state.json"""
        if not os.path.exists(STORAGE_STATE_FILE):
            return {
                "exists": False,
                "status_text": "인증 세션 없음 (로그인 필요)",
                "is_valid": False,
                "last_modified": None,
                "cookie_count": 0
            }

        try:
            mtime = os.path.getmtime(STORAGE_STATE_FILE)
            last_mod_str = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")

            with open(STORAGE_STATE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)

            cookies = data.get("cookies", [])
            has_tistory = any("tistory.com" in c.get("domain", "") for c in cookies)
            has_tssession = any(c.get("name") == "TSSESSION" for c in cookies)

            return {
                "exists": True,
                "is_valid": has_tistory and has_tssession,
                "status_text": "세션 정상 가동 중" if (has_tistory and has_tssession) else "세션 파일 있음 (확인 권장)",
                "last_modified": last_mod_str,
                "cookie_count": len(cookies),
                "has_tssession": has_tssession
            }
        except Exception as e:
            return {
                "exists": False,
                "status_text": f"세션 파일 읽기 오류: {e}",
                "is_valid": False,
                "last_modified": None,
                "cookie_count": 0
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

            page.goto("https://www.tistory.com/auth/login", wait_until="domcontentloaded", timeout=45000)
            time.sleep(2)

            kakao_btn = page.locator("a.link_kakao_id, .btn_login.link_kakao_id, a:has-text('카카오계정으로 로그인')").first
            if kakao_btn.is_visible():
                kakao_btn.click()
                time.sleep(3)

            if "accounts.kakao.com" not in page.url:
                context.close()
                browser.close()
                p.stop()
                return {"success": False, "error": "카카오 로그인 페이지 접근 실패"}

            # Fill inputs
            id_input = page.locator("input[name='loginId'], #loginId, input#loginId--1").first
            pw_input = page.locator("input[name='password'], #password, input#password--2").first

            if not id_input.is_visible() or not pw_input.is_visible():
                context.close()
                browser.close()
                p.stop()
                return {"success": False, "error": "카카오 로그인 입력창을 찾을 수 없습니다."}

            id_input.fill(email)
            time.sleep(0.3)
            pw_input.fill(password)
            time.sleep(0.3)

            # Submit
            submit_btn = page.locator("button[type='submit'], .btn_g.highlight.submit").first
            submit_btn.click()
            time.sleep(5)

            curr_url = page.url
            curr_title = ""
            try:
                curr_title = page.title()
            except Exception:
                pass

            # Check if 2FA triggered
            if "추가 사용자 확인" in curr_title or "penalty_verification" in curr_url:
                context.close()
                browser.close()
                p.stop()
                return {
                    "success": False,
                    "requires_2fa": True,
                    "error": "카카오 모바일 2단계 보안 인증('추가 사용자 확인')이 필요합니다. [QR코드 로그인] 탭을 사용하시면 모바일 카카오톡으로 3초 만에 원클릭 승인하실 수 있습니다!"
                }

            # Check if login succeeded
            if ("tistory.com" in curr_url) and ("/auth/login" not in curr_url) and ("accounts.kakao.com" not in curr_url):
                os.makedirs(SESSION_DIR, exist_ok=True)
                context.storage_state(path=STORAGE_STATE_FILE)
                with open(STORAGE_STATE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                session_str = json.dumps(data)
                context.close()
                browser.close()
                p.stop()
                return {
                    "success": True,
                    "message": "카카오 계정 로그인이 성공적으로 완료되었습니다!",
                    "session_json": session_str
                }
            else:
                context.close()
                browser.close()
                p.stop()
                return {
                    "success": False,
                    "error": f"로그인 미완료 (현재 페이지: {curr_title or curr_url}). 아이디/비밀번호를 확인하거나 QR코드 로그인을 이용해주세요."
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

            os.makedirs(SESSION_DIR, exist_ok=True)
            with open(STORAGE_STATE_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            return {
                "success": True,
                "message": f"세션 데이터가 성공적으로 저장되었습니다! (쿠키 {len(data.get('cookies', []))}개)"
            }
        except Exception as e:
            return {"success": False, "error": f"JSON 파싱 실패: {e}"}

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
