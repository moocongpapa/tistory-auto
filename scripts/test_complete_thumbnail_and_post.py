import os
import sys
import time
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
session_file = os.path.join(BASE_DIR, "session_data", "storage_state.json")
thumb_file = os.path.join(BASE_DIR, "static", "thumbnails", "test_thumb.jpg")

subdomain = "billionaire1004"
title = "2026 직장인 몰입의 기술: 뽀모도로 시간 관리와 생산성 극대화 루틴"
category_name = "시간 관리&습관"

article_html = """
<div style="background:#f8fafc; border-left:4px solid #3b82f6; padding:16px; margin-bottom:20px; border-radius:8px;">
    <strong style="color:#1e40af; font-size:16px;">📌 직장인 몰입 루틴 3줄 요약:</strong>
    <p style="margin-top:6px; color:#334155; line-height:1.6;">1. 25분 집중 + 5분 휴식 3회 반복<br>2. 스마트폰 및 멀티태스킹 원천 차단<br>3. 매일 같은 시간 루틴 고정화</p>
</div>

<h2>1. 왜 퇴근 후 1시간이 하루 전체를 좌우하는가?</h2>
<p>성공적인 자기계발의 핵심은 많은 시간이 아니라 '밀도 높은 몰입'에 있습니다. 퇴근 후 단 1시간의 포모도로 루틴이 여러분의 1년을 바꿉니다.</p>

<h2>2. 실전 포모도로 3단계 세팅법</h2>
<ol style="line-height:1.8; color:#334155;">
    <li><strong>환경 격리:</strong> 책상 위에는 오늘 다룰 단 하나의 작업만 둡니다.</li>
    <li><strong>시간 시각화:</strong> 아날로그 타이머나 전용 앱을 25분에 맞춥니다.</li>
    <li><strong>충분한 뇌 휴식:</strong> 5분 휴식 시에는 화면을 보지 않고 눈을 감습니다.</li>
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
    
    # 3. Upload Thumbnail Photo
    uploaded_image_figure = ""
    if os.path.exists(thumb_file):
        print("3. Uploading thumbnail image...")
        try:
            page.locator("#attach-layer-btn-open").first.click(force=True)
            time.sleep(0.5)
            with page.expect_file_chooser(timeout=5000) as fc_info:
                page.locator(".mce-menu-item:has-text('사진'), [role='menuitem']:has-text('사진')").first.click(force=True)
            fc = fc_info.value
            fc.set_files(thumb_file)
            time.sleep(4)
            print("Thumbnail uploaded to TinyMCE!")
        except Exception as e:
            print("Thumbnail upload error:", e)
            
    # 4. Inject Full Body Content (Preserving Thumbnail)
    print("4. Injecting body content...")
    page.evaluate("""(html) => {
        if (window.tinymce && window.tinymce.activeEditor) {
            const ed = window.tinymce.activeEditor;
            const currentContent = ed.getContent() || '';
            // If image exists, append content after image
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
    
    # 5. Select Category
    print("5. Selecting Category...")
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
    
    # 6. Add Tags
    tag_inp = page.locator("#tagText, #tag-input, input.tag_inp").first
    if tag_inp.is_visible():
        for tag in ["시간관리", "자기계발", "포모도로", "생산성"]:
            tag_inp.click()
            tag_inp.fill(tag)
            tag_inp.press("Enter")
            time.sleep(0.15)
            
    # 7. Click 완료 & 공개발행
    print("7. Publishing...")
    page.locator("#publish-layer-btn, button:has-text('완료')").first.click(force=True)
    time.sleep(1.5)
    page.locator("label[for='open20']").click(force=True)
    time.sleep(0.5)
    page.locator("#publish-btn").first.click(force=True)
    
    for sec in range(12):
        time.sleep(1)
        if "/manage/newpost" not in page.url:
            print("🎉 PUBLISHED! Redirected to:", page.url)
            break
            
    # 8. Check Main Page for Thumbnail Card!
    time.sleep(2)
    page.goto(f"https://{subdomain}.tistory.com/", wait_until="networkidle")
    time.sleep(2)
    
    card_info = page.evaluate("""() => {
        const firstCard = document.querySelector('.article-card, .post-item, .list_content, article, .box-article');
        const cardImg = firstCard ? firstCard.querySelector('img') : null;
        const allCardImgs = Array.from(document.querySelectorAll('a img, .thumb img, .thumbnail img')).map(i => i.src);
        return {
            hasFirstCardImg: !!cardImg,
            cardImgSrc: cardImg ? cardImg.src : null,
            allCardImgs: allCardImgs.slice(0, 5)
        };
    }""")
    print("\n=== BLOG MAIN CARD THUMBNAIL AUDIT ===")
    print("First Card Thumbnail:", card_info['hasFirstCardImg'], card_info['cardImgSrc'])
    print("All Found Card Thumbnails:", card_info['allCardImgs'])
    
    browser.close()
