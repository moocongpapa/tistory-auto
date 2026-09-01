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

print(f"Logging in with: {email}")

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
        
    if "accounts.kakao.com" in page.url:
        print("At accounts.kakao.com, filling credentials...")
        page.fill("input[name='loginId'], #loginId--1", email)
        time.sleep(0.5)
        page.fill("input[name='password'], #password--2", password)
        time.sleep(0.5)
        
        # Check save login checkbox
        try:
            save_chk = page.locator("label:has-text('간편로그인'), label[for*='saveSignedIn'], input#saveSignedIn--4").first
            if save_chk.is_visible():
                save_chk.click()
                time.sleep(0.3)
        except Exception:
            pass
            
        print("Clicking submit button...")
        submit_btn = page.locator("button[type='submit'], button.btn_g.highlight.submit").first
        submit_btn.click()
        
        # Wait for redirect
        for i in range(15):
            time.sleep(1)
            print(f"Waiting redirect... ({i+1}s) current URL: {page.url}")
            if "tistory.com" in page.url and "accounts.kakao.com" not in page.url:
                print("Successfully redirected to Tistory!")
                break
                
        time.sleep(3)
        page.screenshot(path="data/kakao_login_result.png")
        
    # Now check /manage on smartwork-lab
    page.goto("https://smartwork-lab.tistory.com/manage", wait_until="networkidle")
    time.sleep(3)
    page.screenshot(path="data/smartwork_manage_result.png")
    print("Final smartwork manage URL:", page.url)
    
    ctx.close()
