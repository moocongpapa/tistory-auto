import os
import sys
import time
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
session_file = os.path.join(BASE_DIR, "session_data", "storage_state.json")
thumb_file = os.path.join(BASE_DIR, "static", "thumbnails", "test_thumb.jpg")

# Create a nice vibrant thumbnail image
from PIL import Image, ImageDraw, ImageFont
img = Image.new('RGB', (800, 500), color=(37, 99, 235))
draw = ImageDraw.Draw(img)
draw.rectangle([(20, 20), (780, 480)], outline=(255, 255, 255), width=4)
img.save(thumb_file)

subdomain = "billionaire1004"
title = "2026 포모도로 시간 관리법: 하루 3시간 몰입으로 인생을 바꾸는 실전 루틴"
category_name = "시간 관리&습관"

article_html = """
<div style="background:#f8fafc; border-left:4px solid #3b82f6; padding:16px; margin-bottom:20px; border-radius:8px;">
    <strong style="color:#1e40af; font-size:16px;">📌 포모도로 루틴 핵심 요약:</strong>
    <p style="margin-top:6px; color:#334155; line-height:1.6;">퇴근 후 지친 뇌를 깨우는 가장 효과적인 방법은 25분 집중과 5분 휴식의 3세트 반복입니다.</p>
</div>

<h2>1. 왜 퇴근 후 포모도로 기법이 필요한가?</h2>
<p>직장인들의 가장 큰 문제는 퇴근 후 의지력이 고갈된 상태에서 '무엇을 할지' 고민하다가 침대에 눕는 것입니다. 25분이라는 짧은 시간 제한은 뇌의 시작 장벽을 극적으로 낮춰줍니다.</p>

<h2>2. 실전 3단계 뽀모도로 세팅법</h2>
<ol style="line-height:1.8; color:#334155;">
    <li><strong>스마트폰 다른 방에 격리:</strong> 시각적 자극을 원천 차단합니다.</li>
    <li><strong>단일 목표 1가지만 정의:</strong> 25분 동안 끝낼 작은 단위를 설정합니다.</li>
    <li><strong>5분 휴식 시 스트레칭과 수분 섭취:</strong> 절대 SNS를 보지 마세요.</li>
</ol>
"""

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(storage_state=session_file, viewport={"width": 1400, "height": 950})
    page = ctx.new_page()
    
    # 1. Open Editor
    print("1. Opening editor...")
    page.goto(f"https://{subdomain}.tistory.com/manage/newpost/", wait_until="networkidle")
    time.sleep(3)
    
    # 2. Fill Title
    print("2. Filling title...")
    title_inp = page.locator("#post-title-inp, textarea.textarea_tit").first
    title_inp.click()
    title_inp.fill(title)
    title_inp.press("Enter")
    time.sleep(0.5)
    
    # 3. Upload Photo via Attach Layer
    print("3. Uploading thumbnail image...")
    try:
        attach_btn = page.locator("#attach-layer-btn-open, div[aria-label='첨부'] button").first
        attach_btn.click(force=True)
        time.sleep(0.6)
        
        with page.expect_file_chooser(timeout=5000) as fc_info:
            page.locator(".mce-menu-item:has-text('사진'), [role='menuitem']:has-text('사진')").first.click(force=True)
        fc = fc_info.value
        fc.set_files(thumb_file)
        print("Waiting for image upload to CDN...")
        time.sleep(4)
        
        # 4. Click '대표' Button on Image
        print("4. Activating 대표 Thumbnail button...")
        rep_clicked = page.evaluate("""() => {
            const ed = window.tinymce && window.tinymce.activeEditor;
            if (ed) {
                const figure = ed.dom.select('figure.imageblock')[0] || ed.dom.select('img')[0];
                if (figure) {
                    ed.selection.select(figure);
                    ed.fire('click');
                    ed.fire('nodeChange');
                }
            }
            // Check button.btn_represent
            const repBtn = document.querySelector('button.btn_represent, .btn_represent, button[aria-label*=\"대표\"]');
            if (repBtn) {
                repBtn.click();
                return true;
            }
            return false;
        }""")
        print("Rep Button Click Result:", rep_clicked)
        time.sleep(0.5)
    except Exception as e:
        print("Thumbnail upload/rep error:", e)
        
    # 5. Append Body Content HTML
    print("5. Appending body HTML...")
    page.evaluate("""(html) => {
        if (window.tinymce && window.tinymce.activeEditor) {
            const ed = window.tinymce.activeEditor;
            const currentContent = ed.getContent() || '';
            if (currentContent.includes('<figure') || currentContent.includes('<img')) {
                ed.setContent(currentContent + '<br>' + html, { format: 'html' });
            } else {
                ed.setContent(html, { format: 'html' });
            }
            ed.undoManager?.add();
            ed.setDirty(true);
            ed.fire('change');
            ed.fire('input');
            ed.save();
        }
    }""", article_html)
    time.sleep(1)
    
    # 6. Select Category
    print("6. Selecting category...")
    page.locator("#category-btn").first.click(force=True)
    time.sleep(0.8)
    cat_opt = page.locator("#category-list .mce-menu-item:has-text('시간 관리'), .mce-menu .mce-menu-item:has-text('시간 관리')").first
    if cat_opt.count() > 0:
        cat_opt.click(force=True)
    else:
        page.evaluate("""() => {
            const items = Array.from(document.querySelectorAll('#category-list .mce-menu-item, .mce-menu .mce-menu-item'));
            const match = items.find(it => it.innerText.includes('시간 관리'));
            if (match) match.click();
        }""")
    time.sleep(0.5)
    print("Category selected:", page.locator("#category-btn").inner_text().strip())
    
    # 7. Add Tags
    tag_inp = page.locator("#tagText, #tag-input, input.tag_inp").first
    if tag_inp.is_visible():
        for tag in ["포모도로", "시간관리", "자기계발"]:
            tag_inp.click()
            tag_inp.fill(tag)
            tag_inp.press("Enter")
            time.sleep(0.15)
            
    # 8. Click 완료 & 공개발행
    print("8. Publishing...")
    page.locator("#publish-layer-btn, button:has-text('완료')").first.click(force=True)
    time.sleep(1.5)
    page.locator("label[for='open20']").click(force=True)
    time.sleep(0.5)
    page.locator("#publish-btn").first.click(force=True)
    
    for sec in range(12):
        time.sleep(1)
        if "/manage/newpost" not in page.url:
            print("🎉 PUBLISHED! URL:", page.url)
            break
            
    # 9. Verify Blog Main Page
    time.sleep(2)
    page.goto(f"https://{subdomain}.tistory.com/", wait_until="networkidle")
    time.sleep(2)
    page.screenshot(path="data/blog_main_verified_rep_thumb.png")
    
    audit = page.evaluate("""() => {
        const firstCard = document.querySelector('.article-card, .post-item, .box-article, article');
        const img = firstCard ? firstCard.querySelector('img') : null;
        return {
            hasImg: !!img,
            src: img ? img.src : null
        };
    }""")
    print("\n=== AUDIT RESULT ===")
    print("First Card Thumbnail:", audit)
    
    browser.close()
