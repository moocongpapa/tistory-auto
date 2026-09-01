import os
import sys
import time
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
session_file = os.path.join(BASE_DIR, "session_data", "storage_state.json")

# Sample thumbnail file
thumb_file = os.path.join(BASE_DIR, "static", "thumbnails", "blog_5_thumb_106864_387.jpg")
print("Thumbnail file exists:", os.path.exists(thumb_file), thumb_file)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(storage_state=session_file, viewport={"width": 1400, "height": 950})
    page = ctx.new_page()
    
    page.goto("https://billionaire1004.tistory.com/manage/newpost/", wait_until="networkidle")
    time.sleep(3)
    
    # Inspect all file inputs and image buttons
    info = page.evaluate("""() => {
        const fileInputs = Array.from(document.querySelectorAll('input[type="file"]')).map(inp => ({
            id: inp.id,
            name: inp.name,
            className: inp.className,
            accept: inp.accept,
            outerHTML: inp.outerHTML
        }));
        
        const photoButtons = Array.from(document.querySelectorAll('button, div, a')).filter(el => {
            const t = el.innerText || el.getAttribute('aria-label') || el.getAttribute('title') || '';
            return t.includes('사진') || t.includes('이미지') || el.className.includes('image') || el.className.includes('photo');
        }).map(el => ({
            tag: el.tagName,
            id: el.id,
            className: el.className,
            text: el.innerText ? el.innerText.trim() : '',
            ariaLabel: el.getAttribute('aria-label'),
            title: el.getAttribute('title')
        }));
        
        return { fileInputs, photoButtons };
    }""")
    
    print("\nFILE INPUTS FOUND:")
    for inp in info['fileInputs']:
        print(" ", inp)
        
    print("\nPHOTO BUTTONS FOUND:")
    for btn in info['photoButtons'][:10]:
        print(" ", btn)
        
    # Try attaching file to file inputs
    file_inputs = page.locator("input[type='file']")
    print("\nFile Input Locator Count:", file_inputs.count())
    
    if file_inputs.count() > 0:
        print("Setting input files on input[type='file']...")
        
        # Listen to upload network requests
        responses = []
        page.on("response", lambda r: responses.append(f"[{r.status}] {r.url}") if "attach" in r.url or "image" in r.url or "kage" in r.url or "upload" in r.url else None)
        
        file_inputs.first.set_input_files(thumb_file)
        time.sleep(3)
        
        print("\nUpload Network Responses:", responses)
        page.screenshot(path="data/thumbnail_upload_test.png")
        
        # Check if representative image checkbox / layer appears
        rep_info = page.evaluate("""() => {
            const rep = document.querySelector('.btn_represent, .represent, .thumb_represent, button[aria-label*=\"대표\"]');
            const images = Array.from(document.querySelectorAll('img')).map(img => ({
                src: img.src,
                className: img.className,
                alt: img.alt
            }));
            return {
                hasRepBtn: !!rep,
                repHtml: rep ? rep.outerHTML : '',
                imagesCount: images.length,
                images: images.slice(0, 5)
            };
        }""")
        print("\nRepresentative Image Check:", rep_info)
        
    browser.close()
