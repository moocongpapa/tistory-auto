import os
import sys
import time
from playwright.sync_api import sync_playwright

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
session_dir = os.path.join(BASE_DIR, "session_data")

with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(user_data_dir=session_dir, headless=True)
    page = ctx.new_page()
    
    # 1. Check manage/posts
    page.goto("https://smartwork-lab.tistory.com/manage/posts", wait_until="networkidle")
    time.sleep(3)
    page.screenshot(path="data/manage_posts_screen.png")
    
    manage_titles = page.evaluate("""() => {
        return Array.from(document.querySelectorAll('a.link_tit, .tit_post, .txt_tit, a[href*="/entry/"]')).map(el => el.innerText.trim()).filter(x => x.length > 0);
    }""")
    print("=== SMARTWORK-LAB MANAGE POST TITLES ===")
    for idx, t in enumerate(manage_titles[:10], 1):
        print(f"{idx}. {t}")

    # 2. Check billionaire1004 manage/posts
    page.goto("https://billionaire1004.tistory.com/manage/posts", wait_until="networkidle")
    time.sleep(3)
    b_titles = page.evaluate("""() => {
        return Array.from(document.querySelectorAll('a.link_tit, .tit_post, .txt_tit, a[href*="/entry/"]')).map(el => el.innerText.trim()).filter(x => x.length > 0);
    }""")
    print("=== BILLIONAIRE1004 MANAGE POST TITLES ===")
    for idx, t in enumerate(b_titles[:10], 1):
        print(f"{idx}. {t}")

    ctx.close()
