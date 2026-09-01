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
    time.sleep(2)
    
    cfg = page.evaluate("""() => {
        return {
            categories: window.Config?.blog?.categories || [],
            categoryHtml: document.querySelector('#category-btn')?.outerHTML || '',
            categoryParentHtml: document.querySelector('#category-btn')?.parentElement?.outerHTML || ''
        };
    }""")
    print("CONFIG BLOG CATEGORIES:")
    print(json.dumps(cfg['categories'], ensure_ascii=False, indent=2))
    print("\nCATEGORY BTN PARENT HTML:")
    print(cfg['categoryParentHtml'][:500])
    
    browser.close()
