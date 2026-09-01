import os
import time
from playwright.sync_api import sync_playwright

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SESSION_DIR = os.path.join(BASE_DIR, "session_data")

with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(
        user_data_dir=SESSION_DIR,
        headless=True,
        viewport={"width": 1280, "height": 900},
        args=["--disable-blink-features=AutomationControlled"]
    )
    page = ctx.new_page()
    
    print("1. 티스토리 메인(tistory.com) 접속 중...")
    page.goto("https://www.tistory.com/", wait_until="domcontentloaded", timeout=30000)
    time.sleep(2)
    print("메인 페이지 URL:", page.url)
    print("메인 페이지 제목:", page.title())
    print("로그인 버튼 존재 여부 (.btn_login, .link_login):", page.locator(".btn_login, .link_login").count())
    print("프로필/로그인된 상태 요소 (.link_profile, .area_user):", page.locator(".link_profile, .area_user").count())

    print("\n2. 블로그 관리자 페이지(smartwork-lab.tistory.com/manage) 접속 중...")
    page.goto("https://smartwork-lab.tistory.com/manage", wait_until="domcontentloaded", timeout=30000)
    time.sleep(3)
    print("관리자 페이지 URL:", page.url)
    print("관리자 페이지 제목:", page.title())

    print("\n3. 글쓰기 에디터(smartwork-lab.tistory.com/manage/newpost/) 접속 중...")
    page.goto("https://smartwork-lab.tistory.com/manage/newpost/", wait_until="domcontentloaded", timeout=30000)
    time.sleep(4)
    print("에디터 페이지 URL:", page.url)
    print("에디터 페이지 제목:", page.title())
    
    # Take screenshot for diagnosis
    shot_path = os.path.join(BASE_DIR, "data", "diag_screenshot.png")
    page.screenshot(path=shot_path)
    print(f"진단 스크린샷 저장됨: {shot_path}")

    ctx.close()
