import sys
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright
import os, time

session_file = os.path.join(os.getcwd(), 'session_data', 'storage_state.json')

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(storage_state=session_file, viewport={'width': 1400, 'height': 950})
    page = ctx.new_page()
    page.goto('https://billionaire1004.tistory.com/manage/newpost/', wait_until='networkidle')
    time.sleep(3)
    
    cat_btn = page.locator('#category-btn, button:has-text("카테고리")').first
    cat_btn.click()
    time.sleep(1)
    
    dump = page.evaluate("""() => {
        const els = Array.from(document.querySelectorAll('*')).filter(el => {
            const t = el.innerText || '';
            return t.includes('시간 관리') && el.children.length === 0;
        });
        return els.map(el => ({
            tag: el.tagName,
            className: el.className,
            id: el.id,
            parentTag: el.parentElement ? el.parentElement.tagName : '',
            parentClass: el.parentElement ? el.parentElement.className : '',
            grandParentClass: el.parentElement && el.parentElement.parentElement ? el.parentElement.parentElement.className : '',
            text: el.innerText
        }));
    }""")
    print('FOUND MATCHING ELEMENTS:', len(dump))
    for d in dump:
        print("MATCH:", d)
    browser.close()
