"""
Single Blog Test Runner
Generates and posts 1 article immediately to a specified blog.
"""

import os
import sys
import argparse
import logging
from dotenv import load_dotenv

# Set root directory in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

from core.scheduler import MultiBlogScheduler

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def main():
    parser = argparse.ArgumentParser(description="단일 블로그 즉시 포스팅 테스트")
    parser.add_argument("--blog", default="blog_1", help="블로그 ID (예: blog_1, blog_2, ...)")
    parser.add_argument("--draft", action="store_true", help="임시 저장 모드로 포스팅할지 여부")
    args = parser.parse_args()

    print(f"\n🚀 [{args.blog}] 포스팅 파이프라인을 실행합니다... (임시저장: {args.draft})\n")
    scheduler = MultiBlogScheduler()
    result = scheduler.run_blog_pipeline(blog_id=args.blog, is_draft_override=args.draft)
    print(f"\n결과: {result}\n")

if __name__ == "__main__":
    main()
