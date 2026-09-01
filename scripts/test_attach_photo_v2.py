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
    
    # Click the visible div[aria-label="첨부"]
    attach_div = page.locator("div[aria-label='첨부']").first
    print("Clicking div[aria-label='첨부']... Count:", attach_div.count())
    attach_div.click(force=True)
    time.sleep(1)
    
    # Look for visible menu items
    menu_items = page.evaluate("""() => {
        return Array.from(document.querySelectorAll('.mce-menu-item, .mce-menu, [role=\"menuitem\"], .layer_attach li')).map(el => ({
            text: el.innerText ? el.innerText.trim() : '',
            tag: el.tagName,
            className: el.className,
            rect: el.getBoundingClientRect()
        })).filter(x => x.text);
    }""")
    print("VISIBLE MENU ITEMS AFTER CLICK:", menu_items)
    
    # Try capturing file chooser on '사진'
    photo_item = page.locator(".mce-menu-item:has-text('사진'), [role='menuitem']:has-text('사진'), li:has-text('사진')").first
    if photo_item.count() > 0:
        print("Found Photo item! Triggering file chooser...")
        with page.expect_file_chooser(timeout=5000) as fc_info:
            photo_item.click(force=True)
        fc = fc_info.value
        print("🎉 SUCCESS! File chooser captured! Setting file:", thumb_file)
        fc.set_files(thumb_file)
        time.sleep(5)
        
        # Check uploaded image in TinyMCE & Represent badge
        check = page.evaluate("""() => {
            const ed = window.tinymce && window.tinymce.activeEditor;
            const imgs = ed ? Array.from(ed.dom.select('img')).map(i => ({
                src: i.src,
                alt: i.alt,
                className: i.className
            })) : [];
            
            // Check represent button/badge
            const repBtns = Array.from(document.querySelectorAll('.btn_represent, button[aria-label*=\"대표\"], [data-represent]')).map(b => ({
                text: b.innerText,
                className: b.className,
                outer: b.outerHTML
            }));
            
            return { imgs, repBtns };
        }""")
        print("\nUploaded Images & Rep Badge:", check)
        page.screenshot(path="data/photo_upload_tested.png")
        
    browser.close()
