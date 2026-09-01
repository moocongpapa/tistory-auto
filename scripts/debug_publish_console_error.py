import os
import sys
import time
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
session_file = os.path.join(BASE_DIR, "session_data", "storage_state.json")

console_logs = []
network_logs = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(storage_state=session_file, viewport={"width": 1400, "height": 950})
    page = ctx.new_page()
    
    page.on("console", lambda msg: console_logs.append(f"[{msg.type}] {msg.text}"))
    page.on("requestfailed", lambda req: network_logs.append(f"[FAILED] {req.url} -> {req.failure}"))
    page.on("response", lambda res: network_logs.append(f"[RES {res.status}] {res.url}") if "post" in res.url or "publish" in res.url or "manage" in res.url else None)
    
    page.goto("https://smartwork-lab.tistory.com/manage/newpost/", wait_until="networkidle")
    time.sleep(3)
    
    title = "콘솔 디버깅 테스트 포스팅"
    page.fill("#post-title-inp", title)
    time.sleep(1)
    
    # Fill Content
    page.evaluate("""() => {
        if (window.tinymce && window.tinymce.activeEditor) {
            window.tinymce.activeEditor.setContent('<p>콘솔 디버깅 본문입니다.</p>');
            window.tinymce.activeEditor.save();
        }
    }""")
    time.sleep(1)
    
    # Click '완료'
    page.click("#publish-layer-btn")
    time.sleep(2)
    
    # Select '공개'
    page.locator("label[for='open20']").click()
    time.sleep(1)
    
    print("Clicking publish button...")
    page.locator("#publish-btn").click()
    time.sleep(5)
    
    print("\n=== CONSOLE LOGS ===")
    for log in console_logs[-20:]:
        print(log)
        
    print("\n=== NETWORK LOGS ===")
    for net in network_logs[-20:]:
        print(net)
        
    browser.close()
