"""
Test & Validate Theme-Specific Article Generation Across All 5 Blogs
"""

import os
import sys
import io
import yaml
from dotenv import load_dotenv

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from core.gemini_client import GeminiClient
from core.trend_collector import TrendCollector

load_dotenv()
CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", "config.yaml")

with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

gemini = GeminiClient()
trends_collector = TrendCollector()
trend_keywords = trends_collector.get_trend_keywords_list(limit=6)

print(f"=== 실시간 수집된 트렌드 키워드 ===")
print(", ".join(trend_keywords))
print()

blogs = config.get("blogs", [])
model_name = config.get("ai", {}).get("text_model", "gemini-3.5-flash")

for blog in blogs:
    blog_id = blog.get("id")
    blog_name = blog.get("name")
    themes = blog.get("themes", [])
    
    print(f"==================================================")
    print(f"🏢 [{blog_id}] {blog_name}")
    print(f"==================================================")
    
    for theme in themes:
        theme_name = theme.get("name")
        keywords = theme.get("keywords", [])
        
        print(f"\n📂 카테고리/테마: [{theme_name}]")
        print(f"   - 기본 키워드 풀: {', '.join(keywords[:4])}...")
        
        try:
            topic_info = gemini.discover_topic(
                blog_name=blog_name,
                theme_name=theme_name,
                keywords=keywords,
                previous_topics=[],
                trend_keywords=trend_keywords,
                model=model_name
            )
            print(f"   🎯 기획된 핵심 키워드: {topic_info.get('keyword')}")
            print(f"   💡 가제목 후보: {topic_info.get('title_candidate')}")
            print(f"   📝 글 전개 방향: {topic_info.get('topic')[:80]}...")
        except Exception as e:
            print(f"   ❌ 기획 에러: {e}")

print("\n=== 전체 카테고리별 테마 점검 완료 ===")
