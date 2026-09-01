import sys
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright
import os, time, json

session_file = os.path.join(os.getcwd(), 'session_data', 'storage_state.json')

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(storage_state=session_file, viewport={'width': 1400, 'height': 950})
    page = ctx.new_page()
    page.goto('https://billionaire1004.tistory.com/manage/newpost/', wait_until='networkidle')
    time.sleep(3)
    
    cat_btn = page.locator('#category-btn').first
    cat_btn.click()
    time.sleep(1)
    
    list_info = page.evaluate("""() => {
        const list = document.querySelector('#category-list') || document.querySelector('[role="listbox"]') || document.querySelector('.mce-menu');
        if (!list) return { exists: false, items: [] };
        const items = Array.from(list.querySelectorAll('*')).map(el => ({
            id: el.id,
            tag: el.tagName,
            className: el.className,
            role: el.getAttribute('role'),
            text: el.innerText ? el.innerText.trim() : ''
        })).filter(x => x.text.length > 0 && x.text !== '카테고리');
        return { exists: true, outer: list.outerHTML, items: items };
    }""")
    print('CATEGORY LIST INFO:')
    print(json.dumps(list_info['items'], ensure_ascii=False, indent=2))
    
    # Try clicking the option matching '시간 관리'
    print("\nAttempting Playwright click on option...")
    opt = page.locator("#category-list [role='option']:has-text('시간 관리'), #category-list li:has-text('시간 관리'), #category-list .mce-text:has-text('시간 관리'), #category-list div:has-text('시간 관리')").first
    print("Found option count:", opt.count())
    if opt.count() > 0:
        opt.click()
        time.sleep(1)
        
    btn_after = page.locator("#category-btn").first.inner_text().strip()
    print(f"BUTTON TEXT AFTER CLICK: '{btn_after}'")
    page.screenshot(path="data/category_perfect_result.png")
    
    browser.close()
