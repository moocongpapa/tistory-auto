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
    
    page.goto("https://smartwork-lab.tistory.com/manage/newpost/", wait_until="networkidle")
    time.sleep(3)
    
    # 1. Title Input with real keyboard typing
    title = f"직장인 노션 AI 자동화 비법 {int(time.time())}"
    title_inp = page.locator("#post-title-inp, textarea.textarea_tit").first
    title_inp.click()
    title_inp.fill(title)
    title_inp.press("Enter")
    time.sleep(0.5)
    
    # 2. Body injection with TinyMCE + Focus + Keyboard Event
    html_content = "<h2>노션 AI로 끝내는 보고서 작성</h2><p>매일 반복되는 업무를 AI로 10분 만에 끝내는 완벽 가이드입니다.</p>"
    page.evaluate("""(html) => {
        if (window.tinymce && window.tinymce.activeEditor) {
            const ed = window.tinymce.activeEditor;
            ed.setContent(html);
            ed.fire('change');
            ed.fire('input');
            ed.fire('SetContent');
            ed.save();
        }
    }""", html_content)
    time.sleep(0.5)
    
    # Focus TinyMCE iframe/content and trigger real keystroke
    try:
        editor_frame = page.frame_locator("#editor-root iframe, #content-editor-iframe, .mce-edit-area iframe").first
        if editor_frame:
            body = editor_frame.locator("body").first
            body.click()
            body.press("End")
            page.keyboard.type(" ")
            time.sleep(0.2)
            page.keyboard.press("Backspace")
    except Exception as e:
        print("Frame focus note:", e)
        
    time.sleep(1)
    
    # 3. Select Category via UI
    cat_btn = page.locator("#category-btn, .btn_category, button:has-text('카테고리')").first
    if cat_btn.is_visible():
        cat_btn.click()
        time.sleep(0.5)
        opt = page.locator(".list_category li:has-text('AI'), ul li:has-text('AI')").first
        if opt.is_visible():
            opt.click()
            print("Selected Category:", opt.inner_text())
            time.sleep(0.5)
            
    # 4. Open Publish Layer
    page.click("#publish-layer-btn, button:has-text('완료')")
    time.sleep(1.5)
    
    # 5. Select '공개'
    page.locator("label[for='open20']").click(force=True)
    time.sleep(0.5)
    
    # 6. Click '공개발행'
    print("Clicking #publish-btn...")
    page.locator("#publish-btn").click(force=True)
    
    # 7. Monitor Redirect
    success = False
    for s in range(15):
        time.sleep(1)
        print(f"[{s+1}s] URL: {page.url}")
        if "/manage/newpost" not in page.url:
            print(f"🎉🎉🎉 100% SUCCESSFUL PUBLISH! Final URL: {page.url}")
            success = True
            break
            
    if success:
        # Check manage/posts list
        page.goto("https://smartwork-lab.tistory.com/manage/posts", wait_until="networkidle")
        time.sleep(2)
        posts = page.evaluate("""() => {
            return Array.from(document.querySelectorAll('a.link_tit, .tit_post, .txt_tit')).map(el => el.innerText.trim());
        }""")
        print("Live Posts in Manage List:", posts)
        
    browser.close()
