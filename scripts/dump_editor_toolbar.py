import os
import sys
import time
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    user_data_dir = "data/browser_sessions/billionaire1004"
    browser = p.chromium.launch_persistent_context(
        user_data_dir=user_data_dir,
        headless=True,
        viewport={"width": 1400, "height": 900}
    )
    page = browser.new_page()
    page.goto("https://billionaire1004.tistory.com/manage/newpost/", wait_until="domcontentloaded")
    time.sleep(3)
    
    toolbar_elements = page.evaluate("""() => {
        const toolbar = document.querySelector('#mceu_0, .mce-toolbar-grp, .header_editor, #editor-root');
        const allButtons = Array.from(document.querySelectorAll('button, div[role="button"], div.mce-widget, div.mce-btn, span.mce-txt')).map(el => ({
            id: el.id,
            className: el.className,
            text: el.innerText ? el.innerText.trim() : '',
            ariaLabel: el.getAttribute('aria-label'),
            title: el.getAttribute('title'),
            tag: el.tagName
        })).filter(x => x.text || x.ariaLabel || x.title);
        
        return {
            url: window.location.href,
            buttons: allButtons
        };
    }""")
    
    import json
    print("TOOLBAR BUTTONS:")
    print(json.dumps(toolbar_elements, ensure_ascii=False, indent=2))
    
    browser.close()
