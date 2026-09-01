import os
import time
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv()
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SESSION_DIR = os.path.join(BASE_DIR, "session_data")

email = os.environ.get("KAKAO_EMAIL")
password = os.environ.get("KAKAO_PASSWORD")

test_title = "[실제 테스트] 스마트 업무 자동화 가이드"
test_html = """
<h2>1. 업무 효율화를 위한 스마트 팁</h2>
<p>반복적인 일상 업무를 간소화하고 시간을 절약하는 핵심 노하우를 알아봅니다.</p>
<!-- ADSENSE_MID -->
<h2>2. 실무 템플릿과 적용 방안</h2>
<p>실제 업무에 바로 적용할 수 있는 구체적인 단계별 매뉴얼입니다.</p>
"""

with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(
        user_data_dir=SESSION_DIR,
        headless=True,
        viewport={"width": 1280, "height": 900},
        args=["--disable-blink-features=AutomationControlled"]
    )
    page = ctx.new_page()

    def handle_dialog(dialog):
        print(f"다이얼로그: {dialog.message}")
        dialog.accept()

    page.on("dialog", handle_dialog)

    editor_url = "https://smartwork-lab.tistory.com/manage/newpost/"
    page.goto(editor_url, wait_until="domcontentloaded", timeout=45000)
    time.sleep(3)

    # 1. Title
    t_input = page.locator("#post-title-inp, textarea.textarea_tit").first
    t_input.wait_for(state="visible", timeout=15000)
    t_input.fill(test_title)
    print("1. 제목 입력 완료")

    # 2. Inspect Editor JS Objects
    objs = page.evaluate("""() => {
        return {
            hasTinyMCE: typeof window.tinymce !== 'undefined',
            hasActiveEditor: window.tinymce && !!window.tinymce.activeEditor,
            hasEditor: typeof window.editor !== 'undefined',
            hasCodeMirror: typeof window.CodeMirror !== 'undefined',
            bodyText: document.body.innerText.substring(0, 100)
        };
    }""")
    print("2. 에디터 전역 객체 상태:", objs)

    # 3. Try injecting into default editor first (TinyMCE or ContentEditable)
    inject1 = page.evaluate("""(html) => {
        if (window.tinymce && window.tinymce.activeEditor) {
            window.tinymce.activeEditor.setContent(html);
            window.tinymce.activeEditor.save();
            return 'tinymce.activeEditor.setContent + save() success';
        }
        return 'tinymce not active';
    }""", test_html)
    print("3. TinyMCE 주입 시도:", inject1)

    # 4. Switch to HTML mode and check CodeMirror
    try:
        page.locator("#editor-mode-layer-btn-open, button.btn_mode").first.click()
        time.sleep(0.5)
        page.locator("#editor-mode-html, button:has-text('HTML')").first.click()
        time.sleep(2)
    except Exception as e:
        print("4. 모드 전환 에러:", e)

    inject2 = page.evaluate("""(html) => {
        const cmEl = document.querySelector('.CodeMirror');
        if (cmEl && cmEl.CodeMirror) {
            cmEl.CodeMirror.setValue(html);
            cmEl.CodeMirror.save(); // Sync back to textarea!
            return 'CodeMirror.setValue + save() success';
        }
        return 'CodeMirror not found';
    }""", test_html)
    print("5. CodeMirror 주입 시도:", inject2)

    # 5. Switch back to 기본모드 to enforce HTML parsing if needed
    try:
        page.locator("#editor-mode-layer-btn-open, button.btn_mode").first.click()
        time.sleep(0.5)
        page.locator("#editor-mode-markdown, #editor-mode-basic, button:has-text('기본모드')").first.click()
        time.sleep(1.5)
        print("6. 기본모드로 다시 복귀 (렌더링 동기화 완료)")
    except Exception as e:
        print("6. 기본모드 복귀 패스:", e)

    # 6. Check final content in editor
    final_content = page.evaluate("""() => {
        if (window.tinymce && window.tinymce.activeEditor) {
            return window.tinymce.activeEditor.getContent();
        }
        const cm = document.querySelector('.CodeMirror');
        if (cm && cm.CodeMirror) {
            return cm.CodeMirror.getValue();
        }
        return document.querySelector('#editor-root, .mce-content-body')?.innerHTML || 'EMPTY';
    }""")
    print("7. 에디터 내 최종 본문 확인 (길이):", len(final_content))
    print("7. 에디터 내 최종 본문 미리보기:", final_content[:150])

    shot_path = os.path.join(BASE_DIR, "data", "final_editor_check.png")
    page.screenshot(path=shot_path)
    print(f"8. 최종 스크린샷: {shot_path}")

    ctx.close()
