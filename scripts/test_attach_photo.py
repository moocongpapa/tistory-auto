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
    
    # Click '첨부' button
    attach_btn = page.locator("#mceu_0-open, #mceu_0 button, div[aria-label='첨부'] button, #mceu_0").first
    print("Clicking 첨부 button...")
    attach_btn.click(force=True)
    time.sleep(1)
    
    # Check menu items under '첨부'
    menu_items = page.evaluate("""() => {
        return Array.from(document.querySelectorAll('.mce-menu .mce-menu-item, .mce-menu-item')).map(it => ({
            text: it.innerText ? it.innerText.trim() : '',
            id: it.id,
            className: it.className
        }));
    }""")
    print("\nATTACH MENU ITEMS:", menu_items)
    
    # Click '사진' with file_chooser
    try:
        with page.expect_file_chooser(timeout=5000) as fc_info:
            page.locator(".mce-menu-item:has-text('사진'), .mce-text:has-text('사진')").first.click(force=True)
        fc = fc_info.value
        print("🎉 SUCCESS! File chooser captured! Setting file:", thumb_file)
        fc.set_files(thumb_file)
        time.sleep(4)
        
        # Check if uploaded image appears in TinyMCE
        res = page.evaluate("""() => {
            const ed = window.tinymce && window.tinymce.activeEditor;
            const imgs = ed ? Array.from(ed.dom.select('img')).map(i => i.src) : [];
            const rep = document.querySelector('.btn_represent, [aria-label*=\"대표\"]');
            return {
                edImages: imgs,
                hasRepBtn: !!rep
            };
        }""")
        print("\nTinyMCE Uploaded Images:", res['edImages'])
        page.screenshot(path="data/thumbnail_upload_confirmed.png")
    except Exception as e:
        print("File chooser error:", e)
        
    browser.close()
