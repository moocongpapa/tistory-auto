import os
import sys
import time
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
session_file = os.path.join(BASE_DIR, "session_data", "storage_state.json")

subdomain = "billionaire1004"
title = "2026 직장인 퇴근 후 3시간 자기계발 실전 포모도로 루틴 가이드"
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

<h2>3. 30일 실천 후기 및 놀라운 변화</h2>
<p>매일 3세트(총 1시간 15분)만 집중해도 한 달이면 40시간 이상의 순수 몰입 시간을 확보할 수 있습니다. 지금 바로 타이머를 25분에 맞추고 시작해 보세요!</p>
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
    
    # 3. Inject into TinyMCE in DEFAULT MODE & Verify getContent()
    print("3. Injecting HTML into TinyMCE...")
    inject_res = page.evaluate("""(html) => {
        if (window.tinymce && window.tinymce.activeEditor) {
            const ed = window.tinymce.activeEditor;
            ed.setContent(html, { format: 'html' });
            ed.undoManager?.add();
            ed.setDirty(true);
            ed.fire('change');
            ed.fire('input');
            ed.fire('SetContent');
            ed.save();
            const savedContent = ed.getContent();
            return {
                success: true,
                savedLength: savedContent ? savedContent.length : 0,
                preview: savedContent ? savedContent.slice(0, 100) : ''
            };
        }
        return { success: false, savedLength: 0 };
    }""", article_html)
    print("TinyMCE Injection Result:", inject_res)
    time.sleep(1)
    
    # 4. Select Category
    print("4. Selecting Category...")
    cat_btn = page.locator("#category-btn").first
    cat_btn.click(force=True)
    time.sleep(0.8)
    
    # Select '시간 관리&습관'
    cat_opt = page.locator("#category-list .mce-menu-item:has-text('시간 관리'), .mce-menu .mce-menu-item:has-text('시간 관리')").first
    if cat_opt.count() > 0:
        cat_opt.click(force=True)
        print("Clicked category option directly via locator!")
        time.sleep(0.5)
    else:
        print("Locator not found, fallback to JS click...")
        page.evaluate("""() => {
            const items = Array.from(document.querySelectorAll('#category-list .mce-menu-item, .mce-menu .mce-menu-item'));
            const match = items.find(it => it.innerText.includes('시간 관리'));
            if (match) match.click();
        }""")
        time.sleep(0.5)
        
    btn_text = page.locator("#category-btn").inner_text().strip()
    print(f"Category Button text after selection: '{btn_text}'")
    
    # 5. Add Tags
    print("5. Adding tags...")
    tag_inp = page.locator("#tagText, #tag-input, input.tag_inp").first
    if tag_inp.is_visible():
        for tag in ["시간관리", "자기계발", "포모도로", "직장인루틴"]:
            tag_inp.click()
            tag_inp.fill(tag)
            tag_inp.press("Enter")
            time.sleep(0.2)
            
    # 6. Click 완료
    print("6. Clicking 완료...")
    page.locator("#publish-layer-btn, button:has-text('완료')").first.click(force=True)
    time.sleep(1.5)
    
    # 7. Select 공개
    print("7. Selecting 공개...")
    page.locator("label[for='open20']").click(force=True)
    time.sleep(0.5)
    
    # 8. Click 최종 공개발행
    pub_btn = page.locator("#publish-btn").first
    print("8. Final publish button text:", pub_btn.inner_text().strip())
    
    # Capture post payload
    payloads = []
    def on_request(req):
        if "post" in req.url or "publish" in req.url:
            payloads.append(f"REQ [{req.method}] {req.url} | PostDataLen: {len(req.post_data or '')}")
    page.on("request", on_request)
    
    pub_btn.click(force=True)
    
    for sec in range(12):
        time.sleep(1)
        print(f"  Waiting ({sec+1}s)... URL: {page.url}")
        if "/manage/newpost" not in page.url:
            print("🎉 REDIRECTED TO:", page.url)
            break
            
    print("\nNetwork Post Payloads:")
    for p_item in payloads:
        print(" ", p_item)
        
    # 9. Verify the newly published article directly on blog!
    time.sleep(2)
    page.goto(f"https://{subdomain}.tistory.com/", wait_until="networkidle")
    time.sleep(2)
    
    # Find link to our new article
    links = page.evaluate("""() => {
        return Array.from(document.querySelectorAll('a')).map(a => ({
            text: a.innerText.trim(),
            href: a.href
        })).filter(x => x.href.includes('/entry/') || x.href.match(/\\/\\d+$/));
    }""")
    print("\nLatest Article on Blog Main:", links[0] if links else 'None')
    
    if links:
        page.goto(links[0]['href'], wait_until="networkidle")
        time.sleep(2)
        
        audit = page.evaluate("""() => {
            const cat = document.querySelector('.category, .txt_category, .box-category, .area_head .category')?.innerText?.trim() || '';
            const title = document.querySelector('h1, .tit_post, .title_post, .entry-title')?.innerText?.trim() || '';
            const body = document.querySelector('.entry-content, .article-view, article, .tt_article_useless_p_margin')?.innerText?.trim() || '';
            const headings = Array.from(document.querySelectorAll('.entry-content h2, .article-view h2, article h2')).map(h => h.innerText.trim());
            return {
                category: cat,
                title: title,
                bodyLength: body.length,
                headings: headings,
                bodyPreview: body.slice(0, 300)
            };
        }""")
        print("\n=== VERIFIED LIVE ARTICLE DETAILS ===")
        print("URL:", page.url)
        print("Category on Page:", audit['category'])
        print("Title on Page:", audit['title'])
        print("Headings on Page:", audit['headings'])
        print("Body Text Length:", audit['bodyLength'])
        print("Body Preview:\n", audit['bodyPreview'])
        page.screenshot(path="data/verified_perfect_article.png")
        
    browser.close()
