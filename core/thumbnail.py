"""
High-CTR Blog Thumbnail Generator using Pillow
Creates 1200x630 (16:9) blog thumbnails with Korean typography, badge, and gradient overlay.
"""

import os
import textwrap
import logging
from typing import Optional
from PIL import Image, ImageDraw, ImageFont, ImageFilter

logger = logging.getLogger(__name__)

THUMBNAILS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "generated", "thumbnails")

class ThumbnailGenerator:
    def __init__(self, output_dir: str = THUMBNAILS_DIR):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.font_path = self._find_korean_font()

    def _find_korean_font(self) -> Optional[str]:
        candidates = [
            "C:/Windows/Fonts/malgunbd.ttf", # Malgun Gothic Bold
            "C:/Windows/Fonts/malgun.ttf",   # Malgun Gothic
            "C:/Windows/Fonts/NanumGothicBold.ttf",
            "C:/Windows/Fonts/NanumGothic.ttf",
            "C:/Windows/Fonts/gulim.ttc",
            "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf",
            "/System/Library/Fonts/AppleSDGothicNeo.ttc"
        ]
        for path in candidates:
            if os.path.exists(path):
                return path
        return None

    def _create_gradient_background(self, width: int = 1200, height: int = 630) -> Image.Image:
        base = Image.new("RGB", (width, height), color=(15, 23, 42)) # Slate 900
        draw = ImageDraw.Draw(base)
        for y in range(height):
            # Gradient from deep slate-blue to dark indigo
            r = int(15 + (y / height) * 20)
            g = int(23 + (y / height) * 35)
            b = int(42 + (y / height) * 75)
            draw.line([(0, y), (width, y)], fill=(r, g, b))
        return base

    def create_thumbnail(
        self,
        title: str,
        badge_text: str = "BLOG POST",
        base_image_path: Optional[str] = None,
        filename_prefix: str = "thumb"
    ) -> str:
        width, height = 1200, 630

        if base_image_path and os.path.exists(base_image_path):
            try:
                img = Image.open(base_image_path).convert("RGB")
                # Center crop & resize to 1200x630
                img_ratio = img.width / img.height
                target_ratio = width / height
                if img_ratio > target_ratio:
                    new_width = int(img.height * target_ratio)
                    offset = (img.width - new_width) // 2
                    img = img.crop((offset, 0, offset + new_width, img.height))
                else:
                    new_height = int(img.width / target_ratio)
                    offset = (img.height - new_height) // 2
                    img = img.crop((0, offset, img.width, offset + new_height))
                img = img.resize((width, height), Image.Resampling.LANCZOS)
                
                # Apply soft blur for readability
                img = img.filter(ImageFilter.GaussianBlur(radius=2))

                # Add dark overlay for contrast
                overlay = Image.new("RGBA", (width, height), (0, 0, 0, 140))
                img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
            except Exception as e:
                logger.warning(f"Failed to process base image: {e}. Using gradient.")
                img = self._create_gradient_background(width, height)
        else:
            img = self._create_gradient_background(width, height)

        draw = ImageDraw.Draw(img)

        # Load Fonts
        try:
            if self.font_path:
                badge_font = ImageFont.truetype(self.font_path, 32)
                title_font = ImageFont.truetype(self.font_path, 54)
            else:
                badge_font = ImageFont.load_default()
                title_font = ImageFont.load_default()
        except Exception:
            badge_font = ImageFont.load_default()
            title_font = ImageFont.load_default()

        # 1. Draw Category Badge
        badge_text = f" {badge_text.strip()} "
        badge_bbox = draw.textbbox((0, 0), badge_text, font=badge_font)
        badge_w = badge_bbox[2] - badge_bbox[0] + 30
        badge_h = badge_bbox[3] - badge_bbox[1] + 16
        badge_x = 90
        badge_y = 110

        # Draw rounded rectangle for badge
        draw.rounded_rectangle(
            [badge_x, badge_y, badge_x + badge_w, badge_y + badge_h],
            radius=12,
            fill=(49, 130, 206) # Blue 500
        )
        draw.text(
            (badge_x + 15, badge_y + 6),
            badge_text,
            fill=(255, 255, 255),
            font=badge_font
        )

        # 2. Draw Title (Word-wrapped)
        # Clean title (remove special clutter)
        clean_title = title.replace("\"", "").replace("'", "")
        wrapped_lines = textwrap.wrap(clean_title, width=17)
        if len(wrapped_lines) > 3:
            wrapped_lines = wrapped_lines[:3]
            wrapped_lines[2] = wrapped_lines[2] + "..."

        start_y = 210
        line_height = 76
        for i, line in enumerate(wrapped_lines):
            y = start_y + (i * line_height)
            # Text shadow
            draw.text((92, y + 2), line, fill=(0, 0, 0), font=title_font)
            draw.text((90, y), line, fill=(255, 255, 255), font=title_font)

        # 3. Draw Bottom Accent Bar
        draw.rectangle([90, height - 70, 250, height - 64], fill=(236, 201, 75)) # Gold / Yellow accent

        # Save output
        out_filename = f"{filename_prefix}_{int(os.path.getmtime(self.font_path) if self.font_path else 0)}_{os.getpid()}_{abs(hash(title)) % 10000}.jpg"
        out_path = os.path.join(self.output_dir, out_filename)
        img.save(out_path, "JPEG", quality=95)
        logger.info(f"Thumbnail created at: {out_path}")
        return out_path
