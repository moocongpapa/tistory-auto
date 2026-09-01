"""
Script to generate Tistory blog setting assets:
1. Blog Main Image (image.png - 512x512)
2. Icon (icon.png - 64x64)
3. Favicon (favicon.ico - 32x32 multi-size ICO)
for all 5 blogs.
"""

import os
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "blog_settings_assets")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# System fonts fallback
FONT_CANDIDATES = [
    "C:/Windows/Fonts/malgunbd.ttf", # Malgun Gothic Bold
    "C:/Windows/Fonts/arialbd.ttf",
    "C:/Windows/Fonts/segoeui.ttf",
    "C:/Windows/Fonts/malgun.ttf"
]

def get_font(size):
    for f in FONT_CANDIDATES:
        if os.path.exists(f):
            try:
                return ImageFont.truetype(f, size)
            except Exception:
                continue
    return ImageFont.load_default()

BLOG_SPECS = [
    {
        "folder": "blog_1_smartwork_lab",
        "name": "Smart Work Lab",
        "short_title": "SMART",
        "sub_title": "WORK LAB",
        "icon_char": "⚡",
        "color1": (79, 70, 229),   # Indigo
        "color2": (6, 182, 212),   # Cyan
        "bg_dark": (11, 15, 25)
    },
    {
        "folder": "blog_2_money_roadmap_24",
        "name": "Money Roadmap 24",
        "short_title": "MONEY",
        "sub_title": "ROADMAP 24",
        "icon_char": "📈",
        "color1": (5, 150, 105),   # Emerald
        "color2": (16, 185, 129),  # Mint Green
        "bg_dark": (10, 16, 29)
    },
    {
        "folder": "blog_3_policy_finder_365",
        "name": "정책 알리미 365",
        "short_title": "정책",
        "sub_title": "알리미 365",
        "icon_char": "📢",
        "color1": (37, 99, 235),   # Royal Blue
        "color2": (245, 158, 11),  # Amber
        "bg_dark": (11, 17, 32)
    },
    {
        "folder": "blog_4_wellness_routine",
        "name": "웰니스 루틴 연구소",
        "short_title": "웰니스",
        "sub_title": "루틴 연구소",
        "icon_char": "🌿",
        "color1": (22, 163, 74),   # Forest Green
        "color2": (13, 148, 136),  # Sage Teal
        "bg_dark": (10, 20, 14)
    },
    {
        "folder": "blog_5_grow_mindset",
        "name": "Grow Mindset",
        "short_title": "GROW",
        "sub_title": "MINDSET",
        "icon_char": "🚀",
        "color1": (124, 58, 237),  # Royal Violet
        "color2": (245, 158, 11),  # Gold
        "bg_dark": (15, 10, 28)
    }
]

def draw_gradient_circle(draw, center, radius, color1, color2):
    cx, cy = center
    # Draw radial/concentric soft glow
    for r in range(radius, 0, -1):
        ratio = (radius - r) / radius
        r_col = int(color1[0] + (color2[0] - color1[0]) * ratio)
        g_col = int(color1[1] + (color2[1] - color1[1]) * ratio)
        b_col = int(color1[2] + (color2[2] - color1[2]) * ratio)
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(r_col, g_col, b_col))

def create_main_image(spec, out_path):
    size = 512
    img = Image.new("RGB", (size, size), spec["bg_dark"])
    draw = ImageDraw.Draw(img)

    # Gradient background sphere
    draw_gradient_circle(draw, (size // 2, size // 2), 220, spec["color1"], spec["color2"])

    # Subtle inner circle
    inner_r = 190
    draw.ellipse(
        [size // 2 - inner_r, size // 2 - inner_r, size // 2 + inner_r, size // 2 + inner_r],
        fill=spec["bg_dark"]
    )

    # Accent ring
    draw.ellipse(
        [size // 2 - 180, size // 2 - 180, size // 2 + 180, size // 2 + 180],
        outline=spec["color2"],
        width=4
    )

    # Text rendering
    font_main = get_font(60)
    font_sub = get_font(32)

    t1 = spec["short_title"]
    t2 = spec["sub_title"]

    bbox1 = draw.textbbox((0, 0), t1, font=font_main)
    w1, h1 = bbox1[2] - bbox1[0], bbox1[3] - bbox1[1]

    bbox2 = draw.textbbox((0, 0), t2, font=font_sub)
    w2, h2 = bbox2[2] - bbox2[0], bbox2[3] - bbox2[1]

    y_start = (size - (h1 + h2 + 20)) // 2

    # Draw Title 1
    draw.text(((size - w1) // 2, y_start - 10), t1, fill=(255, 255, 255), font=font_main)
    # Draw Title 2
    draw.text(((size - w2) // 2, y_start + h1 + 15), t2, fill=spec["color2"], font=font_sub)

    # Decorative dots
    draw.ellipse([size // 2 - 6, y_start - 35, size // 2 + 6, y_start - 23], fill=spec["color1"])

    img.save(out_path, "PNG", quality=95)

def create_icon_and_favicon(main_img_path, icon_path, favicon_path):
    with Image.open(main_img_path) as img:
        # 1. 64x64 Icon
        icon_img = img.resize((64, 64), Image.Resampling.LANCZOS)
        icon_img.save(icon_path, "PNG")

        # 2. Favicon .ico (32x32, 16x16)
        img_32 = img.resize((32, 32), Image.Resampling.LANCZOS)
        img_16 = img.resize((16, 16), Image.Resampling.LANCZOS)
        img_32.save(favicon_path, format="ICO", sizes=[(32, 32), (16, 16)])

def main():
    for spec in BLOG_SPECS:
        blog_dir = os.path.join(OUTPUT_DIR, spec["folder"])
        os.makedirs(blog_dir, exist_ok=True)

        main_img = os.path.join(blog_dir, "image.png")
        icon_img = os.path.join(blog_dir, "icon.png")
        fav_ico = os.path.join(blog_dir, "favicon.ico")

        print(f"Generating assets for {spec['name']}...")
        create_main_image(spec, main_img)
        create_icon_and_favicon(main_img, icon_img, fav_ico)
        print(f"  -> Saved in: {blog_dir}")

    print("\nAll blog assets successfully generated!")

if __name__ == "__main__":
    main()
