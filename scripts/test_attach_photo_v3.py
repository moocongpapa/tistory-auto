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
    
    # 1. Click attach button
    print("1. Clicking #attach-layer-btn-open...")
    page.locator("#attach-layer-btn-open").first.click(force=True)
    time.sleep(0.8)
    page.screenshot(path="data/attach_menu_opened.png")
    
    # 2. Check menu items
    menu_items = page.evaluate("""() => {
        return Array.from(document.querySelectorAll('.mce-menu .mce-menu-item, [role=\"menuitem\"]')).map(it => ({
            text: it.innerText ? it.innerText.trim() : '',
            id: it.id,
            className: it.className
        }));
    }""")
    print("2. Menu items found:", menu_items)
    
    # 3. Click '사진' with file chooser
    print("3. Clicking '사진' menu item with expect_file_chooser...")
    try:
        with page.expect_file_chooser(timeout=5000) as fc_info:
            page.locator(".mce-menu-item:has-text('사진'), [role='menuitem']:has-text('사진')").first.click(force=True)
            
        fc = fc_info.value
        print("🎉 SUCCESS! File chooser captured! Setting file:", thumb_file)
        fc.set_files(thumb_file)
        time.sleep(6)
        
        # 4. Check if image is uploaded to TinyMCE
        res = page.evaluate("""() => {
            const ed = window.tinymce && window.tinymce.activeEditor;
            const edHtml = ed ? ed.getContent() : '';
            const imgs = ed ? Array.from(ed.dom.select('img')).map(i => ({
                src: i.src,
                alt: i.alt,
                dataset: i.dataset
            })) : [];
            return {
                imgs,
                htmlPreview: edHtml.slice(0, 200)
            };
        }""")
        print("\n4. Upload Result:", res)
        page.screenshot(path="data/photo_upload_result.png")
    except Exception as e:
        print("Error during photo upload:", e)
        
    browser.close()
