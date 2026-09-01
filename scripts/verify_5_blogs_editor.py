import os
import sys
import time
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
load_dotenv()

session_file = os.path.join(BASE_DIR, "session_data", "storage_state.json")
email = os.environ.get("KAKAO_EMAIL")
password = os.environ.get("KAKAO_PASSWORD")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(viewport={"width": 1280, "height": 900})
    page = context.new_page()
    
    # 1. Login to tistory main
    page.goto("https://www.tistory.com/auth/login", wait_until="networkidle")
    time.sleep(2)
    page.click("a.link_kakao_id, .btn_login.link_kakao_id")
    time.sleep(3)
    
    page.fill("input#loginId--1, input[name='loginId']", email)
    time.sleep(0.3)
    page.fill("input#password--2, input[name='password']", password)
    time.sleep(0.3)
    page.click("button.btn_g.highlight.submit, button[type='submit']")
    
    for _ in range(15):
        time.sleep(1)
        if "tistory.com" in page.url and "accounts.kakao.com" not in page.url:
            break
            
    print("Logged into Tistory Main! URL:", page.url)
    
    # 2. Check all 5 blogs from dropdown
    blogs = [
        ("smartwork-lab", "Smart Work Lab"),
        ("billionaire1004", "Grow Mindset"),
        ("wellness-routine", "웰니스 루틴 연구소"),
        ("policy-finder365", "정책 알리미 365"),
        ("finance-roadmap-for-future", "Money Roadmap 24")
    ]
    
    for sub, name in blogs:
        print(f"\n--- Checking Blog [{name}] ({sub}) ---")
        # Try writing a post on each blog
        newpost_url = f"https://{sub}.tistory.com/manage/newpost/"
        page.goto(newpost_url, wait_until="networkidle")
        time.sleep(2)
        print(f"Editor URL on [{sub}]: {page.url}")
        
        title_inp = page.locator("#post-title-inp, textarea.textarea_tit")
        is_editor_ready = title_inp.count() > 0 and title_inp.is_visible()
        print(f"Is Editor Ready on [{sub}]? -> {is_editor_ready}")
        page.screenshot(path=f"data/editor_check_{sub}.png")
        
    context.storage_state(path=session_file)
    print("\nSaved storage_state.json successfully!")
    browser.close()
