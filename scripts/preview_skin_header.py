import os
from playwright.sync_api import sync_playwright

def render_skin_preview(skin_dir, output_png):
    skin_html_path = os.path.join(skin_dir, "skin.html")
    style_css_path = os.path.join(skin_dir, "style.css")
    
    with open(skin_html_path, "r", encoding="utf-8") as f:
        html = f.read()
    with open(style_css_path, "r", encoding="utf-8") as f:
        css = f.read()
        
    # Replace standard Tistory tags with sample mockup content
    mock_replacements = {
        "[##_title_##]": "Grow Mindset",
        "[##_blogger_##]": "커리어 멘토",
        "[##_desc_##]": "자기계발 & 커리어 성장 연구소",
        "[##_image_##]": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=200&auto=format&fit=crop&q=80",
        "[##_blog_url_##]": "#",
        "[##_article_rep_category_link_##]": "#",
        "[##_article_rep_category_##]": "시간 관리&습관",
        "[##_article_rep_title_##]": "2026 포모도로 시간 관리법: 하루 3시간 몰입으로 인생을 바꾸는 실전 루틴",
        "[##_article_rep_author_##]": "커리어 멘토",
        "[##_article_rep_date_##]": "2026. 09. 01 17:03",
        "[##_s_ad_isolation_##]": "",
        "[##_article_rep_desc_##]": "<p>퇴근 후 주어지는 3시간을 어떻게 활용하느냐에 따라 1년 뒤 커리어와 삶의 궤적이 완전히 달라집니다.</p><h2>1. 왜 퇴근 후 포모도로 기법인가?</h2><p>단순한 타이머 설정이 아닌 뇌 과학 기반의 25분 초몰입 사이클입니다.</p>",
        "[##_article_rep_thumbnail_raw_url_##]": "https://images.unsplash.com/photo-1499750310107-5fef28a66643?w=1200&auto=format&fit=crop&q=80",
        "[##_category_list_##]": "<ul><li><a href='#'>시간 관리&습관 (12)</a></li><li><a href='#'>업무 스킬&커리어 (8)</a></li></ul>",
        "[##_rctps_rep_link_##]": "#",
        "[##_rctps_rep_title_##]": "미라클 모닝 5am 루틴 실천기",
        "[##_rctps_rep_date_##]": "2026.08.30",
        "[##_rctrp_rep_link_##]": "#",
        "[##_rctrp_rep_desc_##]": "정말 유익한 글 감사합니다!",
        "[##_rctrp_rep_name_##]": "김성장",
        "[##_tag_label_rep_##]": "<a href='#'>#포모도로</a> <a href='#'>#시간관리</a> <a href='#'>#몰입루틴</a>",
        "[##_count_today_##]": "1,248",
        "[##_count_yesterday_##]": "2,150",
        "[##_count_total_##]": "48,920",
    }
    
    # Strip Tistory conditional skin tags like <s_article_rep>, <s_permalink_article_rep>, etc.
    import re
    cleaned_html = html
    cleaned_html = re.sub(r'</?s_[^>]+>', '', cleaned_html)
    
    for tag, val in mock_replacements.items():
        cleaned_html = cleaned_html.replace(tag, val)
        
    # Inject CSS inline
    full_html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Blog Post Header Preview</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/xeicon@2.3.3/xeicon.min.css">
    <style>
    {css}
    </style>
</head>
<body>
    {cleaned_html}
</body>
</html>
"""

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.set_content(full_html, wait_until="networkidle")
        page.screenshot(path=output_png)
        browser.close()
    print(f"Rendered preview to: {output_png}")

if __name__ == "__main__":
    render_skin_preview(
        "c:/Users/kws911004/.gemini/antigravity/scratch/tistory-auto/skins/blog_5_grow_mindset",
        "c:/Users/kws911004/.gemini/antigravity/scratch/tistory-auto/data/blog_5_header_preview.png"
    )
