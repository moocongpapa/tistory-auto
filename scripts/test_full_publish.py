import os
import sys
import time
import logging

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from core.tistory_bot import TistoryBot

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("test_publish")

bot = TistoryBot(headless=True)
subdomain = "smartwork-lab"

test_title = f"테스트 자동 발행 포스팅 {int(time.time())}"
test_html = """
<p>안녕하세요! 이것은 티스토리 자동화 시스템에서 발행된 정식 테스트 글입니다.</p>
<h2>1. 테스트 안내</h2>
<p>자동 발행 엔진이 정상적으로 티스토리에 등록되는지 확인하고 있습니다.</p>
<blockquote>이 글이 정상 노출되면 자동 발행이 100% 성공한 것입니다.</blockquote>
"""

print(f"=== Starting Test Publish for {subdomain} ===")
result = bot.post_article(
    subdomain=subdomain,
    title=test_title,
    content_html=test_html,
    tags=["테스트", "자동발행", "성공검증"],
    category_name="테크 트렌드",
    is_draft=False
)
print("Result:", result)
