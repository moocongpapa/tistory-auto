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
    page.screenshot(path="data/editor_page_full.png")
    
    # Check all visible elements on top header
    visible_elems = page.evaluate("""() => {
        return Array.from(document.querySelectorAll('*')).filter(el => {
            const r = el.getBoundingClientRect();
            return r.top >= 0 && r.top <= 120 && r.width > 15 && r.height > 15;
        }).map(el => ({
            tag: el.tagName,
            id: el.id,
            className: el.className,
            text: el.innerText ? el.innerText.trim() : '',
            ariaLabel: el.getAttribute('aria-label') || '',
            title: el.getAttribute('title') || '',
            rect: el.getBoundingClientRect()
        }));
    }""")
    
    import json
    print("TOP VISIBLE ELEMENTS (top 0~120px):")
    for el in visible_elems:
        if el['text'] or el['ariaLabel'] or el['title'] or el['id']:
            print(f"[{el['tag']}] #{el['id']} .{el['className']} | text: '{el['text']}' | label: '{el['ariaLabel']}' | title: '{el['title']}' | rect: {el['rect']}")
            
    browser.close()
