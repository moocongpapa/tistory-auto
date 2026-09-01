import os
import time
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SESSION_DIR = os.path.join(BASE_DIR, "session_data")

email = os.environ.get("KAKAO_EMAIL")
password = os.environ.get("KAKAO_PASSWORD")

with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(
        user_data_dir=SESSION_DIR,
        headless=True,
        viewport={"width": 1280, "height": 900},
        args=["--disable-blink-features=AutomationControlled"]
    )
    page = ctx.new_page()
    page.goto("https://www.tistory.com/auth/login", wait_until="domcontentloaded", timeout=45000)
    time.sleep(2)

    kakao_btn = page.locator("a.link_kakao_id, .btn_login, a:has-text('카카오계정으로 로그인')").first
    if kakao_btn.is_visible():
        kakao_btn.click()
        time.sleep(3)

    if "accounts.kakao.com" in page.url:
        id_input = page.locator("input[name='loginId'], #loginId").first
        if id_input.is_visible():
            id_input.fill(email)
            time.sleep(0.5)

        pw_input = page.locator("input[name='password'], #password").first
        if pw_input.is_visible():
            pw_input.fill(password)
            time.sleep(0.5)

        submit_btn = page.locator("button[type='submit']").first
        if submit_btn.is_visible():
            submit_btn.click()
            time.sleep(6)

    shot_path = os.path.join(BASE_DIR, "data", "kakao_current_state.png")
    page.screenshot(path=shot_path)
    print("URL:", page.url)
    print("Title:", page.title())
    print("Screenshot saved to:", shot_path)
    ctx.close()
