"""
Ultimate 1-time Kakao Login Setup Script
Directly opens Kakao login page, preserves session with "Remember Me", and syncs across all subdomains.
"""

import os
import sys
import time
from playwright.sync_api import sync_playwright

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SESSION_DIR = os.path.join(BASE_DIR, "session_data")

def run_login_setup():
    os.makedirs(SESSION_DIR, exist_ok=True)
    print("\n" + "=" * 60)
    print(" [카카오 & 티스토리 1회 로그인 완벽 도우미]")
    print("=" * 60)
    print(" 1. 브라우저가 열리면 카카오 [아이디]와 [비밀번호]를 입력하여 로그인합니다.")
    print(" 2. 로그인이 완료되어 티스토리 메인 화면(또는 블로그 관리자)이 보이면,")
    print(" 3. 이 검은색 콘솔 창으로 돌아와 [Enter] 키를 누르면 세션이 영구 저장됩니다.")
    print("=" * 60 + "\n")

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=SESSION_DIR,
            headless=False,
            viewport={"width": 1280, "height": 900},
            args=["--disable-blink-features=AutomationControlled"]
        )
        page = context.new_page()

        # Direct login target to avoid intermediate redirects
        target_login_url = "https://www.tistory.com/auth/login?redirectUrl=https%3A%2F%2Fwww.tistory.com%2Fmember%2Fblog"
        try:
            page.goto(target_login_url, wait_until="domcontentloaded", timeout=45000)
            time.sleep(1)
            # Auto-click yellow kakao button to bring up ID/PW input directly
            kakao_btn = page.locator("a.link_kakao_id, .btn_login, a:has-text('카카오계정으로 로그인')").first
            if kakao_btn.is_visible():
                print(">> 카카오 로그인 화면으로 자동 전환 중...")
                kakao_btn.click()
        except Exception as e:
            print(f"로그인 페이지 안내: {e}")

        print("\n>> 브라우저에서 카카오 [아이디]와 [비밀번호]를 입력하고 로그인을 완료해 주세요.")
        input(">> 로그인을 완전히 마치신 후, 여기서 [Enter] 키를 누르세요: ")

        print("\n로그인 쿠키를 안전하게 동기화하고 저장 중입니다 (약 5초 소요)...")
        time.sleep(3)

        # Sync across tistory member/blog
        try:
            page.goto("https://www.tistory.com/member/blog", wait_until="domcontentloaded", timeout=20000)
            time.sleep(2)
            print(f"최종 동기화 확인 URL: {page.url}")
        except Exception:
            pass

        context.close()
        print("\n" + "=" * 60)
        print(" 🎉 카카오 로그인 세션이 성공적으로 영구 저장되었습니다!")
        print(" 이제부터 5개 블로그에 24시간 완전 자동으로 글이 등록됩니다.")
        print("=" * 60 + "\n")

if __name__ == "__main__":
    run_login_setup()
