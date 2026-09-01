"""
High-Quality High-CTR Preset Thumbnail Batch Generator
Downloads and processes 30 diverse, visually captivating high-res images (1200x800)
for each of the 5 blog theme categories from curated photographic sources.
"""

import os
import time
import urllib.request
import urllib.parse
from PIL import Image, ImageEnhance, ImageFilter

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
THUMBS_DIR = os.path.join(BASE_DIR, "assets", "preset_thumbnails")

CATEGORIES = {
    "it_tech": {
        "start_idx": 32,
        "queries": [
            "artificial intelligence futuristic glowing brain technology",
            "sleek minimalist macbook desk setup aesthetic modern workspace",
            "cyberpunk neon matrix code programming monitor glowing blue",
            "smart home automation iot tablet control modern interior",
            "high tech futuristic robot hand touching human finger",
            "dual monitor coder desk mechanical keyboard rgb lighting",
            "smartwatch on wrist tracking fitness modern minimalist",
            "server room data center blue led fiber optics futuristic",
            "virtual reality vr headset user looking into metaverse",
            "modern ultra thin foldable smartphone floating dark background",
            "quantum computing motherboard microchip circuit macro shot",
            "wireless noise cancelling headphones premium audio desk aesthetic",
            "cloud computing data network abstract connected globe",
            "sleek futuristic electric car dashboard cockpit digital display",
            "clean white apple workspace with ipad pro and magic keyboard",
            "cyber security padlock digital binary code green glow",
            "drone camera flying over modern smart city sunset",
            "developer typing on keyboard code terminal close up",
            "ai chatbot neural network glowing particles visualization",
            "modern clean tech startup office glass meeting room",
            "portable ssd drive and sleek gadget accessories flatlay",
            "augmented reality glasses on wooden desk minimalist",
            "high tech gaming setup ultrawide monitor dark neon",
            "digital nomad working on laptop by ocean view balcony",
            "3d holographic interface floating in dark tech laboratory",
            "modern sleek laptop glowing apple logo on luxury marble",
            "robotic automation arm precision engineering factory",
            "deep learning big data visualization glowing nodes",
            "ultralight carbon fiber laptop in business lounge",
            "smart wearable ring health tracker sleek black background"
        ]
    },
    "finance_money": {
        "start_idx": 32,
        "queries": [
            "stack of gold coins and premium black credit card dark aesthetic",
            "stock market trading candlestick chart green profit graph",
            "leather luxury wallet with crisp dollar banknotes table",
            "modern banking vault door titanium steel gold bars",
            "smartphone screen showing stock portfolio investment growth",
            "calculator pen and financial compound interest chart",
            "real estate house model keys on contract document desk",
            "global currency exchange rate display terminal glowing numbers",
            "young investor analyzing candlestick charts on tablet coffee shop",
            "piggy bank with gold coins saving money compounding concept",
            "dividend income stock chart growth trend arrows up",
            "tax return financial documents with fountain pen and glasses",
            "etf fund portfolio investment balance sheet ledger",
            "luxury fountain pen signing contract on mahogany wood",
            "pile of clean money bills with soft studio lighting",
            "bull and bear stock market sculpture bronze table",
            "cryptocurrency bitcoin physical coin on dark reflective glass",
            "financial freedom retirement savings jar with green plant sprout",
            "luxury office desk view with laptop stock chart skyline background",
            "credit card payment terminal contactless payment close up",
            "emergency fund savings cash envelope budgeting method",
            "macro shot of golden coins reflecting warm ambient light",
            "family budget planning notebook with coffee and laptop",
            "interest rate bond yield curve chart glowing display",
            "wealth management investment report pie chart analytics",
            "financial advisor hand giving keys to happy client",
            "stack of hundred dollar bills tied with ribbon",
            "digital fintech banking app interface on modern smartphone",
            "golden padlock on money stack financial asset protection",
            "compound interest growth curve rising step graph"
        ]
    },
    "policy_life": {
        "start_idx": 31,
        "queries": [
            "modern apartment building architecture blue sky housing dream",
            "korean public transportation subway train modern platform",
            "family hands holding wooden miniature house home security",
            "government digital citizen certificate on tablet desk",
            "clean organized home utility energy saving smart meter",
            "vocational training student learning skills in modern lab",
            "happy young couple receiving apartment keys moving in",
            "official government stamp on application document seal",
            "clean hospital medical checkup clinic modern interior",
            "senior welfare activity center senior hands crafting",
            "youth employment job fair consultation booth career",
            "public transit bus card tap payment reader close up",
            "energy efficient solar panels on modern eco home roof",
            "korean won banknote support voucher envelope clean flatlay",
            "community garden citizen eco welfare park sunlight",
            "student studying in bright public library national scholarship",
            "childcare nursery daycare bright playground toys safety",
            "startup incubation center government subsidized office",
            "home improvement interior renovation tools clean floor",
            "emergency disaster relief kit and safety guide organized",
            "legal counseling law books scale of justice wood desk",
            "green electric vehicle charging station city street",
            "citizen voting ballot box democracy civic duty concept",
            "small business owner coffee shop open sign cheerful",
            "national pension saving growth piggy bank coins sprout",
            "vocational certification diploma degree certificate frame",
            "smart city high speed train station sunset architecture",
            "household grocery shopping receipt budget saving healthy food",
            "warm elderly caregiver holding hands empathy welfare",
            "korean public service center civil service digital kiosk"
        ]
    },
    "wellness_health": {
        "start_idx": 32,
        "queries": [
            "morning sunrise yoga stretch woman on mountain peak calm",
            "organic fresh colorful salad bowl avocado quinoa healthy meal",
            "minimalist home workout kettlebell yoga mat dumbbells bright room",
            "soothing lavender essential oil diffuser warm bedroom relaxation",
            "daily vitamin supplement pills in modern transparent dispenser",
            "running shoes and water bottle on morning jogging park track",
            "fresh green detox smoothie in glass jar with straw mint leaf",
            "peaceful meditation zen stone stack water ripples calm",
            "healthy breakfast oatmeal berries nuts yogurt clean bowl",
            "sound sleep white linen bed pillows morning soft sunlight",
            "pilates reformer workout studio instructor elegant posture",
            "fresh raw fruits and vegetables flatlay organic market",
            "smart fitness tracker watch showing heart rate calories",
            "hot herbal chamomile tea cup with honey lemon steaming",
            "massage spa wellness therapy bamboo stones warm towel",
            "intermittent fasting digital clock healthy food timing concept",
            "cold plunge ice bath recovery athlete focused breath",
            "hydration concept pouring clear water with lemon slice glass",
            "cycling bike on scenic forest road morning light fitness",
            "posture correction stretching foam roller back relief",
            "matcha green tea powder whisk ceramic bowl traditional",
            "outdoor trail hiking backpacker walking in lush pine forest",
            "clean skincare routine bottles on white marble bathroom",
            "swimming pool clean blue water lane exercise wellness",
            "deep breathing meditation candle flame dark relaxing room",
            "healthy gut probiotic kombucha drink bottle glass",
            "stretching hands to toes flexibility morning exercise",
            "aromatherapy candles bath salts relaxing tub warm water",
            "mental health journal book open with coffee and plant",
            "golden turmeric latte milk drink in ceramic mug cozy"
        ]
    },
    "growth_career": {
        "start_idx": 31,
        "queries": [
            "professional business meeting laptop whiteboard strategy plan",
            "premium leather daily planner journal with fountain pen coffee",
            "warm cozy reading nook bookshelf stacked literature library",
            "early morning 5am productivity coffee cup sunrise window view",
            "mind map goal setting board colorful sticky notes roadmap",
            "leaving office on time sunset city skyline glass window",
            "ted talk speaker on stage spotlight confidence presentation",
            "pomodoro timer desk productivity focus clock 25 minutes",
            "executive signing promotion contract document fountain pen",
            "mindset psychology book open with bookmark spectacles desk",
            "creative brainstorming sticky notes design sprint workshop",
            "growth mindset versus fixed mindset brain tree metaphor",
            "clean minimalist home office desk dual screens plant",
            "modern leadership teamwork high five in startup meeting",
            "resume cv portfolio review with hiring manager coffee",
            "deep work headphones on laptop keyboard focus flow state",
            "habit tracker checklist notebook filled with checkmarks",
            "climbing stairs success milestone steps to the top sunset",
            "public speaking podium microphone auditorium stage confidence",
            "daily gratitude journal writing hand with tea cup warm light",
            "networking business card exchange conference handshake",
            "chess board king piece strategic move checkmate leadership",
            "time blocking calendar schedule weekly planner color coded",
            "coffee beans grinder manual brew v60 morning ritual focus",
            "inspirational quote typewriter page vintage wooden desk",
            "standing desk ergonomic workspace dual monitor modern office",
            "marathon runner crossing finish line achievement celebration",
            "mindfulness breathing desk plant sunlight productivity",
            "financial ledger balance scale career progression graph",
            "high performance mentor coaching one on one discussion"
        ]
    }
}

