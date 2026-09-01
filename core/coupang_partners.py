"""
Coupang Partners HMAC API Integration & Smart Product Box Generator
Automatically injects affiliate product recommendation banners into blog articles.
"""

import os
import time
import hmac
import hashlib
import logging
from typing import List, Dict, Any, Optional
from urllib.parse import urlencode
import requests
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

API_BASE = "https://api-gateway.coupang.com"

class CoupangPartnersManager:
    def __init__(self):
        self.access_key = os.environ.get("COUPANG_ACCESS_KEY")
        self.secret_key = os.environ.get("COUPANG_SECRET_KEY")
        self.session = requests.Session()

    def is_configured(self) -> bool:
        return bool(self.access_key and self.secret_key and self.access_key != "your_coupang_access_key")

    def _generate_hmac(self, method: str, path: str, query: str = "") -> str:
        datetime_str = time.strftime("%y%m%dT%H%M%SZ", time.gmtime())
        message = datetime_str + method + path + query
        signature = hmac.new(
            bytes(self.secret_key, "utf-8"),
            message.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return (
            f"CEA algorithm=HmacSHA256, access-key={self.access_key}, "
            f"signed-date={datetime_str}, signature={signature}"
        )

    def search_products(self, keyword: str, limit: int = 2) -> List[Dict[str, Any]]:
        if not self.is_configured():
            return []

        path = "/v2/providers/affiliate_open_api/apis/openapi/products/search"
        params = {"keyword": keyword, "limit": limit, "subId": "tistory_auto"}
        query = urlencode(params)
        authorization = self._generate_hmac("GET", path, query)
        url = f"{API_BASE}{path}?{query}"

        headers = {
            "Authorization": authorization,
            "Content-Type": "application/json",
        }

        try:
            resp = self.session.get(url, headers=headers, timeout=8)
            resp.raise_for_status()
            data = resp.json().get("data", {})
            if isinstance(data, dict):
                return data.get("productData", [])
            return data if isinstance(data, list) else []
        except Exception as e:
            logger.warning(f"쿠팡 파트너스 API 상품 검색 실패: {e}")
            return []

    def generate_product_box_html(self, keyword: str) -> str:
        """Generate responsive styled product recommendation box with Coupang disclosure."""
        products = self.search_products(keyword, limit=2)
        if not products:
            return ""

        cards_html = ""
        for p in products:
            name = p.get("productName", "")
            img = p.get("productImage", "")
            price = f"{p.get('productPrice', 0):,}원"
            link = p.get("productUrl", "")

            cards_html += f"""
            <div style="flex: 1; min-width: 260px; border: 1px solid #e2e8f0; border-radius: 10px; padding: 14px; background: #ffffff; text-align: center; box-shadow: 0 2px 6px rgba(0,0,0,0.04);">
                <a href="{link}" target="_blank" rel="nofollow noopener" style="text-decoration: none; color: inherit;">
                    <img src="{img}" alt="{name}" style="max-height: 140px; object-fit: contain; margin-bottom: 10px; border-radius: 6px;">
                    <div style="font-size: 13px; font-weight: 600; color: #1e293b; line-height: 1.4; height: 38px; overflow: hidden; margin-bottom: 6px;">{name}</div>
                    <div style="font-size: 15px; font-weight: 800; color: #dc2626; margin-bottom: 10px;">{price}</div>
                    <span style="display: inline-block; background: #2563eb; color: #ffffff; padding: 6px 14px; border-radius: 6px; font-size: 12px; font-weight: 700;">최저가 확인하기 &gt;</span>
                </a>
            </div>
            """

        box_html = f"""
        <!-- COUPANG_PARTNERS_SECTION -->
        <div style="margin: 32px 0 20px; padding: 20px; background: #f8fafc; border: 1px dashed #cbd5e1; border-radius: 12px;">
            <div style="font-size: 14px; font-weight: 700; color: #0f172a; margin-bottom: 14px; display: flex; align-items: center;">
                <span style="background: #ef4444; color: white; padding: 2px 8px; border-radius: 4px; font-size: 11px; margin-right: 8px;">추천</span>
                '{keyword}' 관련 인기 추천 상품
            </div>
            <div style="display: flex; gap: 14px; flex-wrap: wrap;">
                {cards_html}
            </div>
            <p style="font-size: 11px; color: #94a3b8; text-align: center; margin-top: 12px; margin-bottom: 0;">
                ※ 이 포스팅은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다.
            </p>
        </div>
        """
        return box_html
