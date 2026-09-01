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
    
    # Check attach button
    attach_info = page.evaluate("""() => {
        const btns = Array.from(document.querySelectorAll('button, div[role="button"], div.btn, a')).map(el => ({
            tag: el.tagName,
            id: el.id,
            className: el.className,
            text: el.innerText ? el.innerText.trim() : '',
            ariaLabel: el.getAttribute('aria-label'),
            title: el.getAttribute('title')
        }));
        
        const attachBtn = document.querySelector('#attach-layer-btn-open') || 
                          document.querySelector('#attach-layer-btn') || 
                          document.querySelector('div[aria-label="첨부"] button') ||
                          document.querySelector('div[aria-label="첨부"]') ||
                          Array.from(document.querySelectorAll('button')).find(b => b.innerText && b.innerText.includes('첨부'));
        
        let menuHTML = '';
        if (attachBtn) {
            attachBtn.click();
        }
        
        return {
            attachFound: !!attachBtn,
            attachOuter: attachBtn ? attachBtn.outerHTML : ''
        };
    }""")
    print("ATTACH BUTTON INFO:", attach_info)
    time.sleep(1)
    
    # Check open menu
    menu_info = page.evaluate("""() => {
        const openMenus = Array.from(document.querySelectorAll('.mce-menu, .layer_attach, .mce-menu-item, [role="menu"], [role="menuitem"]')).map(el => ({
            tag: el.tagName,
            id: el.id,
            className: el.className,
            text: el.innerText ? el.innerText.trim() : '',
            role: el.getAttribute('role'),
            outerHTML: el.outerHTML.slice(0, 150)
        }));
        return openMenus;
    }""")
    print("OPEN MENUS:")
    import json
    print(json.dumps(menu_info, ensure_ascii=False, indent=2))
    
    browser.close()
