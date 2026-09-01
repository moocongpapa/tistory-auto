"""
High-Resolution Preset Image Thumbnail Generator
Selects aesthetically pleasing, relevant high-res curated photos (no text clutter)
by theme category for maximum CTR and clean Unsplash/Pinterest-style blog aesthetics.
"""

import os
import glob
import shutil
import random
import logging
from typing import Optional
from PIL import Image, ImageOps

logger = logging.getLogger(__name__)

# Base directory for the project
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Category mapping from blog theme keywords to preset folders
CATEGORY_MAPPINGS = {
    "it_tech": ["it", "tech", "ai", "테크", "기기", "앱", "코딩", "자동화", "소프트웨어", "컴퓨터", "맥북", "생산성"],
    "finance_money": ["금융", "재테크", "절세", "주식", "etf", "투자", "머니", "청년도약", "통장", "대출", "가계부", "종잣돈"],
    "policy_life": ["정책", "지원금", "복지", "생활", "절약", "공과금", "k-패스", "청약", "지원", "청년월세", "국비지원"],
    "wellness_health": ["웰니스", "건강", "식단", "다이어트", "영양제", "피로", "스트레칭", "홈트", "수면", "루틴", "간헐적"],
    "growth_career": ["마인드", "자기계발", "커리어", "시간", "습관", "업무", "기획서", "도서", "독서", "이직", "동기부여"]
}

class ThumbnailGenerator:
    def __init__(
        self, 
        preset_base_dir: Optional[str] = None
    ):
        self.preset_base_dir = preset_base_dir or os.path.join(PROJECT_ROOT, "assets", "preset_thumbnails")
        os.makedirs(self.preset_base_dir, exist_ok=True)

    def _resolve_category(self, theme_name: str, blog_id: str = "") -> str:
        """Map theme or blog_id to preset thumbnail category."""
        # Check by blog ID first
        if blog_id == "blog_1":
            return "it_tech"
        elif blog_id == "blog_2":
            return "finance_money"
        elif blog_id == "blog_3":
            return "policy_life"
        elif blog_id == "blog_4":
            return "wellness_health"
        elif blog_id == "blog_5":
            return "growth_career"

        # Check by theme text matching
        theme_lower = (theme_name or "").lower()
        for cat_key, keywords in CATEGORY_MAPPINGS.items():
            for kw in keywords:
                if kw in theme_lower:
                    return cat_key

        return random.choice(list(CATEGORY_MAPPINGS.keys()))

    def get_preset_image(self, category: str) -> Optional[str]:
        """Fetch a random high-quality curated photo directly from the category preset folder."""
        cat_dir = os.path.join(self.preset_base_dir, category)
        if not os.path.exists(cat_dir):
            cat_dir = self.preset_base_dir

        images = glob.glob(os.path.join(cat_dir, "*.jpg")) + \
                 glob.glob(os.path.join(cat_dir, "*.jpeg")) + \
                 glob.glob(os.path.join(cat_dir, "*.png"))

        if images:
            chosen = random.choice(images)
            abs_chosen = os.path.abspath(chosen)
            logger.info(f"선택된 프리셋 썸네일 원본: {abs_chosen} (카테고리: {category})")
            return abs_chosen
        return None

    def create_thumbnail(
        self,
        title: str = "",
        badge_text: str = "",
        theme_name: str = "",
        blog_id: str = "",
        base_image_path: Optional[str] = None,
        filename_prefix: str = "thumb"
    ) -> str:
        """
        Directly uses preset curated images from assets/preset_thumbnails without duplicate generation.
        Returns the absolute file path of the chosen preset image.
        """
        category = self._resolve_category(theme_name or badge_text, blog_id=blog_id)
        source_image_path = base_image_path or self.get_preset_image(category)

        if source_image_path and os.path.exists(source_image_path):
            return os.path.abspath(source_image_path)

        # Fallback: search any preset image
        all_presets = glob.glob(os.path.join(self.preset_base_dir, "**", "*.jpg"), recursive=True) + \
                      glob.glob(os.path.join(self.preset_base_dir, "**", "*.png"), recursive=True)
        if all_presets:
            return os.path.abspath(random.choice(all_presets))

        raise FileNotFoundError(f"assets/preset_thumbnails 폴더에 사용 가능한 썸네일 이미지가 없습니다: {self.preset_base_dir}")
