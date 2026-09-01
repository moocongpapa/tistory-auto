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
    editor_url = "https://smartwork-lab.tistory.com/manage/newpost/"
    page.goto(editor_url, wait_until="domcontentloaded", timeout=45000)
    time.sleep(3)

    if "auth/login" in page.url:
        kakao_btn = page.locator("a.link_kakao_id, .btn_login, a:has-text('카카오계정으로 로그인')").first
        if kakao_btn.is_visible():
            kakao_btn.click()
            time.sleep(3)

    if "accounts.kakao.com" in page.url:
        id_input = page.locator("input[name='loginId'], #loginId").first
        if id_input.is_visible():
            id_input.fill(email)
            time.sleep(0.3)
        pw_input = page.locator("input[name='password'], #password").first
        if pw_input.is_visible():
            pw_input.fill(password)
            time.sleep(0.3)
        submit_btn = page.locator("button[type='submit']").first
        if submit_btn.is_visible():
            submit_btn.click()
            time.sleep(6)

    if "manage/newpost" not in page.url:
        page.goto(editor_url, wait_until="domcontentloaded", timeout=30000)
        time.sleep(4)

    print("최종 URL:", page.url)
    print("페이지 제목:", page.title())

    # Find and print all buttons
    buttons = page.locator("button, a.btn_g, a.btn, input[type='button']")
    print(f"발견된 버튼 총 개수: {buttons.count()}")
    for i in range(buttons.count()):
        btn = buttons.nth(i)
        try:
            txt = btn.inner_text().strip().replace("\n", " ")
            cls = btn.get_attribute("class") or ""
            btn_id = btn.get_attribute("id") or ""
            vis = btn.is_visible()
            print(f"[{i}] id='{btn_id}' class='{cls}' visible={vis} text='{txt}'")
        except Exception:
            pass

    shot_path = os.path.join(BASE_DIR, "data", "actual_editor_screenshot.png")
    page.screenshot(path=shot_path)
    print(f"실제 에디터 스크린샷: {shot_path}")
    ctx.close()
