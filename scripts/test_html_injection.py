import os
import time
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv()
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SESSION_DIR = os.path.join(BASE_DIR, "session_data")

email = os.environ.get("KAKAO_EMAIL")
password = os.environ.get("KAKAO_PASSWORD")

test_html = """
<h2>1. ChatGPT 프롬프트 작성의 핵심 원리</h2>
<p>업무 효율을 3배 이상 극대화하려면 명확한 역할(Role)과 맥락(Context)을 제공해야 합니다.</p>
<!-- ADSENSE_MID -->
<h2>2. 실전에서 바로 쓰는 5가지 템플릿</h2>
<p>보고서 요약, 이메일 초안 작성 등 실무에 즉시 적용 가능한 템플릿을 소개합니다.</p>
"""

with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(
        user_data_dir=SESSION_DIR,
        headless=True,
        viewport={"width": 1280, "height": 900},
        args=["--disable-blink-features=AutomationControlled"]
    )
    page = ctx.new_page()

    # Handle dialogs
    def handle_dialog(dialog):
        print(f">> 다이얼로그 감지: {dialog.message}")
        dialog.accept()

    page.on("dialog", handle_dialog)

    editor_url = "https://smartwork-lab.tistory.com/manage/newpost/"
    page.goto(editor_url, wait_until="domcontentloaded", timeout=45000)
    time.sleep(3)

    # Fill title
    title_inp = page.locator("#post-title-inp, textarea.textarea_tit").first
    title_inp.wait_for(state="visible", timeout=20000)
    title_inp.fill("[완전 테스트] ChatGPT 프롬프트 작성 꿀팁 총정리")
    print(">> 제목 입력 완료")

    # Switch to HTML mode
    try:
        mode_btn = page.locator("#editor-mode-layer-btn-open, button.btn_mode").first
        if mode_btn.is_visible():
            mode_btn.click()
            time.sleep(0.5)
            html_opt = page.locator("#editor-mode-html, button:has-text('HTML'), li:has-text('HTML')").first
            if html_opt.is_visible():
                html_opt.click()
                print(">> HTML 모드 선택 클릭 완료")
                time.sleep(1.5)
    except Exception as e:
        print(">> 모드 전환 예외:", e)

    # 5-stage HTML Content Injection
    res = page.evaluate(
        """(html) => {
            // 1. CodeMirror
            const cm = document.querySelector('.CodeMirror');
            if (cm && cm.CodeMirror) {
                cm.CodeMirror.setValue(html);
                return 'CodeMirror injected';
            }
            // 2. Textarea
            const textarea = document.querySelector('textarea.html') || document.querySelector('#editor-mode-html-textarea') || document.querySelector('textarea.mce-textbox');
            if (textarea) {
                textarea.value = html;
                textarea.dispatchEvent(new Event('input', { bubbles: true }));
                textarea.dispatchEvent(new Event('change', { bubbles: true }));
                return 'Textarea injected';
            }
            // 3. TinyMCE
            if (window.tinymce && window.tinymce.activeEditor) {
                window.tinymce.activeEditor.setContent(html);
                return 'TinyMCE injected';
            }
            // 4. Iframe body
            const iframe = document.querySelector('#content-editor-iframe') || document.querySelector('iframe');
            if (iframe && iframe.contentDocument && iframe.contentDocument.body) {
                iframe.contentDocument.body.innerHTML = html;
                return 'Iframe body injected';
            }
            // 5. ContentEditable Root
            const root = document.querySelector('#editor-root') || document.querySelector('.mce-content-body');
            if (root) {
                root.innerHTML = html;
                root.dispatchEvent(new Event('input', { bubbles: true }));
                return 'Root DOM injected';
            }
            return 'None matched';
        }""",
        test_html
    )
    print(f">> 본문 주입 결과: {res}")
    time.sleep(2)

    # Save as draft
    page.evaluate("() => { (document.querySelector('#temp-save-btn') || document.querySelector('.btn_save'))?.click(); }")
    print(">> 임시저장 클릭 완료")
    time.sleep(3)

    shot_path = os.path.join(BASE_DIR, "data", "test_content_injected.png")
    page.screenshot(path=shot_path)
    print(">> 스크린샷:", shot_path)
    ctx.close()
