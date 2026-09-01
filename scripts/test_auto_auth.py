import os
import time
from playwright.sync_api import sync_playwright

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SESSION_DIR = os.path.join(BASE_DIR, "session_data")

with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(
        user_data_dir=SESSION_DIR,
        headless=True,
        args=["--disable-blink-features=AutomationControlled"]
    )
    page = ctx.new_page()
    page.goto("https://wellness-routine.tistory.com/manage/newpost/", wait_until="domcontentloaded", timeout=30000)
    time.sleep(2)
    print("현재 URL:", page.url)

    # If login page, click kakao button
    if "auth/login" in page.url:
        print("로그인 페이지 감지. 카카오 로그인 버튼 탐색 중...")
        kakao_btn = page.locator(".btn_login.link_kakao_id, .link_kakao_id, a.link_kakao, a[href*='kakao']").first
        if kakao_btn.count() > 0 and kakao_btn.is_visible():
            print("카카오 버튼 클릭!")
            kakao_btn.click()
            time.sleep(5)
            print("클릭 후 URL:", page.url)
            print("에디터 제목 입력창 존재 여부:", page.locator("#post-title-inp").count())
        else:
            print("카카오 버튼을 찾지 못함.")
    else:
        print("이미 로그인되어 있음! 에디터 진입 성공.")

    ctx.close()
