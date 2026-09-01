import os
import sys
import time
import logging

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from core.tistory_bot import TistoryBot
from playwright.sync_api import sync_playwright

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("test_real_publish")

bot = TistoryBot(headless=True)
subdomain = "smartwork-lab"

title = f"직장인 생산성 200% 올리는 노션 AI 활용 가이드 {int(time.time())}"
html_body = """
<div style="background:#f8fafc; border-left:4px solid #3b82f6; padding:16px; border-radius:8px; margin-bottom:20px;">
    <strong>💡 핵심 요약:</strong> 매일 반복되는 업무 문서와 기획안 작성을 노션 AI로 10분 만에 끝내는 실전 활용 팁을 소개합니다.
</div>
<h2>1. 노션 AI로 시작하는 스마트 워크</h2>
<p>직장인들에게 가장 부족한 것은 시간입니다. 노션 AI의 자동 요약 및 템플릿 생성 기능을 활용하면 보고서 초안 작성 시간을 획기적으로 줄일 수 있습니다.</p>
<h2>2. 실전 적용 3단계 프로세스</h2>
<ol>
    <li><strong>회의록 자동 요약:</strong> 긴 회의 녹취록을 3줄 액션 아이템으로 변환</li>
    <li><strong>기획서 템플릿 생성:</strong> 원하는 주제 키워드만 넣으면 목차 자동 구성</li>
    <li><strong>문법 및 톤앤매너 교정:</strong> 보고용 비즈니스 문체로 원클릭 변환</li>
</ol>
<p>지금 바로 시작하여 정시 퇴근의 여유를 누려보세요!</p>
"""

print(f"=== 1. Posting Article to [{subdomain}] ===")
res = bot.post_article(
    subdomain=subdomain,
    title=title,
    content_html=html_body,
    tags=["노션AI", "생산성향상", "직장인꿀팁", "업무자동화", "스마트워크"],
    category_name="AI&업무 자동화",
    is_draft=False
)
print("Publish Result:", res)

# 2. Open public blog and verify post appears online
print("\n=== 2. Checking Live Blog Online ===")
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1280, "height": 900})
    
    # Visit blog front page
    page.goto(f"https://{subdomain}.tistory.com/", wait_until="networkidle")
    time.sleep(3)
    page.screenshot(path="data/verified_live_front_post.png")
    
    # Check post titles visible on front page
    front_titles = page.evaluate("""() => {
        return Array.from(document.querySelectorAll('h1, h2, h3, h4, .title, .tit_post, .link_article, a')).map(el => el.innerText.trim()).filter(t => t.length > 5);
    }""")
    print("Found Titles on Live Blog Front Page:")
    for idx, t in enumerate(front_titles[:15], 1):
        print(f"  {idx}. {t}")
        
    browser.close()
