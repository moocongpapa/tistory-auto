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
    
    # Dump entire toolbar element hierarchy
    toolbar_info = page.evaluate("""() => {
        const toolbar = document.querySelector('.mce-toolbar, .area_tool, #editor-toolbar, .mce-menubar, .mce-top-part');
        if (!toolbar) return 'NO TOOLBAR FOUND';
        
        // Find all interactive items in toolbar
        const items = Array.from(document.querySelectorAll('.mce-toolbar button, .mce-toolbar .mce-btn, .area_tool button, .area_tool a, .mce-menubar .mce-menubtn, .mce-top-part button, .mce-top-part div[role=\"button\"]')).map(el => ({
            tag: el.tagName,
            id: el.id,
            className: el.className,
            ariaLabel: el.getAttribute('aria-label') || '',
            title: el.getAttribute('title') || '',
            text: el.innerText ? el.innerText.trim() : '',
            icon: el.querySelector('i')?.className || ''
        }));
        
        return {
            toolbarClass: toolbar.className,
            items: items
        };
    }""")
    
    import json
    print(json.dumps(toolbar_info, ensure_ascii=False, indent=2))
    
    # Also check if there is an attach button on the right side or top
    attach_btns = page.evaluate("""() => {
        return Array.from(document.querySelectorAll('*')).filter(el => {
            const attr = (el.getAttribute('aria-label') || '') + ' ' + (el.getAttribute('title') || '') + ' ' + (el.innerText || '');
            return attr.includes('사진') || attr.includes('첨부') || attr.includes('파일');
        }).map(el => ({
            tag: el.tagName,
            id: el.id,
            className: el.className,
            text: el.innerText ? el.innerText.trim() : '',
            ariaLabel: el.getAttribute('aria-label') || '',
            title: el.getAttribute('title') || ''
        }));
    }""")
    print("\nATTACH ELEMENTS:")
    print(json.dumps(attach_btns, ensure_ascii=False, indent=2))
    
    browser.close()
