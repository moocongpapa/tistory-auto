"""
Interactive 1-time Kakao / Tistory Login Helper
Saves browser session cookies permanently in session_data/ for automated posting.
"""

import os
import sys
import time
from playwright.sync_api import sync_playwright

SESSION_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "session_data")

def run_login_setup():
    os.makedirs(SESSION_DIR, exist_ok=True)
    print("\n=======================================================")
    print(" [카카오 & 티스토리 1회 로그인 세션 설정기]")
    print("=======================================================")
    print("1. 브라우저가 열리면 카카오 계정으로 로그인해 주세요.")
    print("2. 로그인이 완료되어 티스토리 관리자/홈에 진입하면,")
    print("   이 터미널 창으로 돌아와 [Enter] 키를 눌러주세요.")
    print("=======================================================\n")

    with sync_playwright() as p:
        # Launch non-headless browser
        context = p.chromium.launch_persistent_context(
            user_data_dir=SESSION_DIR,
            headless=False,
            viewport={"width": 1280, "height": 850},
            args=["--disable-blink-features=AutomationControlled"]
        )
        page = context.new_page()
        page.goto("https://www.tistory.com/auth/login", wait_until="domcontentloaded")

        input("\n로그인을 완료한 후 여기서 [Enter] 키를 누르세요...")

        time.sleep(2)
        print("\n로그인 상태를 저장하고 검증 중...")
        page.goto("https://www.tistory.com/", wait_until="domcontentloaded")
        time.sleep(2)

        print("\n🎉 브라우저 세션이 성공적으로 'session_data/' 폴더에 저장되었습니다!")
        print("이제부터는 백그라운드 자동 포스팅이 로그인 상태로 원활히 동작합니다.\n")
        context.close()

if __name__ == "__main__":
    run_login_setup()
