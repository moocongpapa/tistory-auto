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
    
    # 1. Upload photo
    print("1. Uploading image...")
    page.locator("#attach-layer-btn-open").first.click(force=True)
    time.sleep(0.5)
    with page.expect_file_chooser(timeout=5000) as fc_info:
        page.locator(".mce-menu-item:has-text('사진'), [role='menuitem']:has-text('사진')").first.click(force=True)
    fc = fc_info.value
    fc.set_files(thumb_file)
    time.sleep(4)
    
    # 2. Inspect TinyMCE editor iframe or root for the uploaded image
    print("2. Inspecting image element in editor...")
    img_info = page.evaluate("""() => {
        const ed = window.tinymce && window.tinymce.activeEditor;
        if (!ed) return { error: 'no editor' };
        
        // Find image or figure in editor
        const figure = ed.dom.select('figure.imageblock')[0] || ed.dom.select('img')[0];
        if (!figure) return { error: 'no figure found in editor' };
        
        // Click figure
        ed.selection.select(figure);
        ed.fire('click');
        ed.fire('nodeChange');
        
        return {
            figureHTML: figure.outerHTML,
            figureClass: figure.className,
            dataset: figure.dataset
        };
    }""")
    print("TinyMCE Figure Selected:", img_info)
    time.sleep(1)
    
    # 3. Check if representative badge / button is visible in editor or overlay
    rep_buttons = page.evaluate("""() => {
        const btns = Array.from(document.querySelectorAll('button, div, span, a')).filter(el => {
            const t = el.innerText || el.getAttribute('aria-label') || el.getAttribute('title') || '';
            return t.includes('대표') || el.className.includes('represent') || el.className.includes('thumb');
        }).map(el => ({
            tag: el.tagName,
            id: el.id,
            className: el.className,
            text: el.innerText ? el.innerText.trim() : '',
            ariaLabel: el.getAttribute('aria-label') || '',
            title: el.getAttribute('title') || '',
            rect: el.getBoundingClientRect()
        }));
        return btns;
    }""")
    print("\nREPRESENTATIVE BUTTONS FOUND IN DOM:")
    for b in rep_buttons:
        print(" ", b)
        
    page.screenshot(path="data/editor_image_selected.png")
    browser.close()
