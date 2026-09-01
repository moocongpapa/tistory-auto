import os
import sys
import time
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
session_file = os.path.join(BASE_DIR, "session_data", "storage_state.json")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(storage_state=session_file, viewport={"width": 1400, "height": 950})
    page = ctx.new_page()
    
    # Go to editor
    page.goto("https://smartwork-lab.tistory.com/manage/newpost/", wait_until="networkidle")
    time.sleep(3)
    
    title = f"노션 AI 업무 자동화 실전 가이드 {int(time.time())}"
    page.fill("#post-title-inp", title)
    time.sleep(1)
    
    # Fill Content
    page.evaluate("""() => {
        if (window.tinymce && window.tinymce.activeEditor) {
            window.tinymce.activeEditor.setContent('<h2>1. 시작하기</h2><p>노션 AI를 활용하여 문서를 자동화하는 방법을 안내합니다.</p>');
            window.tinymce.activeEditor.save();
        }
    }""")
    time.sleep(1)
    
    # Click '완료' button
    page.click("#publish-layer-btn, button:has-text('완료')")
    time.sleep(2)
    
    # 1. Click 공개 radio via Label & Input Click
    print("Selecting 공개 radio...")
    page.locator("label[for='open20']").click(force=True)
    time.sleep(0.5)
    page.locator("input#open20").check(force=True)
    time.sleep(0.5)
    
    # Force React State Change Event
    page.evaluate("""() => {
        const r = document.querySelector('input#open20');
        if (r) {
            r.checked = true;
            r.dispatchEvent(new Event('change', { bubbles: true }));
            r.dispatchEvent(new Event('input', { bubbles: true }));
        }
    }""")
    time.sleep(1)
    
    # Check button text
    pub_btn_text = page.locator("#publish-btn").inner_text()
    print(f"Publish button text after selecting 공개: '{pub_btn_text}'")
    page.screenshot(path="data/react_publish_ready.png")
    
    # 2. Click Publish Button
    print("Submitting publish form...")
    page.locator("#publish-btn").click(force=True)
    
    # 3. Monitor navigation
    redirected = False
    for s in range(15):
        time.sleep(1)
        print(f"Wait {s+1}s... Current URL: {page.url}")
        if "/manage/newpost" not in page.url:
            print(f"🎉 SUCCESS! Redirected to: {page.url}")
            redirected = True
            break
            
    page.screenshot(path="data/after_react_publish.png")
    
    # If redirected, verify manage page
    if redirected:
        page.goto("https://smartwork-lab.tistory.com/manage/posts", wait_until="networkidle")
        time.sleep(2)
        posts = page.evaluate("""() => {
            return Array.from(document.querySelectorAll('a.link_tit, .tit_post, .txt_tit')).map(el => el.innerText.trim()).filter(x => x.length > 0);
        }""")
        print("Live Posts in Manage:", posts)
        
    browser.close()