def download_and_process_image(query: str, target_path: str) -> bool:
    """Download curated photo via Pollinations / Unsplash redirect and process with PIL."""
    encoded = urllib.parse.quote(query)
    # Using reliable high-speed high-quality seed image generator
    url = f"https://image.pollinations.ai/prompt/{encoded}%20photorealistic%20cinematic%208k%20depth%20of%20field?width=1200&height=800&nologo=true&seed={random.randint(1000, 999999)}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }

    tmp_path = target_path + ".tmp"
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as resp, open(tmp_path, "wb") as out_file:
            out_file.write(resp.read())

        # Open and enhance image with Pillow
        with Image.open(tmp_path) as img:
            img = img.convert("RGB")
            # Resize / crop to exact 1200x800
            target_w, target_h = 1200, 800
            img_w, img_h = img.size

            # Aspect ratio crop
            target_ratio = target_w / target_h
            img_ratio = img_w / img_h

            if img_ratio > target_ratio:
                # Wider: crop sides
                new_w = int(img_h * target_ratio)
                left = (img_w - new_w) // 2
                img = img.crop((left, 0, left + new_w, img_h))
            else:
                # Taller: crop top/bottom
                new_h = int(img_w / target_ratio)
                top = (img_h - new_h) // 2
                img = img.crop((0, top, img_w, top + new_h))

            img = img.resize((target_w, target_h), Image.Resampling.LANCZOS)

            # Slight color & contrast enhancement for punchy high-CTR thumbnails
            enhancer = ImageEnhance.Color(img)
            img = enhancer.enhance(1.08)
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.05)

            # Save as optimized JPEG
            img.save(target_path, "JPEG", quality=88, optimize=True)

        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        return True

    except Exception as e:
        print(f"  ❌ Error downloading [{query}]: {e}")
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        return False

