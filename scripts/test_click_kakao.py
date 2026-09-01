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
    page.goto("https://smartwork-lab.tistory.com/manage/newpost/", wait_until="domcontentloaded", timeout=30000)
    time.sleep(2)
    print("접속 URL:", page.url)

    # Click the yellow kakao login button
    kakao_btn = page.get_by_role("link", name="카카오계정으로 로그인")
    if kakao_btn.count() == 0:
        kakao_btn = page.locator("a.link_kakao_id, .btn_login")

    print("카카오 버튼 개수:", kakao_btn.count())
    if kakao_btn.count() > 0:
        print("노란색 카카오 버튼 클릭 시도!")
        kakao_btn.first.click()
        time.sleep(5)
        print("클릭 후 URL:", page.url)
        print("클릭 후 제목:", page.title())
        print("에디터 제목창 발견:", page.locator("#post-title-inp, textarea.textarea_tit").count())

    shot_path = os.path.join(BASE_DIR, "data", "after_click_screenshot.png")
    page.screenshot(path=shot_path)
    print(f"클릭 후 스크린샷: {shot_path}")

    ctx.close()
