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
    page.goto("https://smartwork-lab.tistory.com/manage/newpost/", wait_until="domcontentloaded", timeout=45000)
    time.sleep(3)

    # Click Category button
    cat_btn = page.locator("#category-btn, .btn_category, button:has-text('카테고리')").first
    print("카테고리 버튼 발견 여부:", cat_btn.is_visible())
    cat_btn.click()
    time.sleep(1)

    # List all category items in layer
    cat_items = page.locator("#category-layer, .layer_category, .list_category, .item_category, .box_category li, .box_category a, .box_category span")
    print(f"카테고리 항목 수: {cat_items.count()}")
    for i in range(min(20, cat_items.count())):
        txt = cat_items.nth(i).inner_text().strip().replace("\n", " > ")
        cls = cat_items.nth(i).get_attribute("class") or ""
        tag = cat_items.nth(i).evaluate("el => el.tagName")
        if txt:
            print(f"[{i}] <{tag} class='{cls}'> text='{txt}'")

    ctx.close()
