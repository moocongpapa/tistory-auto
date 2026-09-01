"""
Diagnostic test: thumbnail upload to Tistory editor via KImageUpload command.
Tests across multiple blogs to verify reliability.
"""
import os, sys, time, json, glob, random
from playwright.sync_api import sync_playwright

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
session_file = os.path.join(BASE_DIR, "session_data", "storage_state.json")

# Collect test thumbnails
thumb_dirs = {
    "smartwork-lab": "it_tech",
    "finance-roadmap-for-future": "finance_money",
    "policy-finder-365": "policy_life",
    "wellness-routine-lab": "wellness_health",
    "billionaire1004": "growth_career",
}

results = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(storage_state=session_file, viewport={"width": 1400, "height": 950})

    for subdomain, thumb_cat in thumb_dirs.items():
        # Pick a random thumbnail
        cat_dir = os.path.join(BASE_DIR, "assets", "preset_thumbnails", thumb_cat)
        thumbs = glob.glob(os.path.join(cat_dir, "*.jpg"))
        if not thumbs:
            print(f"[{subdomain}] No thumbnails in {cat_dir}")
            continue
        thumb_file = random.choice(thumbs)
        abs_thumb = os.path.abspath(thumb_file)
        print(f"\n{'='*60}")
        print(f"[{subdomain}] Testing with: {os.path.basename(thumb_file)}")
        print(f"{'='*60}")

        page = ctx.new_page()
        page.add_init_script("""
            window.confirm = function(msg) { return false; };
            window.alert = function(msg) {};
        """)
        page.on("dialog", lambda dialog: dialog.dismiss())

        try:
            # 1. Navigate to editor
            editor_url = f"https://{subdomain}.tistory.com/manage/newpost/"
            print(f"  1. Navigating to {editor_url}...")
            page.goto(editor_url, wait_until="domcontentloaded", timeout=30000)
            time.sleep(3)

            # 2. Check TinyMCE is ready
            editor_ready = page.evaluate("""() => {
                const ed = window.tinymce && window.tinymce.activeEditor;
                return {
                    hasEditor: !!ed,
                    hasKImageUpload: !!(ed && ed.execCommand),
                    editorId: ed ? ed.id : null
                };
            }""")
            print(f"  2. Editor ready: {editor_ready}")

            if not editor_ready.get("hasEditor"):
                print(f"  ❌ SKIP: No TinyMCE editor found for {subdomain}")
                results.append({"blog": subdomain, "success": False, "reason": "No editor"})
                page.close()
                continue

            # 3. Attempt KImageUpload with file chooser
            print(f"  3. Triggering KImageUpload command...")
            upload_success = False
            error_msg = ""

            for attempt in range(3):
                try:
                    with page.expect_file_chooser(timeout=8000) as fc_info:
                        page.evaluate("""() => {
                            const ed = window.tinymce && window.tinymce.activeEditor;
                            if (ed) { ed.execCommand('KImageUpload'); }
                        }""")

                    fc = fc_info.value
                    print(f"     ✅ File chooser captured (attempt {attempt+1}/3)! Setting file: {os.path.basename(abs_thumb)}")
                    fc.set_files(abs_thumb)
                    print(f"     Waiting 6s for Kakao CDN upload...")
                    time.sleep(6)

                    # Verify upload in editor content
                    verify = page.evaluate("""() => {
                        const ed = window.tinymce && window.tinymce.activeEditor;
                        if (!ed) return { ok: false, reason: 'no editor' };
                        const html = ed.getContent() || '';
                        const hasImage = html.includes('Image|') || html.includes('<figure') || html.includes('<img');
                        const imgs = Array.from(ed.dom.select('img')).map(i => i.src);
                        return {
                            ok: hasImage,
                            imgCount: imgs.length,
                            hasCdn: imgs.some(s => s.includes('kakaocdn.net')),
                            htmlLen: html.length
                        };
                    }""")
                    print(f"     Upload verify: {verify}")

                    if verify.get("ok"):
                        upload_success = True
                        break
                    else:
                        error_msg = f"Image not found in editor content after upload (attempt {attempt+1})"
                        print(f"     ⚠️ {error_msg}, retrying...")
                        time.sleep(1)

                except Exception as e:
                    error_msg = str(e)
                    print(f"     ⚠️ Attempt {attempt+1}/3 failed: {error_msg}")
                    time.sleep(1)
                    # Try clicking the editor body to re-focus before retrying
                    try:
                        page.evaluate("""() => {
                            const ed = window.tinymce && window.tinymce.activeEditor;
                            if (ed) { ed.focus(); }
                        }""")
                    except:
                        pass

            status = "✅ SUCCESS" if upload_success else f"❌ FAILED: {error_msg}"
            print(f"  4. Result: {status}")
            results.append({"blog": subdomain, "success": upload_success, "error": error_msg if not upload_success else ""})

        except Exception as e:
            print(f"  ❌ Fatal error for {subdomain}: {e}")
            results.append({"blog": subdomain, "success": False, "reason": str(e)})
        finally:
            page.close()

    browser.close()

print(f"\n{'='*60}")
print("SUMMARY")
print(f"{'='*60}")
for r in results:
    icon = "✅" if r.get("success") else "❌"
    print(f"  {icon} {r['blog']}: {'OK' if r.get('success') else r.get('error', r.get('reason', 'unknown'))}")
print(f"\nTotal: {sum(1 for r in results if r.get('success'))}/{len(results)} succeeded")
