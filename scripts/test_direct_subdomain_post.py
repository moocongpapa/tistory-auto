import os
import sys
import time
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
session_file = os.path.join(BASE_DIR, "session_data", "storage_state.json")

subdomain = "billionaire1004"
title = "2026 포모도로 시간 관리법: 퇴근 후 하루 3시간 몰입 공식"
category_target = "시간 관리&습관"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(storage_state=session_file, viewport={"width": 1400, "height": 950})
    page = ctx.new_page()
    
    # 1. Open editor
    page.goto(f"https://{subdomain}.tistory.com/manage/newpost/", wait_until="networkidle")
    time.sleep(3)
    
    # 2. Fill Title
    title_inp = page.locator("#post-title-inp, textarea.textarea_tit").first
    title_inp.click()
    title_inp.fill(title)
    title_inp.press("Enter")
    time.sleep(0.5)
    
    # 3. Fill Body via HTML Mode
    html = """
    <h2>1. 포모도로 기법이란?</h2>
    <p>25분 집중과 5분 휴식을 반복하는 가장 과학적인 시간 관리법입니다.</p>
    <h2>2. 실전 3단계 루틴</h2>
    <p>스마트폰을 격리하고 단일 작업에만 집중하세요.</p>
    """
    
    mode_btn = page.locator("#editor-mode-layer-btn-open, button:has-text('기본모드'), button.btn_mode").first
    if mode_btn.is_visible():
        mode_btn.click()
        time.sleep(0.5)
        html_opt = page.locator("#editor-mode-html, button:has-text('HTML'), li:has-text('HTML')").first
        if html_opt.is_visible():
            html_opt.click()
            time.sleep(1)
            page.evaluate("""(h) => {
                const cm = document.querySelector('.CodeMirror');
                if (cm && cm.CodeMirror) {
                    cm.CodeMirror.setValue(h);
                    cm.CodeMirror.save();
                }
            }""", html)
            time.sleep(0.5)
            
    # 4. Select Category
    print("Opening category dropdown...")
    cat_btn = page.locator("#category-btn, .btn_category, button:has-text('카테고리')").first
    cat_btn.click(force=True)
    time.sleep(1)
    
    # Click the exact category item
    res_cat = page.evaluate("""(kw) => {
        const items = Array.from(document.querySelectorAll('.list_category li, .layer_category li, .list_category span'));
        for (const it of items) {
            if (it.innerText && it.innerText.includes(kw)) {
                it.click();
                return it.innerText.trim();
            }
        }
        return null;
    }""", "시간 관리")
    print("Selected Category Result:", res_cat)
    time.sleep(1)
    page.screenshot(path="data/direct_sub_category.png")
    
    # 5. Add Tag
    tag_inp = page.locator("#tagText, #tag-input, input.tag_inp").first
    if tag_inp.is_visible():
        tag_inp.click()
        tag_inp.fill("포모도로")
        tag_inp.press("Enter")
        time.sleep(0.5)
        
    # 6. Click 완료
    print("Clicking 완료...")
    page.locator("#publish-layer-btn, button:has-text('완료')").first.click(force=True)
    time.sleep(2)
    
    # 7. Select 공개
    print("Clicking 공개 radio...")
    page.locator("label[for='open20']").click(force=True)
    time.sleep(0.5)
    page.locator("input#open20").check(force=True)
    time.sleep(0.5)
    
    # 8. Check Publish Button
    pub_btn = page.locator("#publish-btn").first
    print("Final Publish Button Text:", pub_btn.inner_text())
    page.screenshot(path="data/direct_sub_before_publish.png")
    
    # 9. Click Publish and listen to responses
    responses = []
    page.on("response", lambda r: responses.append(f"[{r.status}] {r.url}") if "post" in r.url or "manage" in r.url else None)
    
    pub_btn.click(force=True)
    
    for s in range(15):
        time.sleep(1)
        print(f"[{s+1}s] URL: {page.url}")
        if "/manage/newpost" not in page.url:
            print("🎉 REDIRECTED TO:", page.url)
            break
            
    page.screenshot(path="data/direct_sub_after_publish.png")
    print("Publish Responses:", responses)
    
    # 10. Check manage list
    page.goto(f"https://{subdomain}.tistory.com/manage/posts", wait_until="networkidle")
    time.sleep(2)
    posts = page.evaluate("""() => {
        return Array.from(document.querySelectorAll('a.link_tit, .tit_post, .txt_tit')).map(el => el.innerText.trim());
    }""")
    print("Latest 3 Posts on Manage:", posts[:3])
    
    browser.close()
