import os
import sys
import time
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
session_file = os.path.join(BASE_DIR, "session_data", "storage_state.json")

blogs = [
    ("blog_1", "smartwork-lab", "Smart Work Lab"),
    ("blog_2", "finance-roadmap-for-future", "Money Roadmap 24"),
    ("blog_3", "policy-finder365", "정책 알리미 365"),
    ("blog_4", "wellness-routine", "웰니스 루틴 연구소"),
    ("blog_5", "billionaire1004", "Grow Mindset")
]

all_blog_categories = {}

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(storage_state=session_file, viewport={"width": 1400, "height": 950})
    page = ctx.new_page()
    
    for b_id, sub, name in blogs:
        print(f"\n--- Scraping Real Categories for [{name}] ({sub}) ---")
        page.goto(f"https://{sub}.tistory.com/manage/newpost/", wait_until="networkidle")
        time.sleep(2)
        
        # Click category button
        cat_btn = page.locator("#category-btn, .btn_category, button:has-text('카테고리')").first
        if cat_btn.is_visible():
            cat_btn.click()
            time.sleep(1)
            
            categories = page.evaluate("""() => {
                const list = document.querySelectorAll('.list_category li, .layer_category li, ul.list_category li');
                return Array.from(list).map(el => el.innerText.trim()).filter(t => t.length > 0 && t !== '카테고리 없음');
            }""")
            all_blog_categories[b_id] = {
                "name": name,
                "subdomain": sub,
                "categories": categories
            }
            print(f"Found {len(categories)} categories:", categories)
            
    browser.close()

import json
with open("data/real_tistory_categories.json", "w", encoding="utf-8") as f:
    json.dump(all_blog_categories, f, ensure_ascii=False, indent=2)
print("\nSaved real categories to data/real_tistory_categories.json!")