def main():
    import random
    print("=== Starting High-CTR Preset Thumbnail Batch Generation (30 per blog) ===\n")
    total_generated = 0

    for cat_name, cat_info in CATEGORIES.items():
        cat_dir = os.path.join(THUMBS_DIR, cat_name)
        os.makedirs(cat_dir, exist_ok=True)
        start_idx = cat_info["start_idx"]
        queries = cat_info["queries"]

        print(f"\n📂 Processing category [{cat_name}] (Starting index: {start_idx}, Total: {len(queries)} images)...")
        cat_success = 0

        for i, query in enumerate(queries):
            file_num = start_idx + i
            target_filename = f"thumb_{file_num:02d}.jpg"
            target_path = os.path.join(cat_dir, target_filename)

            print(f"  [{i+1}/{len(queries)}] Generating {target_filename} for query: '{query[:40]}...'")
            success = download_and_process_image(query, target_path)
            if success:
                cat_success += 1
                total_generated += 1
                print(f"     ✅ Saved: {target_filename} ({os.path.getsize(target_path) // 1024} KB)")
            else:
                print(f"     ⚠️ Retrying with alternative seed...")
                time.sleep(1)
                retry_success = download_and_process_image(query + " high quality photo", target_path)
                if retry_success:
                    cat_success += 1
                    total_generated += 1
                    print(f"     ✅ Retry Saved: {target_filename}")

            time.sleep(0.5)

        print(f"🎉 [{cat_name}] Completed! {cat_success}/{len(queries)} thumbnails generated.")

    print(f"\n==========================================")
    print(f"🌟 ALL DONE! Total {total_generated} high-res thumbnails generated.")
    print(f"==========================================")

if __name__ == "__main__":
    import random
    main()
