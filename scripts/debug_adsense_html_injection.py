import os
import sys
import time
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
load_dotenv()

session_file = os.path.join(BASE_DIR, "session_data", "storage_state.json")

from core.gemini_client import GeminiClient
from core.adsense import AdSenseManager

gen = GeminiClient()
adsense = AdSenseManager()

raw_html = """
<h2>1. 배당 ETF 투자의 기초</h2>
<p>안정적인 배당 수익을 얻기 위한 가장 좋은 방법은 SCHD와 JEPI를 분산 투자하는 것입니다.</p>
<p>꾸준한 현금 흐름을 만들어보세요.</p>
"""
html_with_ads = adsense.inject_ads(raw_html)

print("=== HTML WITH ADS ===")
print(html_with_ads)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(storage_state=session_file, viewport={"width": 1400, "height": 950})
    page = ctx.new_page()
    
    console_msgs = []
    page.on("console", lambda msg: console_msgs.append(f"[{msg.type}] {msg.text}"))
    
    page.goto("https://finance-roadmap-for-future.tistory.com/manage/newpost/", wait_until="networkidle")
    time.sleep(3)
    
    # Fill Title
    page.fill("#post-title-inp", f"애드센스 주입 테스트 {int(time.time())}")
    time.sleep(0.5)
    
    # Inject HTML with ads
    page.evaluate("""(html) => {
        if (window.tinymce && window.tinymce.activeEditor) {
            const ed = window.tinymce.activeEditor;
            ed.setContent(html);
            ed.focus();
            ed.fire('change');
            ed.fire('input');
            ed.fire('SetContent');
            ed.save();
        }
    }""", html_with_ads)
    time.sleep(1)
    
    # Check TinyMCE content after setContent
    content_after = page.evaluate("() => window.tinymce.activeEditor.getContent()")
    print("Content in editor length:", len(content_after))
    
    # Click category
    cat_btn = page.locator("#category-btn, .btn_category, button:has-text('카테고리')").first
    if cat_btn.is_visible():
        cat_btn.click()
        time.sleep(0.5)
        opt = page.locator(".list_category li, ul li").first
        if opt.is_visible():
            opt.click()
            time.sleep(0.5)
            
    # Click 완료
    page.click("#publish-layer-btn, button:has-text('완료')")
    time.sleep(1.5)
    
    # Click 공개
    page.locator("label[for='open20']").click(force=True)
    time.sleep(0.5)
    
    # Click 발행
    page.click("#publish-btn")
    time.sleep(5)
    
    print("\n=== CONSOLE LOGS ===")
    for c in console_msgs[-15:]:
        print(c)
        
    print("Final URL:", page.url)
    browser.close()
