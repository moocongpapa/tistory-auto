import os
import sys
import time
from playwright.sync_api import sync_playwright

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
session_dir = os.path.join(BASE_DIR, "session_data")

with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(user_data_dir=session_dir, headless=True)
    page = ctx.new_page()
    page.goto("https://www.tistory.com/auth/login", wait_until="networkidle")
    time.sleep(2)
    
    kakao_btn = page.locator("a.link_kakao_id, .btn_login.link_kakao_id").first
    if kakao_btn.is_visible():
        kakao_btn.click()
        time.sleep(3)
        
    page.screenshot(path="data/kakao_login_state.png")
    print("Saved data/kakao_login_state.png, URL:", page.url)
    
    # Check elements on kakao login page
    els = page.evaluate("""() => {
        return Array.from(document.querySelectorAll('input, button, a, span')).map(el => ({
            tag: el.tagName,
            id: el.id,
            className: el.className,
            text: el.innerText ? el.innerText.trim() : (el.value || '')
        })).filter(x => x.text || x.id);
    }""")
    print("KAKAO ELEMENTS COUNT:", len(els))
    for e in els[:15]:
        print("EL:", e)
        
    ctx.close()
