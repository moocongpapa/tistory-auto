import os
import sys
import time
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1400, "height": 950})
    page.goto("https://billionaire1004.tistory.com/", wait_until="networkidle")
    time.sleep(2)
    
    # Click first article link
    first_link = page.locator("a[href*='/22'], a[href*='/entry/']").first
    print("First link href:", first_link.get_attribute("href"))
    first_link.click()
    time.sleep(2)
    
    # Audit header elements
    header_dom = page.evaluate("""() => {
        const h2 = document.querySelector('.title-article, h1, h2, .tit_post, .entry-title');
        const header = document.querySelector('.article-header, .box-meta, .area_head, .inner-header');
        return {
            url: window.location.href,
            headerHTML: header ? header.outerHTML.slice(0, 1000) : 'NO HEADER FOUND',
            allH2: Array.from(document.querySelectorAll('h1, h2, strong.tit_post')).map(h => ({
                tag: h.tagName,
                className: h.className,
                text: h.innerText.trim(),
                parentClass: h.parentElement ? h.parentElement.className : ''
            }))
        };
    }""")
    
    import json
    print("LIVE POST AUDIT:")
    print(json.dumps(header_dom, ensure_ascii=False, indent=2))
    page.screenshot(path="data/live_post_header_screenshot.png")
    
    browser.close()
