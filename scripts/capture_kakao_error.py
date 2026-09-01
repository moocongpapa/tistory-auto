import os
import sys
import time
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
load_dotenv()

session_dir = os.path.join(BASE_DIR, "session_data")
email = os.environ.get("KAKAO_EMAIL")
password = os.environ.get("KAKAO_PASSWORD")

with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(
        user_data_dir=session_dir,
        headless=True,
        viewport={"width": 1280, "height": 800}
    )
    page = ctx.new_page()
    page.goto("https://www.tistory.com/auth/login", wait_until="networkidle")
    time.sleep(2)
    
    kakao_btn = page.locator("a.link_kakao_id, .btn_login.link_kakao_id").first
    if kakao_btn.is_visible():
        kakao_btn.click()
        time.sleep(3)
        
    page.fill("input#loginId--1", email)
    time.sleep(0.3)
    page.fill("input#password--2", password)
    time.sleep(0.3)
    
    # Click submit
    page.click("button.btn_g.highlight.submit")
    time.sleep(4)
    
    screenshot_path = os.path.join(BASE_DIR, "kakao_submit_state.png")
    page.screenshot(path=screenshot_path)
    print("Screenshot saved to:", screenshot_path)
    print("Current URL after submit:", page.url)
    
    # Print error messages on page
    errors = page.evaluate("""() => {
        return Array.from(document.querySelectorAll('.desc_error, .info_error, .txt_error, p, span')).map(el => el.innerText.trim()).filter(x => x.includes('비밀번호') || x.includes('인증') || x.includes('오류') || x.includes('확인') || x.includes('일치'));
    }""")
    print("PAGE ERROR MESSAGES:", errors)
    
    ctx.close()
