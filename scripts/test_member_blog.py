import os
import time
from playwright.sync_api import sync_playwright

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SESSION_DIR = os.path.join(BASE_DIR, "session_data")

with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(
        user_data_dir=SESSION_DIR,
        headless=True,
        viewport={"width": 1280, "height": 900},
        args=["--disable-blink-features=AutomationControlled"]
    )
    page = ctx.new_page()
    print("1. https://www.tistory.com/member/blog 접속...")
    page.goto("https://www.tistory.com/member/blog", wait_until="domcontentloaded", timeout=30000)
    time.sleep(3)
    print("URL:", page.url)
    print("페이지 제목:", page.title())

    # Find blog links or write links on member/blog
    write_links = page.locator("a[href*='manage/newpost'], a[href*='smartwork-lab.tistory.com']")
    print(f"발견된 블로그/글쓰기 링크 수: {write_links.count()}")
    for i in range(min(5, write_links.count())):
        print(f"링크 {i}: text='{write_links.nth(i).inner_text().strip()}', href='{write_links.nth(i).get_attribute('href')}'")

    shot_path = os.path.join(BASE_DIR, "data", "member_blog_screenshot.png")
    page.screenshot(path=shot_path)
    print(f"스크린샷: {shot_path}")

    ctx.close()
