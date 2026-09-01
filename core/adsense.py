"""
Google AdSense Strategic Integration Module
Automatically injects responsive Top, Mid-article, and Bottom Ad units to maximize CTR and revenue.
"""

import re
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class AdSenseManager:
    def __init__(self, pub_id: str = "ca-pub-9856782529784947", enabled: bool = True):
        # Format pub_id cleanly
        if pub_id and not pub_id.startswith("ca-"):
            pub_id = f"ca-{pub_id}"
        self.pub_id = pub_id or "ca-pub-9856782529784947"
        self.enabled = enabled

    def generate_ad_block(self, position: str = "top", slot_id: Optional[str] = None) -> str:
        """Generate high-CTR responsive AdSense unit HTML without inline script tags for clean editor UI."""
        if not self.enabled:
            return ""

        slot_attr = f'data-ad-slot="{slot_id}"' if slot_id else 'data-ad-format="auto"'
        
        ad_html = f"""
<!-- AdSense {position.upper()} Slot -->
<div class="adsense-container adsense-{position}" style="margin: 28px auto; text-align: center; max-width: 100%; min-height: 100px; display: flex; justify-content: center; align-items: center;">
  <ins class="adsbygoogle"
       style="display:block"
       data-ad-client="{self.pub_id}"
       {slot_attr}
       data-full-width-responsive="true"></ins>
</div>
"""
        return ad_html

    def inject_ads(self, html_content: str, slots: Optional[Dict[str, str]] = None) -> str:
        """
        Strategically inject Top, In-Article (Mid), and Bottom ads into blog post HTML.
        - Top Ad: Placed at the very top or after TOC.
        - Mid Ad: Placed naturally before the 2nd <h2> heading.
        - Bottom Ad: Placed right above summary / FAQ or at the bottom.
        """
        if not self.enabled or not self.pub_id:
            return html_content

        slots = slots or {}
        top_slot = slots.get("slot_top")
        mid_slot = slots.get("slot_mid")
        bottom_slot = slots.get("slot_bottom")

        top_ad = self.generate_ad_block("top", top_slot)
        mid_ad = self.generate_ad_block("mid", mid_slot)
        bottom_ad = self.generate_ad_block("bottom", bottom_slot)

        modified_html = html_content

        # 1. Inject Mid Ad before 2nd <h2> if exists, or before 3rd <p>
        h2_matches = list(re.finditer(r'<h2[^>]*>', modified_html, re.IGNORECASE))
        if len(h2_matches) >= 2:
            # Place right before the 2nd <h2>
            second_h2_pos = h2_matches[1].start()
            modified_html = modified_html[:second_h2_pos] + mid_ad + modified_html[second_h2_pos:]
        else:
            # Fallback: place around the middle of content
            p_matches = list(re.finditer(r'</p>', modified_html, re.IGNORECASE))
            if len(p_matches) >= 3:
                mid_p_pos = p_matches[len(p_matches) // 2].end()
                modified_html = modified_html[:mid_p_pos] + mid_ad + modified_html[mid_p_pos:]

        # 2. Inject Top Ad at the beginning of article body
        modified_html = top_ad + modified_html

        # 3. Inject Bottom Ad at the end of article body
        modified_html = modified_html + bottom_ad

        logger.info(f"Google AdSense 3단 광고(상단/중간/하단) 자동 주입 완료 (pub-id: {self.pub_id})")
        return modified_html
