import os
import sys
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from dotenv import load_dotenv
load_dotenv()

from core.scheduler import MultiBlogScheduler

scheduler = MultiBlogScheduler()
print(">> 블로그 1 (Smart Work Lab) 공개 포스팅 파이프라인 시작...")
result = scheduler.run_blog_pipeline("blog_1", is_draft_override=False)
print(">> 최종 결과:", result)
