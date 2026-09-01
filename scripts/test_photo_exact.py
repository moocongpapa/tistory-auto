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
    
    # Inspect elements near x: 180~240, y: 15~50
    photo_target = page.evaluate("""() => {
        const elements = Array.from(document.querySelectorAll('*')).filter(el => {
            const r = el.getBoundingClientRect();
            return r.left >= 170 && r.left <= 230 && r.top >= 10 && r.top <= 60 && r.width > 10;
        }).map(el => ({
            tag: el.tagName,
            id: el.id,
            className: el.className,
            ariaLabel: el.getAttribute('aria-label') || '',
            title: el.getAttribute('title') || '',
            rect: el.getBoundingClientRect(),
            outerHTML: el.outerHTML.slice(0, 150)
        }));
        return elements;
    }""")
    
    import json
    print("PHOTO TARGET BUTTON CANDIDATES:")
    print(json.dumps(photo_target, ensure_ascii=False, indent=2))
    
    # Try clicking the exact coordinate or button
    print("\nAttempting click with expect_file_chooser on the first candidate...")
    try:
        # Click at coordinate (x: 195, y: 35) or locator
        with page.expect_file_chooser(timeout=5000) as fc_info:
            page.mouse.click(195, 35)
            
        fc = fc_info.value
        print("🎉 SUCCESS! File chooser captured! Setting file:", thumb_file)
        fc.set_files(thumb_file)
        time.sleep(5)
        
        # Check uploaded image and DOM
        upload_status = page.evaluate("""() => {
            const ed = window.tinymce && window.tinymce.activeEditor;
            const imgs = ed ? Array.from(ed.dom.select('img')).map(i => ({
                src: i.src,
                alt: i.alt,
                dataset: i.dataset
            })) : [];
            const figureImgs = Array.from(document.querySelectorAll('figure img, .imageblock img, img')).map(i => i.src);
            return {
                tinymceImages: imgs,
                allPageImages: figureImgs
            };
        }""")
        print("\nUPLOAD STATUS RESULT:", upload_status)
        page.screenshot(path="data/photo_upload_success_verified.png")
    except Exception as e:
        print("Click error:", e)
        
    browser.close()
