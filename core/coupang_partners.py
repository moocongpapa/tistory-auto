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

COUPANG_CATEGORY_LINKS = {
    "home": "https://link.coupang.com/a/gHPqNvDsBM",
    "golden_box": "https://link.coupang.com/a/gHPsRoNV5U",
    "rocket_fresh": "https://link.coupang.com/a/gHPuRVzF2O",
    "rocket_wow": "https://link.coupang.com/a/gHPx0gbVUi",
    "rocket_delivery": "https://link.coupang.com/a/gHPyXOx3Tw",
    "rocket_jikgu": "https://link.coupang.com/a/gHPzZq4DK0",
    "women_fashion": "https://link.coupang.com/a/gHPBecplEO",
    "men_fashion": "https://link.coupang.com/a/gHPCZSW7Wu",
    "baby_fashion": "https://link.coupang.com/a/gHPDYXPGfc",
    "travel": "https://link.coupang.com/a/gHPEOEywNw",
}

class CoupangPartnersManager:
    def __init__(self):
        self.access_key = os.environ.get("COUPANG_ACCESS_KEY")
        self.secret_key = os.environ.get("COUPANG_SECRET_KEY")
        self.tracking_id = os.environ.get("COUPANG_TRACKING_ID", "").strip()
        self.custom_link = os.environ.get("COUPANG_CUSTOM_LINK", "").strip()
        self.session = requests.Session()

    def is_configured(self) -> bool:
        # Returns True because default partner category links are always active!
        return True

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
        if not (self.access_key and self.secret_key):
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

    def _match_best_category_link(self, keyword: str) -> tuple[str, str, str]:
        """Smart match the most relevant Coupang category link based on keyword."""
        kw = (keyword or "").lower()

        # 1. Travel & Hotel
        if any(w in kw for w in ["여행", "호텔", "숙소", "항공", "펜션", "휴가", "글램핑", "리조트", "티켓", "테마파크"]):
            return COUPANG_CATEGORY_LINKS["travel"], "쿠팡 트래블", "✈️ 실시간 호텔·항공·레저 특가 예약"

        # 2. Nutrition & Supplements (Direct Global Jikgu)
        if any(w in kw for w in ["영양제", "비타민", "오메가", "마그네슘", "유산균", "해외직구", "직구", "단백질보충제", "영양"]):
            return COUPANG_CATEGORY_LINKS["rocket_jikgu"], "로켓직구", "📦 인기 영양제 & 해외 직구 파격 특가"

        # 3. Fresh Food & Diet
        if any(w in kw for w in ["식단", "샐러드", "단백질", "과일", "밀키트", "식품", "다이어트식", "신선"]):
            return COUPANG_CATEGORY_LINKS["rocket_fresh"], "로켓프레시", "🥑 내일 아침 도착! 신선식품·식단 특가"

        # 4. Fashion & Career Wear
        if any(w in kw for w in ["남성", "출근룩", "면접", "정장", "셔츠", "넥타이", "슬랙스"]):
            return COUPANG_CATEGORY_LINKS["men_fashion"], "남성패션", "👔 직장인 데일리 출근룩 & 비즈니스웨어"
        if any(w in kw for w in ["여성", "원피스", "가방", "뷰티", "화장품", "스킨케어", "선크림"]):
            return COUPANG_CATEGORY_LINKS["women_fashion"], "여성패션/뷰티", "💄 인기 여성패션 & 뷰티 베스트셀러"
        if any(w in kw for w in ["육아", "아동", "유아", "출산", "기저귀", "분유", "장난감"]):
            return COUPANG_CATEGORY_LINKS["baby_fashion"], "유아동", "👶 로켓 육아용품 & 아동 패션 특가"

        # 5. IT / Gadgets / Tech / Electronics
        if any(w in kw for w in ["노트북", "아이패드", "갤럭시", "맥북", "이어폰", "모니터", "스마트워치", "충전기", "키보드", "마우스", "스마트폰", "앱"]):
            return COUPANG_CATEGORY_LINKS["rocket_delivery"], "로켓배송", "⚡ IT·전자기기 로켓배송 최저가 보러가기"

        # 6. Savings, Life Hacks, Finance, General
        if any(w in kw for w in ["절약", "세금", "지원금", "할인", "가성비", "생활비", "연말정산", "환급"]):
            return COUPANG_CATEGORY_LINKS["golden_box"], "골드박스", "🏷️ 오늘 하루만! 골드박스 한정수량 특가"

        # Default fallback
        return COUPANG_CATEGORY_LINKS["golden_box"], "골드박스", "🏷️ 쿠팡 오늘의 골드박스 타임 특가"

    def generate_product_box_html(self, keyword: str) -> str:
        """Generate responsive styled product recommendation box with Coupang disclosure."""
        if not self.is_configured():
            return ""

        # 1. Real-time API product search if keys are active
        products = self.search_products(keyword, limit=2)
        if products:
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

            return f"""
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

        # 2. Smart Category Matching Banner using user's active affiliate links
        matched_url, badge_name, title_desc = self._match_best_category_link(keyword)

        golden_box_url = COUPANG_CATEGORY_LINKS["golden_box"]
        rocket_fresh_url = COUPANG_CATEGORY_LINKS["rocket_fresh"]
        rocket_delivery_url = COUPANG_CATEGORY_LINKS["rocket_delivery"]
        rocket_jikgu_url = COUPANG_CATEGORY_LINKS["rocket_jikgu"]

        return f"""
        <!-- COUPANG_PARTNERS_BANNER_SECTION -->
        <div style="margin: 36px 0 24px; padding: 20px 24px; background: linear-gradient(135deg, #f0f7ff 0%, #ffffff 100%); border: 1.5px solid #bfdbfe; border-radius: 14px; box-shadow: 0 4px 12px rgba(37,99,235,0.07);">
            <!-- Top Banner Header -->
            <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px; margin-bottom: 14px;">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <span style="background: #ef4444; color: #ffffff; padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: 800; letter-spacing: -0.2px;">{badge_name}</span>
                    <span style="font-size: 15px; font-weight: 800; color: #1e293b;">{title_desc}</span>
                </div>
                <a href="{matched_url}" target="_blank" rel="nofollow noopener" style="background: #2563eb; color: #ffffff; padding: 9px 20px; border-radius: 8px; text-decoration: none; font-size: 13px; font-weight: 800; display: inline-flex; align-items: center; gap: 6px; box-shadow: 0 2px 6px rgba(37,99,235,0.3); transition: all 0.2s;">
                    <span>특가 확인 &gt;</span>
                </a>
            </div>

            <!-- Quick Sub Category Bar -->
            <div style="display: flex; gap: 8px; flex-wrap: wrap; padding-top: 12px; border-top: 1px dashed #e2e8f0; font-size: 12px;">
                <span style="color: #64748b; font-weight: 600; padding: 3px 0;">빠른 바로가기:</span>
                <a href="{golden_box_url}" target="_blank" rel="nofollow noopener" style="background: #ffffff; border: 1px solid #cbd5e1; padding: 3px 10px; border-radius: 6px; color: #334155; text-decoration: none; font-weight: 600;">🏷️ 오늘 골드박스 특가</a>
                <a href="{rocket_delivery_url}" target="_blank" rel="nofollow noopener" style="background: #ffffff; border: 1px solid #cbd5e1; padding: 3px 10px; border-radius: 6px; color: #334155; text-decoration: none; font-weight: 600;">⚡ 로켓배송</a>
                <a href="{rocket_fresh_url}" target="_blank" rel="nofollow noopener" style="background: #ffffff; border: 1px solid #cbd5e1; padding: 3px 10px; border-radius: 6px; color: #334155; text-decoration: none; font-weight: 600;">🥑 로켓프레시</a>
                <a href="{rocket_jikgu_url}" target="_blank" rel="nofollow noopener" style="background: #ffffff; border: 1px solid #cbd5e1; padding: 3px 10px; border-radius: 6px; color: #334155; text-decoration: none; font-weight: 600;">📦 로켓직구</a>
            </div>

            <!-- Disclosure Statement -->
            <p style="font-size: 11px; color: #94a3b8; text-align: center; margin-top: 14px; margin-bottom: 0;">
                ※ 이 포스팅은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다.
            </p>
        </div>
        """
