import os
import sys
import time
from playwright.sync_api import sync_playwright

subdomain = "billionaire1004"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1400, "height": 950})
    
    # Check blog main
    page.goto(f"https://{subdomain}.tistory.com/", wait_until="networkidle")
    time.sleep(2)
    
    # Get all article links on main
    links = page.evaluate("""() => {
        return Array.from(document.querySelectorAll('a')).map(a => ({
            text: a.innerText.trim(),
            href: a.href
        })).filter(x => x.href.includes('/entry/') || x.href.match(/\\/\\d+$/));
    }""")
    print("ALL ARTICLE LINKS ON MAIN:", links[:10])
    
    # Visit the latest article
    if links:
        latest_url = links[0]['href']
        print(f"Visiting latest article: {latest_url} ({links[0]['text']})")
        page.goto(latest_url, wait_until="networkidle")
        time.sleep(2)
        
        # Check title, category, and body text
        data = page.evaluate("""() => {
            const cat = document.querySelector('.category, .txt_category, .box-category, .area_head .category')?.innerText?.trim() || '';
            const title = document.querySelector('h1, .tit_post, .title_post, .entry-title')?.innerText?.trim() || '';
            const body = document.querySelector('.entry-content, .article-view, article, .tt_article_useless_p_margin')?.innerText?.trim() || '';
            const headings = Array.from(document.querySelectorAll('.entry-content h2, .article-view h2, article h2')).map(h => h.innerText.trim());
            return {
                category: cat,
                title: title,
                bodyLength: body.length,
                headings: headings,
                bodyPreview: body.slice(0, 300)
            };
        }""")
        print("\n--- LATEST ARTICLE CONTENT AUDIT ---")
        print("URL:", latest_url)
        print("Category:", data['category'])
        print("Title:", data['title'])
        print("Headings:", data['headings'])
        print("Body Length:", data['bodyLength'])
        print("Body Preview:\n", data['bodyPreview'])
        page.screenshot(path="data/latest_article_check.png")
        
    browser.close()
