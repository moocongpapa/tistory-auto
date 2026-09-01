import os
import sys
import time
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
session_file = os.path.join(BASE_DIR, "session_data", "storage_state.json")

# Find an existing thumbnail file in static/thumbnails
thumbs_dir = os.path.join(BASE_DIR, "static", "thumbnails")
os.makedirs(thumbs_dir, exist_ok=True)
thumb_files = [os.path.join(thumbs_dir, f) for f in os.listdir(thumbs_dir) if f.endswith(('.jpg', '.png'))]
if not thumb_files:
    from PIL import Image
    dummy_path = os.path.join(thumbs_dir, "test_thumb.jpg")
    img = Image.new('RGB', (800, 500), color=(50, 100, 200))
    img.save(dummy_path)
    thumb_files = [dummy_path]

thumb_file = thumb_files[0]
print("Using Thumbnail File:", thumb_file)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(storage_state=session_file, viewport={"width": 1400, "height": 950})
    page = ctx.new_page()
    
    page.goto("https://billionaire1004.tistory.com/manage/newpost/", wait_until="networkidle")
    time.sleep(3)
    
    # Check all toolbar buttons
    buttons = page.evaluate("""() => {
        return Array.from(document.querySelectorAll('button, div[role=\"button\"], a')).map((el, i) => ({
            index: i,
            tag: el.tagName,
            id: el.id,
            className: el.className,
            text: el.innerText ? el.innerText.trim() : '',
            title: el.getAttribute('title') || '',
            ariaLabel: el.getAttribute('aria-label') || '',
            dataTool: el.getAttribute('data-tool') || el.getAttribute('data-command') || ''
        })).filter(x => x.text || x.title || x.ariaLabel || x.dataTool);
    }""")
    
    print("\nALL ACTION BUTTONS ON EDITOR:")
    for b in buttons:
        if any(k in (b['text'] + b['title'] + b['ariaLabel'] + b['dataTool']) for k in ['사진', '이미지', '첨부', 'image', 'photo', 'file']):
            print(" -> PHOTO CANDIDATE:", b)

    # Try triggering file chooser via Photo button
    photo_btn = page.locator("button:has-text('사진'), [data-tool='image'], [data-command='image'], button[aria-label*='사진'], button[title*='사진'], .mce-btn:has-text('사진')").first
    print("\nPhoto button visible:", photo_btn.is_visible())
    
    if photo_btn.is_visible():
        try:
            with page.expect_file_chooser(timeout=5000) as fc_info:
                photo_btn.click()
            file_chooser = fc_info.value
            print("SUCCESS: File Chooser triggered! Setting file:", thumb_file)
            file_chooser.set_files(thumb_file)
            time.sleep(4)
            print("File set! Checking uploaded images in TinyMCE...")
            
            # Check if image appears in TinyMCE or DOM
            img_res = page.evaluate("""() => {
                const ed = window.tinymce && window.tinymce.activeEditor;
                const edImages = ed ? Array.from(ed.dom.select('img')).map(img => img.src) : [];
                const domImages = Array.from(document.querySelectorAll('img')).map(img => img.src);
                return { edImages, domImages };
            }""")
            print("TinyMCE Images:", img_res['edImages'])
            print("DOM Images:", len(img_res['domImages']))
            page.screenshot(path="data/photo_upload_success.png")
        except Exception as e:
            print("File chooser error:", e)
            
    browser.close()
