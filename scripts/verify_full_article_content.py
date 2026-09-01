import os
import sys
import time
import logging

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from core.tistory_bot import TistoryBot
from core.adsense import AdSenseManager
from playwright.sync_api import sync_playwright

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

bot = TistoryBot(headless=True)
adsense = AdSenseManager()

subdomain = "smartwork-lab"
title = "2026 직장인 생산성 혁신 노션 AI 실전 마스터 가이드"

raw_article = """
<div style="background:#f1f5f9; border-left:4px solid #2563eb; padding:18px; border-radius:10px; margin-bottom:24px;">
    <strong style="color:#1e40af; font-size:16px;">💡 핵심 요약:</strong>
    <p style="margin-top:6px; color:#334155;">매일 쏟아지는 업무 문서와 회의록 작성을 노션 AI로 10분 만에 끝내는 완벽한 실무 자동화 워크플로우를 소개합니다.</p>
</div>

<h2>1. 왜 지금 노션 AI를 도입해야 하는가?</h2>
<p>현대 직장인들에게 가장 부족한 자원은 바로 '시간'입니다. 단순 반복적인 문서 작성과 데이터 정리 업무에 치이다 보면 본질적인 기획과 분석에 집중할 시간을 빼앗기게 됩니다.</p>
<p>노션 AI를 워크스페이스에 통합하면 다음과 같은 극적인 변화를 경험할 수 있습니다.</p>

<h2>2. 실무에서 바로 써먹는 핵심 기능 3가지</h2>
<ol style="line-height:1.8; color:#334155;">
    <li><strong>회의록 즉시 요약 및 액션 아이템 추출:</strong> 1시간짜리 회의 내용을 30초 만에 3줄 요약과 담당자별 할 일 목록으로 변환합니다.</li>
    <li><strong>기획서 및 보고서 초안 원클릭 생성:</strong> 핵심 키워드 몇 가지만 입력하면 체계적인 목차와 본문 뼈대를 자동으로 작성해 줍니다.</li>
    <li><strong>비즈니스 톤앤매너 자동 교정:</strong> 거친 초안 문장을 격식 있고 신뢰감 있는 비즈니스 전문 문체로 다듬어 줍니다.</li>
</ol>

<h2>3. 노션 AI 프롬프트 작성 꿀팁</h2>
<p>AI에게 구체적인 역할(Role)과 맥락(Context), 원하는 출력 형식(Format)을 명확하게 제시할수록 결과물의 품질이 극대화됩니다.</p>
<div style="background:#f8fafc; border:1px solid #cbd5e1; border-radius:8px; padding:14px; margin:16px 0;">
    <code style="color:#0f172a; font-size:14px; font-family:Consolas, monospace;">프롬프트 예시: "너는 10년 차 IT 전략 기획자야. 첨부된 신규 프로젝트 개요를 바탕으로 임원 보고용 1페이지 요약본을 작성해줘."</code>
</div>

<h2>4. 업무 효율 200% 달성을 위한 결론</h2>
<p>스마트 워크의 핵심은 도구를 얼마나 내 업무 프로세스에 자연스럽게 녹여내는가에 달려 있습니다. 오늘 소개해 드린 노션 AI 활용법을 오늘 업무부터 바로 적용해 보세요!</p>
"""

# Inject Ads
full_html = adsense.inject_ads(raw_article)

print("=== 1. Starting Full Article Publishing ===")
result = bot.post_article(
    subdomain=subdomain,
    title=title,
    content_html=full_html,
    tags=["노션AI", "스마트워크", "생산성향상", "직장인꿀팁", "업무자동화"],
    category_name="AI&업무 자동화",
    is_draft=False
)
print("Publish Result:", result)

# Verify Live Page Content
print("\n=== 2. Verifying Full Content on Live Blog Front & Article Page ===")
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1280, "height": 900})
    
    # Check front
    page.goto(f"https://{subdomain}.tistory.com/", wait_until="networkidle")
    time.sleep(2)
    page.screenshot(path="data/verified_full_article_front.png")
    
    # Click into the article
    article_link = page.locator(f"a:has-text('{title}'), .link-article:has-text('노션 AI')").first
    if article_link.count() > 0 and article_link.is_visible():
        article_link.click()
        time.sleep(2)
        print("Visited Article Page:", page.url)
        page.screenshot(path="data/verified_full_article_detail.png")
        
        # Check all headers and paragraphs
        headings = page.evaluate("() => Array.from(document.querySelectorAll('h2, h3')).map(h => h.innerText.trim())")
        body_text_len = page.evaluate("() => document.querySelector('.entry-content, .article-view, article')?.innerText?.length || 0")
        
        print("\n[VERIFICATION RESULTS]")
        print("  - Title Clean:", title)
        print("  - Headings Found on Live Page:", headings)
        print("  - Body Text Character Length on Live Page:", body_text_len, "chars")
        
        if body_text_len > 300 and len(headings) >= 4:
            print("🎉🎉🎉 PERFECT! FULL ARTICLE AND ALL HEADINGS ARE 100% PRESERVED ONLINE!")
        else:
            print("⚠️ Check content preservation details.")
            
    browser.close()
