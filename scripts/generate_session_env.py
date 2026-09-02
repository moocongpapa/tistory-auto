import os
import sys
import json
import time
import subprocess
from playwright.sync_api import sync_playwright

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SESSION_DIR = os.path.join(BASE_DIR, 'session_data')
STATE_FILE = os.path.join(SESSION_DIR, 'storage_state.json')

def main():
    os.makedirs(SESSION_DIR, exist_ok=True)
    print()
    print('=' * 65)
    print(' 🔑 [카카오 해외 IP 보안 우회 세션 생성기 for Render]')
    print('=' * 65)
    print(' 1. 잠시 후 크롬 브라우저가 자동으로 열립니다.')
    print(' 2. 카카오 [아이디/비밀번호]를 입력하여 로그인을 완료해 주세요.')
    print(' 3. 티스토리 메인 화면(또는 블로그 관리자)이 정상적으로 뜨면,')
    print(' 4. 이 터미널 창으로 돌아와 [Enter] 키를 누르면 세션이 자동 생성됩니다.')
    print('=' * 65)
    print()

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=['--disable-blink-features=AutomationControlled']
        )
        context = browser.new_context(
            viewport={'width': 1280, 'height': 850},
            storage_state=STATE_FILE if os.path.exists(STATE_FILE) else None
        )
        page = context.new_page()

        target_url = 'https://www.tistory.com/auth/login?redirectUrl=https%3A%2F%2Fwww.tistory.com%2Fmember%2Fblog'
        try:
            page.goto(target_url, wait_until='domcontentloaded', timeout=45000)
            time.sleep(1.5)
            kakao_btn = page.locator("a.link_kakao_id, .btn_login, a:has-text('카카오계정으로 로그인')").first
            if kakao_btn.is_visible():
                kakao_btn.click()
        except Exception:
            pass

        print('>> 브라우저에서 카카오 로그인을 완료해 주세요...')
        input('>> 로그인을 성공적으로 마치셨다면 여기서 [Enter] 키를 누르세요: ')

        # Sync blog state
        try:
            page.goto('https://www.tistory.com/member/blog', wait_until='domcontentloaded', timeout=15000)
            time.sleep(2)
        except Exception:
            pass

        # Save storage state
        context.storage_state(path=STATE_FILE)
        browser.close()

    # Read state json as one-line string
    with open(STATE_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    session_str = json.dumps(data)

    # Try copying to macOS clipboard automatically
    copied = False
    try:
        p = subprocess.Popen(['pbcopy'], stdin=subprocess.PIPE)
        p.communicate(session_str.encode('utf-8'))
        copied = True
    except Exception:
        pass

    print()
    print('=' * 65)
    print(' 🎉 카카오 로그인 인증 세션 추출 완료!')
    print('=' * 65)
    if copied:
        print(' 📋 [맥북 클립보드에 자동 복사되었습니다! (Cmd + V로 바로 붙여넣기 가능)]')
    print()
    print('[Render 등록 가이드]')
    print(' 1. Render 대시보드 (https://dashboard.render.com) -> tistory-auto -> Environment 접속')
    print(' 2. Add Environment Variable 클릭')
    print('    - Key: SESSION_STORAGE_STATE')
    print('    - Value: 아래 세션 텍스트 전체 붙여넣기')
    print(' 3. Save Changes 클릭!')
    print('=' * 65)
    print()
    print('--- [SESSION_STORAGE_STATE 값 시작] ---')
    print(session_str)
    print('--- [SESSION_STORAGE_STATE 값 끝] ---')
    print()

if __name__ == '__main__':
    main()
