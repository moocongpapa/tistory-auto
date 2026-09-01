import os
import sys
import time
from playwright.sync_api import sync_playwright

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
session_file = os.path.join(BASE_DIR, "session_data", "storage_state.json")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(storage_state=session_file, viewport={"width": 1400, "height": 950})
    page = ctx.new_page()
    
    page.goto("https://billionaire1004.tistory.com/manage/newpost/", wait_until="networkidle")
    time.sleep(3)
    
    res = page.evaluate("""() => {
        const topBtns = Array.from(document.querySelectorAll('.mce-btn, button, [role=\"button\"]')).map(b => ({
            id: b.id,
            className: b.className,
            text: b.innerText ? b.innerText.trim() : '',
            ariaLabel: b.getAttribute('aria-label') || '',
            title: b.getAttribute('title') || '',
            html: b.outerHTML.slice(0, 150)
        })).filter(x => x.ariaLabel || x.title || x.text);
        return topBtns;
    }""")
    
    for r in res:
        if any(k in (r['text'] + r['ariaLabel'] + r['title']) for k in ['첨부', '사진', '이미지', '파일', '링크', '인용', '구분선']):
            print(f"MATCH: ariaLabel='{r['ariaLabel']}' | title='{r['title']}' | text='{r['text']}' | id='{r['id']}' | class='{r['className']}'")
            
    # Check if there is an attach button
    attach = page.locator("#mceu_0-button, button:has-text('첨부'), div[aria-label*='첨부']").first
    print("\nAttach locator visible:", attach.is_visible() if attach.count() > 0 else 'Not found')
    
    browser.close()
