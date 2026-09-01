import os
import time
import logging
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SESSION_DIR = os.path.join(BASE_DIR, "session_data")

email = os.environ.get("KAKAO_EMAIL")
password = os.environ.get("KAKAO_PASSWORD")

print(f">> 카카오 자동 로그인 실행 중... 계정: {email}")

with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(
        user_data_dir=SESSION_DIR,
        headless=True,
        viewport={"width": 1280, "height": 900},
        args=["--disable-blink-features=AutomationControlled"]
    )
    page = ctx.new_page()

    # Go to login page
    page.goto("https://www.tistory.com/auth/login?redirectUrl=https%3A%2F%2Fwww.tistory.com%2Fmember%2Fblog", wait_until="domcontentloaded", timeout=45000)
    time.sleep(2)

    # Click yellow Kakao login button if on auth/login
    if "auth/login" in page.url:
        kakao_btn = page.locator("a.link_kakao_id, .btn_login, a:has-text('카카오계정으로 로그인')").first
        if kakao_btn.is_visible():
            kakao_btn.click()
            time.sleep(3)

    # Fill ID & PW on Kakao login screen
    if "accounts.kakao.com" in page.url:
        print(">> 카카오 계정 로그인 화면 감지. 아이디와 비밀번호 입력 중...")
        
        # ID input
        id_input = page.locator("input[name='loginId'], #loginId, input#loginId--1").first
        id_input.wait_for(state="visible", timeout=10000)
        id_input.fill(email)
        time.sleep(0.5)

        # Password input
        pw_input = page.locator("input[name='password'], #password, input#password--2").first
        pw_input.wait_for(state="visible", timeout=10000)
        pw_input.fill(password)
        time.sleep(0.5)

        # Click submit button
        submit_btn = page.locator("button[type='submit'], .btn_g.highlight.submit").first
        submit_btn.click()
        print(">> 로그인 버튼 클릭 완료! 인증 대기 중...")
        time.sleep(6)

    print(">> 현재 URL:", page.url)
    print(">> 현재 페이지 제목:", page.title())

    # Check if 2FA or device confirm is requested
    if "accounts.kakao.com" in page.url:
        print(">> ⚠️ 카카오 2단계 인증 또는 기기 확인 필요 여부 확인 중...")
        shot_path = os.path.join(BASE_DIR, "data", "kakao_login_result.png")
        page.screenshot(path=shot_path)
        print(f">> 스크린샷 저장: {shot_path}")
    else:
        print(">> 🎉 티스토리 로그인 완료 및 세션 쿠키 저장 성공!")
        # Sync member/blog
        page.goto("https://www.tistory.com/member/blog", wait_until="domcontentloaded", timeout=20000)
        time.sleep(2)
        print(">> 최종 동기화 URL:", page.url)

    ctx.close()
