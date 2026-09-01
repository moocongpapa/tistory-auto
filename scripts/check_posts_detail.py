import os
import sys
import time
from playwright.sync_api import sync_playwright

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
session_dir = os.path.join(BASE_DIR, "session_data")

with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(user_data_dir=session_dir, headless=True)
    page = ctx.new_page()
    page.goto("https://smartwork-lab.tistory.com/manage/posts", wait_until="networkidle")
    time.sleep(3)
    
    rows = page.evaluate("""() => {
        return Array.from(document.querySelectorAll('.list_post li, table tbody tr, .item_post, .area_item')).map(el => ({
            title: el.querySelector('.tit_post, .txt_tit, a.link_tit, a[href*="/manage/newpost"]') ? el.querySelector('.tit_post, .txt_tit, a.link_tit, a[href*="/manage/newpost"]').innerText.trim() : el.innerText.trim(),
            link: el.querySelector('a')?.href || '',
            status: el.innerText.includes('발행') ? '발행' : (el.innerText.includes('임시') ? '임시' : (el.innerText.includes('비공개') ? '비공개' : '기타')),
            fullText: el.innerText.trim().replace(/\\n+/g, ' | ')
        }));
    }""")
    print("SMARTWORK-LAB POST ROWS COUNT:", len(rows))
    for idx, r in enumerate(rows[:10], 1):
        print(f"{idx}. {r['fullText']}")
        
    ctx.close()
