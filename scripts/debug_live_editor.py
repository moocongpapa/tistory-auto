import os
import sys
import time
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
load_dotenv()

session_dir = os.path.join(BASE_DIR, "session_data")
subdomain = "smartwork-lab"

print(f"=== Live Debugging Editor for {subdomain} ===")

with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(
        user_data_dir=session_dir,
        headless=True,
        viewport={"width": 1400, "height": 950}
    )
    page = ctx.new_page()
    
    # Step 1. Check /manage/newpost/
    editor_url = f"https://{subdomain}.tistory.com/manage/newpost/"
    print(f"1. Navigating to {editor_url}")
    page.goto(editor_url, wait_until="networkidle")
    time.sleep(3)
    page.screenshot(path="data/step1_editor_loaded.png")
    print(f"Current URL: {page.url}")
    
    # Step 2. Title input
    title_el = page.locator("#post-title-inp, textarea.textarea_tit").first
    print(f"2. Title visible: {title_el.is_visible()}")
    if title_el.is_visible():
        title_el.fill("티스토리 실시간 발행 점검 테스트")
        time.sleep(1)
        page.screenshot(path="data/step2_title_entered.png")
        
    # Step 3. Body content
    print("3. Injecting content...")
    page.evaluate("""() => {
        if (window.tinymce && window.tinymce.activeEditor) {
            window.tinymce.activeEditor.setContent('<p>이 글은 자동화 엔진의 공개 발행 검증 테스트 본문입니다.</p>');
            window.tinymce.activeEditor.save();
        }
    }""")
    time.sleep(1)
    page.screenshot(path="data/step3_content_injected.png")
    
    # Step 4. Check '완료' button
    comp_btn = page.locator("#publish-layer-btn, button:has-text('완료'), .btn_complete").first
    print(f"4. Complete button visible: {comp_btn.is_visible()}")
    if comp_btn.is_visible():
        print("Clicking 완료 button...")
        comp_btn.click()
        time.sleep(2)
        page.screenshot(path="data/step4_layer_opened.png")
        
        # Inspect all buttons in publish layer
        layer_btns = page.evaluate("""() => {
            return Array.from(document.querySelectorAll('button, input, label')).map(el => ({
                tag: el.tagName,
                id: el.id,
                className: el.className,
                type: el.type || '',
                text: el.innerText ? el.innerText.trim() : (el.value || '')
            })).filter(x => x.text || x.id);
        }""")
        print("Layer Buttons:", layer_btns)
        
        # Step 5. Click public radio
        open_radio = page.locator("label:has-text('공개'), label[for='open20'], input#open20").first
        print(f"5. Public radio visible: {open_radio.is_visible()}")
        if open_radio.is_visible():
            open_radio.click()
            time.sleep(1)
            page.screenshot(path="data/step5_public_selected.png")
            
        # Step 6. Click final publish
        pub_btn = page.locator("#publish-btn, button.btn_publish, button:has-text('공개발행'), button:has-text('발행')").first
        print(f"6. Final publish button visible: {pub_btn.is_visible()}")
        if pub_btn.is_visible():
            print("Clicking final publish button...")
            pub_btn.click()
            
            # Step 7. Monitor navigation and url for 10 seconds
            for s in range(10):
                time.sleep(1)
                print(f"Time {s+1}s: URL is {page.url}")
                page.screenshot(path=f"data/step7_publishing_{s+1}s.png")
                if "/manage/newpost" not in page.url:
                    print(f"Redirected! Final URL: {page.url}")
                    break
                    
    ctx.close()
