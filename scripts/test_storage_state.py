import os
import sys
import time
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
load_dotenv()

session_file = os.path.join(BASE_DIR, "session_data", "storage_state.json")
os.makedirs(os.path.dirname(session_file), exist_ok=True)

email = os.environ.get("KAKAO_EMAIL")
password = os.environ.get("KAKAO_PASSWORD")

print(f"Testing Kakao Login & storage_state saving for: {email}")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    
    if os.path.exists(session_file):
        context = browser.new_context(storage_state=session_file, viewport={"width": 1280, "height": 800})
        print("Loaded existing storage_state.json")
    else:
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        print("Created clean new context")
        
    page = context.new_page()
    page.goto("https://www.tistory.com/auth/login", wait_until="networkidle")
    time.sleep(2)
    
    # Check if login button is needed
    kakao_btn = page.locator("a.link_kakao_id, .btn_login.link_kakao_id").first
    if kakao_btn.is_visible():
        kakao_btn.click()
        time.sleep(3)
        
    if "accounts.kakao.com" in page.url:
        print("Filling Kakao login form...")
        page.fill("input#loginId--1, input[name='loginId']", email)
        time.sleep(0.3)
        page.fill("input#password--2, input[name='password']", password)
        time.sleep(0.3)
        
        try:
            page.locator("label:has-text('간편로그인'), input#saveSignedIn--4").first.click()
            time.sleep(0.2)
        except Exception:
            pass
            
        page.click("button.btn_g.highlight.submit, button[type='submit']")
        
        # Wait for redirect back to tistory.com
        for sec in range(20):
            time.sleep(1)
            print(f"Waiting redirect ({sec+1}s)... {page.url}")
            if "tistory.com" in page.url and "accounts.kakao.com" not in page.url:
                print("Redirected to Tistory successfully!")
                break
                
        time.sleep(3)

    # Save storage state
    context.storage_state(path=session_file)
    print(f"Saved session state to: {session_file} (Size: {os.path.getsize(session_file)} bytes)")
    
    # Test manage pages on 5 blogs
    subdomains = ["smartwork-lab", "billionaire1004", "wellness-routine", "policy-finder365", "finance-roadmap-for-future"]
    for sub in subdomains:
        manage_url = f"https://{sub}.tistory.com/manage"
        page.goto(manage_url, wait_until="networkidle")
        time.sleep(2)
        print(f"Blog [{sub}] manage URL: {page.url}")
        if "/manage" in page.url and "auth/login" not in page.url:
            print(f"  -> SUCCESS: Logged in on {sub}!")
        else:
            print(f"  -> FAILED: Redirected to login on {sub}!")

    browser.close()
