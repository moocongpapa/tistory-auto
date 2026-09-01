import os
import sys
import time
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
session_file = os.path.join(BASE_DIR, "session_data", "storage_state.json")
thumb_file = os.path.join(BASE_DIR, "static", "thumbnails", "test_thumb.jpg")

subdomain = "billionaire1004"
title = "2026 직장인 시간 관리 혁명: 포모도로 25분 집중 루틴과 5분 뇌 리셋법"
category_name = "시간 관리&습관"

article_html = """
<div style="background:#f8fafc; border-left:4px solid #3b82f6; padding:16px; margin-bottom:20px; border-radius:8px;">
    <strong style="color:#1e40af; font-size:16px;">📌 포모도로 핵심 요약:</strong>
    <p style="margin-top:6px; color:#334155; line-height:1.6;">퇴근 후 3시간, 25분 몰입과 5분 휴식의 3세트 반복으로 생산성을 극대화합니다.</p>
</div>

<h2>1. 왜 직장인에게 포모도로가 가장 강력한가?</h2>
<p>의지력이 바닥난 퇴근 후에는 '25분만 하자'는 작은 목표가 뇌의 저항을 완벽히 무력화합니다.</p>

<h2>2. 실전 3단계 뽀모도로 세팅법</h2>
<ol style="line-height:1.8; color:#334155;">
    <li><strong>스마트폰 다른 방 격리:</strong> 도파민 분비 유혹 차단</li>
    <li><strong>단일 과업 정의:</strong> 하나의 작업만 책상 위에 배치</li>
    <li><strong>5분 눈 감고 휴식:</strong> 뇌 피로도 급속 회복</li>
</ol>
"""

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(storage_state=session_file, viewport={"width": 1400, "height": 950})
    page = ctx.new_page()
    
    # 1. Open editor
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
    
    # 3. Open Attach Menu via reliable JS dispatch
    print("3. Opening attach menu via JS...")
    page.evaluate("""() => {
        const attachBtn = document.querySelector('#attach-layer-btn') || document.querySelector('div[aria-label=\"첨부\"]') || document.querySelector('.mce-i-tistory-attach')?.closest('div');
        if (attachBtn) {
            attachBtn.dispatchEvent(new MouseEvent('mousedown', { bubbles: true, cancelable: true }));
            attachBtn.dispatchEvent(new MouseEvent('mouseup', { bubbles: true, cancelable: true }));
            attachBtn.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }));
        }
    }""")
    time.sleep(0.8)
    
    # 4. Trigger Photo File Chooser
    print("4. Selecting 사진 option with expect_file_chooser...")
    with page.expect_file_chooser(timeout=6000) as fc_info:
        # Click 사진 menu item
        page.evaluate("""() => {
            const items = Array.from(document.querySelectorAll('.mce-menu-item, [role=\"menuitem\"]'));
            const photoItem = items.find(it => it.innerText && it.innerText.includes('사진'));
            if (photoItem) {
                photoItem.dispatchEvent(new MouseEvent('mousedown', { bubbles: true }));
                photoItem.dispatchEvent(new MouseEvent('mouseup', { bubbles: true }));
                photoItem.dispatchEvent(new MouseEvent('click', { bubbles: true }));
                photoItem.click();
            }
        }""")
    fc = fc_info.value
    print("🎉 SUCCESS! File chooser captured! Setting file:", thumb_file)
    fc.set_files(thumb_file)
    print("Waiting for image upload to CDN...")
    time.sleep(4)
    
    # 5. Activate Representative Thumbnail
    print("5. Clicking 대표 thumbnail button...")
    rep_res = page.evaluate("""() => {
        const ed = window.tinymce && window.tinymce.activeEditor;
        if (ed) {
            const figure = ed.dom.select('figure.imageblock')[0] || ed.dom.select('img')[0];
            if (figure) {
                ed.selection.select(figure);
                ed.fire('click');
                ed.fire('nodeChange');
            }
        }
        const repBtn = document.querySelector('button.btn_represent, .btn_represent, button[aria-label*=\"대표\"]');
        if (repBtn) {
            repBtn.click();
            return true;
        }
        return false;
    }""")
    print("Rep Button Result:", rep_res)
    time.sleep(0.5)
    
    # 6. Append Full Body Content
    print("6. Appending body HTML...")
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
    
    # 7. Select Category
    print("7. Selecting Category...")
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
    print("Category text:", page.locator("#category-btn").inner_text().strip())
    
    # 8. Add Tags
    tag_inp = page.locator("#tagText, #tag-input, input.tag_inp").first
    if tag_inp.is_visible():
        for tag in ["포모도로", "시간관리", "자기계발"]:
            tag_inp.click()
            tag_inp.fill(tag)
            tag_inp.press("Enter")
            time.sleep(0.15)
            
    # 9. Click 완료 & 공개발행
    print("9. Publishing...")
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
            
    # 10. Audit Blog Main
    time.sleep(2)
    page.goto(f"https://{subdomain}.tistory.com/", wait_until="networkidle")
    time.sleep(2)
    
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
