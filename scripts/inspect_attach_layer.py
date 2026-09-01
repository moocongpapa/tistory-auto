import os
import sys
import time
from playwright.sync_api import sync_playwright

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
session_file = os.path.join(BASE_DIR, "session_data", "storage_state.json")
thumb_file = os.path.join(BASE_DIR, "static", "thumbnails", "test_thumb.jpg")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(storage_state=session_file, viewport={"width": 1400, "height": 950})
    page = ctx.new_page()
    
    page.goto("https://billionaire1004.tistory.com/manage/newpost/", wait_until="networkidle")
    time.sleep(3)
    
    # Check #attach-layer-btn or #editor-root or toolbar
    res = page.evaluate("""() => {
        const btn = document.querySelector('#attach-layer-btn') || document.querySelector('[data-layer=\"attach\"]') || document.querySelector('.btn_attach');
        if (!btn) return { found: false };
        return {
            found: true,
            id: btn.id,
            className: btn.className,
            offsetParent: !!btn.offsetParent,
            rect: btn.getBoundingClientRect(),
            parentHTML: btn.parentElement ? btn.parentElement.outerHTML.slice(0, 200) : ''
        };
    }""")
    print("ATTACH BTN EVAL:", res)
    
    # Try clicking with JS dispatch
    page.evaluate("""() => {
        const btn = document.querySelector('#attach-layer-btn') || document.querySelector('[data-layer=\"attach\"]');
        if (btn) {
            btn.click();
        }
    }""")
    time.sleep(1)
    
    # Check if attach layer or popup opened
    layer_info = page.evaluate("""() => {
        const layer = document.querySelector('#attach-layer, .layer_attach, .mce-menu');
        const items = Array.from(document.querySelectorAll('#attach-layer *, .layer_attach *')).map(el => ({
            tag: el.tagName,
            text: el.innerText ? el.innerText.trim() : '',
            id: el.id,
            className: el.className
        })).filter(x => x.text);
        return {
            hasLayer: !!layer,
            items: items
        };
    }""")
    print("LAYER INFO AFTER CLICK:", layer_info)
    
    browser.close()
