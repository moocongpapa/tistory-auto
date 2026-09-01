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
    
    # Go to billionaire1004 (Grow Mindset)
    subdomain = "billionaire1004"
    page.goto(f"https://{subdomain}.tistory.com/manage/newpost/", wait_until="networkidle")
    time.sleep(3)
    
    # 1. Fill Title
    page.fill("#post-title-inp", "카테고리 선택 및 발행 정밀 디버깅")
    time.sleep(0.5)
    
    # 2. Inject Body
    page.evaluate("""() => {
        if (window.tinymce && window.tinymce.activeEditor) {
            window.tinymce.activeEditor.setContent('<h2>테스트 소제목</h2><p>본문 내용입니다.</p>');
            window.tinymce.activeEditor.save();
        }
    }""")
    time.sleep(0.5)
    
    # 3. Inspect Category Dropdown
    print("=== INSPECTING CATEGORY ===")
    cat_btn = page.locator("#category-btn, .btn_category, button:has-text('카테고리')").first
    print("Category button visible:", cat_btn.is_visible())
    cat_btn.click()
    time.sleep(1)
    
    # Dump Category HTML & items
    cat_items = page.evaluate("""() => {
        const list = document.querySelector('.list_category') || document.querySelector('.layer_category') || document.querySelector('ul.list_category');
        if (!list) return { html: '', items: [] };
        const items = Array.from(list.querySelectorAll('li, button, a, span')).map(el => ({
            tag: el.tagName,
            className: el.className,
            text: el.innerText.trim(),
            selector: el.getAttribute('data-id') || el.id || ''
        })).filter(x => x.text.length > 0);
        return { html: list.outerHTML, items: items };
    }""")
    print("Category items found:", len(cat_items['items']))
    for it in cat_items['items']:
        print("  CAT ITEM:", it)
        
    page.screenshot(path="data/debug_category_opened.png")
    
    # Try clicking '시간 관리&습관' or '성장 도서&마인드'
    target_category = "시간 관리&습관"
    cat_target = page.locator(f".list_category li:has-text('{target_category}'), .list_category button:has-text('{target_category}'), .layer_category li:has-text('{target_category}')").first
    if cat_target.is_visible():
        print(f"Clicking category: '{target_category}'...")
        cat_target.click(force=True)
        time.sleep(1)
    else:
        print("Category target not found via locator! Trying JS click...")
        page.evaluate(f"""(kw) => {{
            const items = Array.from(document.querySelectorAll('.list_category li, .layer_category li, .list_category span, .list_category a'));
            const match = items.find(el => el.innerText.includes(kw));
            if (match) match.click();
        }}""", "시간")
        time.sleep(1)
        
    # Check if category button text changed
    current_cat_btn_text = cat_btn.inner_text().strip()
    print(f"Current Category Button Text after click: '{current_cat_btn_text}'")
    page.screenshot(path="data/debug_category_selected.png")
    
    # 4. Inspect '완료' and Publish Layer
    print("\n=== INSPECTING PUBLISH LAYER ===")
    comp_btn = page.locator("#publish-layer-btn, button:has-text('완료'), button.btn_complete").first
    comp_btn.click(force=True)
    time.sleep(2)
    
    # Select '공개'
    page.locator("label[for='open20']").click(force=True)
    time.sleep(0.5)
    
    pub_btn = page.locator("#publish-btn").first
    print("Publish button text:", pub_btn.inner_text().strip())
    page.screenshot(path="data/debug_before_final_publish.png")
    
    # Listen to all network responses
    responses = []
    page.on("response", lambda r: responses.append(f"[{r.status}] {r.url}"))
    
    # Click publish button
    print("Clicking #publish-btn...")
    pub_btn.click(force=True)
    
    for sec in range(12):
        time.sleep(1)
        print(f"  Waiting ({sec+1}s)... URL: {page.url}")
        if "/manage/newpost" not in page.url:
            print(f"🎉 SUCCESS REDIRECT! URL: {page.url}")
            break
            
    page.screenshot(path="data/debug_after_final_publish.png")
    
    print("\n=== NETWORK RESPONSES DURING PUBLISH ===")
    for r in responses:
        if "post" in r or "publish" in r or "tistory" in r:
            print(r)
            
    browser.close()
