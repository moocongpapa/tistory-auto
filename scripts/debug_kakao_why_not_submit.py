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

print(f"Inspecting Kakao login form with: email={email}")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1280, "height": 900})
    page.goto("https://www.tistory.com/auth/login", wait_until="networkidle")
    time.sleep(2)
    
    page.click("a.link_kakao_id, .btn_login.link_kakao_id")
    time.sleep(3)
    
    print("Page URL after Kakao button click:", page.url)
    page.screenshot(path="data/kakao_1_before_fill.png")
    
    # Fill inputs using native typing simulation
    id_input = page.locator("input#loginId--1, input[name='loginId']").first
    id_input.click()
    id_input.type(email, delay=50)
    time.sleep(0.5)
    
    pw_input = page.locator("input#password--2, input[name='password']").first
    pw_input.click()
    pw_input.type(password, delay=50)
    time.sleep(0.5)
    
    page.screenshot(path="data/kakao_2_after_fill.png")
    
    # Click submit
    submit_btn = page.locator("button.btn_g.highlight.submit, button[type='submit']").first
    print("Submit button text:", submit_btn.inner_text(), "is_enabled:", submit_btn.is_enabled())
    submit_btn.click()
    
    time.sleep(4)
    page.screenshot(path="data/kakao_3_after_click.png")
    print("Page URL after click:", page.url)
    
    # Check if any error text or 2FA or CAPTCHA appeared
    body_text = page.locator("body").inner_text()
    print("=== BODY TEXT AFTER SUBMIT ===")
    print(body_text[:1000])
    
    browser.close()
