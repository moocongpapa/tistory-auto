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
    
    page.goto("https://billionaire1004.tistory.com/manage/newpost/", wait_until="networkidle")
    time.sleep(3)
    
    # 1. Click Category Button
    cat_btn = page.locator("#category-btn, .btn_category, button:has-text('카테고리')").first
    print("Initial category button text:", cat_btn.inner_text().strip())
    cat_btn.click()
    time.sleep(1)
    
    # 2. Inspect category list DOM in detail
    cat_dom = page.evaluate("""() => {
        const layer = document.querySelector('.list_category') || document.querySelector('.layer_category') || document.querySelector('#category-layer');
        if (!layer) return { outer: '', items: [] };
        
        const items = Array.from(layer.querySelectorAll('li')).map((li, idx) => ({
            index: idx,
            html: li.outerHTML,
            text: li.innerText.trim(),
            dataId: li.getAttribute('data-id') || li.id || '',
            clickableChild: li.querySelector('a, button, span')?.tagName || ''
        }));
        return { outer: layer.outerHTML, items: items };
    }""")
    
    print("\nCategory DOM Items:")
    for it in cat_dom['items']:
        print(f"[{it['index']}] Text: '{it['text']}' | dataId: {it['dataId']} | HTML: {it['html']}")
        
    # 3. Try clicking the 2nd item (시간 관리&습관) using Playwright mouse click at coordinate
    item_loc = page.locator(".list_category li:has-text('시간 관리'), .layer_category li:has-text('시간 관리'), .list_category span:has-text('시간 관리')").first
    print("\nTarget item count:", item_loc.count())
    if item_loc.count() > 0:
        box = item_loc.bounding_box()
        print("Target bounding box:", box)
        if box:
            print("Clicking at coordinate:", box['x'] + box['width']/2, box['y'] + box['height']/2)
            page.mouse.click(box['x'] + box['width']/2, box['y'] + box['height']/2)
            time.sleep(1.5)
            
    # Check button text after click
    cat_btn_after = page.locator("#category-btn, .btn_category, button:has-text('카테고리')").first
    print("\nCategory button text AFTER click:", cat_btn_after.inner_text().strip())
    page.screenshot(path="data/category_click_result.png")
    
    browser.close()
