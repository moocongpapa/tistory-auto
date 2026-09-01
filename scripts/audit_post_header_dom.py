import os
import sys
import time
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1400, "height": 950})
    page.goto("https://billionaire1004.tistory.com/222", wait_until="networkidle")
    time.sleep(2)
    
    header_dom = page.evaluate("""() => {
        const h2 = document.querySelector('.title-article, h1, .tit_post, .entry-title');
        const header = h2 ? h2.closest('.article-header, .area-view, .inner-header, div') : null;
        return {
            h2HTML: h2 ? h2.outerHTML : '',
            headerHTML: header ? header.outerHTML.slice(0, 800) : '',
            computedStyles: h2 ? {
                display: window.getComputedStyle(h2).display,
                fontSize: window.getComputedStyle(h2).fontSize,
                flex: window.getComputedStyle(h2).flex,
                grid: window.getComputedStyle(h2).grid
            } : null,
            parentComputedStyles: h2 && h2.parentElement ? {
                display: window.getComputedStyle(h2.parentElement).display,
                flexDirection: window.getComputedStyle(h2.parentElement).flexDirection,
                gridTemplateColumns: window.getComputedStyle(h2.parentElement).gridTemplateColumns,
                gap: window.getComputedStyle(h2.parentElement).gap
            } : null
        };
    }""")
    
    import json
    print("HEADER DOM AUDIT:")
    print(json.dumps(header_dom, ensure_ascii=False, indent=2))
    
    browser.close()
