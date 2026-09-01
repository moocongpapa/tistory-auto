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
    page.goto("https://smartwork-lab.tistory.com/manage/newpost/", wait_until="domcontentloaded", timeout=45000)
    time.sleep(4)
    print("현재 URL:", page.url)

    # Inspect all buttons in editor
    buttons = page.locator("button, a.btn_g, a.btn, input[type='button'], input[type='submit']")
    print(f"에디터 내 버튼 총 개수: {buttons.count()}")
    for i in range(buttons.count()):
        btn = buttons.nth(i)
        try:
            txt = btn.inner_text().strip().replace("\n", " ")
            cls = btn.get_attribute("class") or ""
            btn_id = btn.get_attribute("id") or ""
            vis = btn.is_visible()
            if txt or "save" in cls or "complete" in cls or "publish" in cls:
                print(f"[{i}] id='{btn_id}' class='{cls}' visible={vis} text='{txt}'")
        except Exception:
            pass

    shot_path = os.path.join(BASE_DIR, "data", "editor_buttons_screenshot.png")
    page.screenshot(path=shot_path)
    print(f"스크린샷 저장: {shot_path}")
    ctx.close()
