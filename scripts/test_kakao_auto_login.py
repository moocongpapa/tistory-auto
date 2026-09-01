import os
import time
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv()
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SESSION_DIR = os.path.join(BASE_DIR, "session_data")

email = os.environ.get("KAKAO_EMAIL")
password = os.environ.get("KAKAO_PASSWORD")

print(f"로그인 테스트 시작: {email} / {password[:3]}***")

with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(
        user_data_dir=SESSION_DIR,
        headless=True,
        viewport={"width": 1280, "height": 900},
        args=["--disable-blink-features=AutomationControlled"]
    )
    page = ctx.new_page()

    # 1. Open Tistory Auth
    page.goto("https://www.tistory.com/auth/login?redirectUrl=https%3A%2F%2Fsmartwork-lab.tistory.com%2Fmanage%2Fposts", wait_until="domcontentloaded", timeout=45000)
    time.sleep(3)
    print("현재 URL (1):", page.url)

    if "auth/login" in page.url:
        k_btn = page.locator("a.link_kakao_id, .btn_login.link_kakao_id").first
        if k_btn.is_visible():
            print("카카오 버튼 클릭...")
            k_btn.click()
            time.sleep(4)

    print("현재 URL (2):", page.url)
    page.screenshot(path=os.path.join(BASE_DIR, "data", "kakao_step_1.png"))

    if "accounts.kakao.com" in page.url:
        # Check if saved account exists
        saved_acc = page.locator(".item_account, .link_account, .tit_item").first
        if saved_acc.is_visible():
            print("저장된 간편 로그인 계정 발견:", saved_acc.inner_text().strip())
            saved_acc.click()
            time.sleep(4)
        else:
            print("ID / PW 입력 중...")
            id_input = page.locator("input[name='loginId'], #loginId, input#loginId--1").first
            id_input.fill(email)
            time.sleep(0.3)
            pw_input = page.locator("input[name='password'], #password, input#password--2").first
            pw_input.fill(password)
            time.sleep(0.3)
            
            # Close popup if exists
            close_btn = page.locator("button:has-text('닫기'), .btn_close").first
            if close_btn.is_visible():
                print("팝업 닫기 클릭...")
                close_btn.click(force=True)
                time.sleep(0.5)

            print("로그인 버튼 클릭...")
            page.evaluate("() => { (document.querySelector('button[type=\"submit\"]') || document.querySelector('.btn_g.highlight.submit'))?.click(); }")
            time.sleep(6)

    print("현재 URL (3):", page.url)
    page.screenshot(path=os.path.join(BASE_DIR, "data", "kakao_step_2.png"))

    # Direct check to manage/posts
    page.goto("https://smartwork-lab.tistory.com/manage/posts", wait_until="domcontentloaded", timeout=45000)
    time.sleep(3)
    print("최종 URL:", page.url)
    page.screenshot(path=os.path.join(BASE_DIR, "data", "kakao_step_3.png"))

    ctx.close()
