import os
from playwright.sync_api import sync_playwright

def render_article_header_preview():
    skin_dir = "c:/Users/kws911004/.gemini/antigravity/scratch/tistory-auto/skins/blog_5_grow_mindset"
    style_css_path = os.path.join(skin_dir, "style.css")
    
    with open(style_css_path, "r", encoding="utf-8") as f:
        css = f.read()
        
    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Post Header Clean Preview</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/xeicon@2.3.3/xeicon.min.css">
    <style>
    {css}
    body {{
        padding: 40px;
        background: #f8fafc;
        max-width: 900px;
        margin: 0 auto;
        font-family: -apple-system, BlinkMacSystemFont, "Apple SD Gothic Neo", "Pretendard Variable", Pretendard, Roboto, "Noto Sans KR", sans-serif;
    }}
    </style>
</head>
<body>
    <h3 style="color:#64748b; font-size:13px; font-weight:700; text-transform:uppercase; margin-bottom:12px;">1. 배경 이미지 없는 기본 모드 (Clean Minimal Card)</h3>
    
    <div class="article-header">
      <div class="article-header-overlay">
        <div class="inner-header">
          <div class="article-meta-wrap">
            <div class="article-category-badge">
              <a href="#">시간 관리&습관</a>
            </div>
            <h1 class="title-article">2026 포모도로 시간 관리법: 하루 3시간 몰입으로 인생을 바꾸는 실전 루틴</h1>
            <div class="article-info-bar">
              <span class="writer"><i class="xi-user-o"></i> 커리어 멘토</span>
              <span class="divider">•</span>
              <span class="date"><i class="xi-calendar"></i> 2026. 9. 1. 17:03</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <h3 style="color:#64748b; font-size:13px; font-weight:700; text-transform:uppercase; margin:40px 0 12px 0;">2. 썸네일 배경 히어로 모드 (Hero Image Card)</h3>
    
    <div class="article-header has-bg" style="background-image: url('https://images.unsplash.com/photo-1499750310107-5fef28a66643?w=1200&auto=format&fit=crop&q=80');">
      <div class="article-header-overlay">
        <div class="inner-header">
          <div class="article-meta-wrap">
            <div class="article-category-badge">
              <a href="#">시간 관리&습관</a>
            </div>
            <h1 class="title-article">2026 포모도로 시간 관리법: 하루 3시간 몰입으로 인생을 바꾸는 실전 루틴</h1>
            <div class="article-info-bar">
              <span class="writer"><i class="xi-user-o"></i> 커리어 멘토</span>
              <span class="divider">•</span>
              <span class="date"><i class="xi-calendar"></i> 2026. 9. 1. 17:03</span>
            </div>
          </div>
        </div>
      </div>
    </div>
</body>
</html>
"""

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1100, "height": 950})
        page.set_content(html, wait_until="networkidle")
        output_png = "c:/Users/kws911004/.gemini/antigravity/scratch/tistory-auto/data/article_header_redesign_preview.png"
        page.screenshot(path=output_png)
        browser.close()
    print("Article Header Preview generated!")

if __name__ == "__main__":
    render_article_header_preview()
