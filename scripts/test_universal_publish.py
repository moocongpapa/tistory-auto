import os
import sys
import time
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
load_dotenv()

session_file = os.path.join(BASE_DIR, "session_data", "storage_state.json")

def publish_test(subdomain: str, title: str, html: str, category_kw: str):
    print(f"\n==========================================")
    print(f"Testing Universal Publish on [{subdomain}]")
    print(f"==========================================")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(storage_state=session_file, viewport={"width": 1400, "height": 950})
        page = ctx.new_page()
        
        # Anti-draft init script
        page.add_init_script("window.confirm = () => false;")
        
        page.goto(f"https://{subdomain}.tistory.com/manage/newpost/", wait_until="networkidle")
        time.sleep(3)
        
        # 1. Title
        title_inp = page.locator("#post-title-inp, textarea.textarea_tit").first
        title_inp.click()
        title_inp.fill(title)
        title_inp.press("Enter")
        time.sleep(0.5)
        
        # 2. Inject HTML and trigger TinyMCE commands
        page.evaluate("""(content) => {
            if (window.tinymce && window.tinymce.activeEditor) {
                const ed = window.tinymce.activeEditor;
                ed.setContent(content);
                ed.focus();
                ed.fire('change');
                ed.fire('input');
                ed.fire('SetContent');
                ed.save();
            }
        }""", html)
        time.sleep(0.5)
        
        # 3. Focus Editor Content Area & Keystroke
        focused = False
        for frame in page.frames:
            try:
                body = frame.locator("body#tinymce, body.mce-content-body, body").first
                if body.count() > 0 and body.is_visible():
                    body.click(force=True)
                    body.press("End")
                    page.keyboard.type(" ")
                    time.sleep(0.1)
                    page.keyboard.press("Backspace")
                    focused = True
                    print("  -> Focused TinyMCE iframe body successfully!")
                    break
            except Exception:
                pass
                
        if not focused:
            try:
                ed_root = page.locator("#editor-root, .mce-edit-area").first
                ed_root.click(force=True)
                page.keyboard.type(" ")
                time.sleep(0.1)
                page.keyboard.press("Backspace")
                print("  -> Focused editor root container!")
            except Exception as e:
                print("  -> Focus note:", e)
                
        time.sleep(1)
        
        # 4. Category
        try:
            cat_btn = page.locator("button:has-text('카테고리'), #category-btn, .btn_category").first
            if cat_btn.is_visible():
                cat_btn.click()
                time.sleep(0.5)
                opt = page.locator(f".list_category li:has-text('{category_kw}'), ul li:has-text('{category_kw}')").first
                if opt.is_visible():
                    opt_text = opt.inner_text().strip()
                    opt.click()
                    print(f"  -> Selected Category: {opt_text}")
                else:
                    first_opt = page.locator(".list_category li, ul.list_category li").first
                    if first_opt.is_visible():
                        first_opt.click()
                        print(f"  -> Selected First Category fallback: {first_opt.inner_text().strip()}")
        except Exception as e:
            print("  -> Category note:", e)
            
        time.sleep(1)
        
        # 5. Open Layer
        comp_btn = page.locator("#publish-layer-btn, button:has-text('완료')").first
        comp_btn.click(force=True)
        time.sleep(1.5)
        
        # 6. Select Public
        try:
            open_lbl = page.locator("label[for='open20'], label:has-text('공개')").first
            if open_lbl.is_visible():
                open_lbl.click(force=True)
                time.sleep(0.3)
            page.evaluate("""() => {
                const r = document.querySelector('input#open20') || document.querySelector('input[value=\"20\"]');
                if (r) {
                    r.checked = true;
                    r.dispatchEvent(new Event('change', { bubbles: true }));
                    r.dispatchEvent(new Event('input', { bubbles: true }));
                }
            }""")
        except Exception as e:
            print("  -> Open radio note:", e)
            
        time.sleep(1)
        
        # 7. Click Publish
        print("  -> Clicking #publish-btn...")
        page.locator("#publish-btn").click(force=True)
        
        # 8. Wait Redirect
        pub_ok = False
        for s in range(15):
            time.sleep(1)
            print(f"     Waiting redirect ({s+1}s)... {page.url}")
            if "/manage/newpost" not in page.url:
                print(f"  🎉 PUBLISHED SUCCESS on [{subdomain}]! URL: {page.url}")
                pub_ok = True
                break
                
        # 9. Verify Live on Blog Front
        if pub_ok:
            page.goto(f"https://{subdomain}.tistory.com/", wait_until="networkidle")
            time.sleep(2)
            titles = page.evaluate("""() => {
                return Array.from(document.querySelectorAll('article, .article-type-common, h1, h2, h3, .title, .tit_post, .link_article')).map(el => el.innerText.trim());
            }""")
            print(f"  -> Live Blog Front Titles: {titles[:5]}")
            
        ctx.storage_state(path=session_file)
        browser.close()

# Test 1: Money Roadmap 24
publish_test(
    subdomain="finance-roadmap-for-future",
    title=f"2030 직장인 미국 배당 ETF SCHD 투자 전략 {int(time.time())}",
    html="<h2>1. SCHD ETF란?</h2><p>SCHD는 미국의 대표적인 배당성장 ETF로 매년 배당금을 늘려주는 기업에 투자합니다.</p><p>장기 복리 효과를 노려보세요.</p>",
    category_kw="주식"
)

# Test 2: Policy Finder 365
publish_test(
    subdomain="policy-finder365",
    title=f"2026 청년 주거지원 정책 및 월세 환급 신청 방법 {int(time.time())}",
    html="<h2>1. 청년 월세 특별지원</h2><p>월 최대 20만 원까지 지원받을 수 있는 정부 청년 주거지원 혜택을 정리했습니다.</p><p>지금 신청해보세요.</p>",
    category_kw="청년"
)
