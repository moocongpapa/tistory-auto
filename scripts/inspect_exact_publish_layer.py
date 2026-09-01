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
    
    # Fill Title
    page.fill("#post-title-inp", "정밀 발행 테스트 포스팅")
    time.sleep(1)
    
    # Fill Content
    page.evaluate("""() => {
        if (window.tinymce && window.tinymce.activeEditor) {
            window.tinymce.activeEditor.setContent('<p>본문 내용입니다.</p>');
            window.tinymce.activeEditor.save();
        }
    }""")
    time.sleep(1)
    
    # Click '완료' button (Right bottom)
    comp_btn = page.locator("#publish-layer-btn, button:has-text('완료'), button.btn_complete").first
    print("Found complete button:", comp_btn.inner_text())
    comp_btn.click()
    time.sleep(2)
    
    # Dump publish layer HTML
    layer_html = page.evaluate("""() => {
        const layer = document.querySelector('#publish-layer') || document.querySelector('.layer_post') || document.querySelector('.layer_publish') || document.querySelector('div[role=\"dialog\"]');
        return layer ? layer.outerHTML : document.body.innerHTML;
    }""")
    with open("data/publish_layer_dump.html", "w", encoding="utf-8") as f:
        f.write(layer_html)
    print("Saved data/publish_layer_dump.html (Size:", len(layer_html), "bytes)")
    
    page.screenshot(path="data/exact_publish_layer.png")
    
    # Now look for the EXACT publish button inside the layer
    btns_in_layer = page.evaluate("""() => {
        return Array.from(document.querySelectorAll('button, input[type=\"submit\"], a')).map(el => ({
            tag: el.tagName,
            id: el.id,
            className: el.className,
            type: el.type,
            text: el.innerText ? el.innerText.trim() : (el.value || '')
        })).filter(x => x.text.includes('발행') || x.id.includes('publish'));
    }""")
    print("Buttons matching '발행':", btns_in_layer)
    
    # Try clicking the last '발행' button
    publish_button = page.locator("#publish-btn, button:has-text('발행'), button:has-text('공개발행')").last
    print("Publish button count:", page.locator("#publish-btn, button:has-text('발행'), button:has-text('공개발행')").count())
    if publish_button.is_visible():
        print("Clicking publish button:", publish_button.inner_text())
        publish_button.click()
        
        for i in range(10):
            time.sleep(1)
            print(f"Waiting navigation ({i+1}s)... URL: {page.url}")
            if "newpost" not in page.url:
                print("SUCCESSFULLY REDIRECTED! New URL:", page.url)
                break
                
    page.screenshot(path="data/after_publish_click.png")
    browser.close()
