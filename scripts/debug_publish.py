import os
import sys
import time
from playwright.sync_api import sync_playwright

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from core.tistory_bot import TistoryBot

bot = TistoryBot(headless=True)
user_data_dir = os.path.join(BASE_DIR, "data", "browser_session")

with sync_playwright() as p:
    context = p.chromium.launch_persistent_context(
        user_data_dir=bot.session_dir,
        headless=True,
        viewport={"width": 1400, "height": 900}
    )
    page = context.new_page()
    page.goto("https://smartwork-lab.tistory.com/manage/newpost/", wait_until="networkidle")
    bot._handle_kakao_login_if_needed(page)
    time.sleep(3)

    # Click 완료 button to open layer
    comp_btn = page.locator("#publish-layer-btn, button:has-text('완료'), .btn_complete").first
    print("완료 버튼 is_visible:", comp_btn.is_visible())
    if comp_btn.is_visible():
        comp_btn.click()
        time.sleep(2)
        page.screenshot(path="data/publish_layer_debug.png")
        print("Captured data/publish_layer_debug.png!")
        
        # Print all buttons/inputs in layer
        layer_items = page.evaluate("""() => {
            return Array.from(document.querySelectorAll('button, input, label, a')).map(el => ({
                tag: el.tagName,
                id: el.id,
                className: el.className,
                type: el.type || '',
                value: el.value || '',
                text: el.innerText ? el.innerText.trim() : (el.value || '')
            })).filter(x => x.text.includes('발행') || x.text.includes('공개') || x.text.includes('비공개') || x.id.includes('publish') || x.id.includes('open'));
        }""")
        for item in layer_items:
            print("LAYER ITEM:", item)

    context.close()
