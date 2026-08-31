"""
Gemini API Client for Content and Image Generation
"""

import os
import json
import re
import logging
from typing import Dict, Any, List, Optional
from google import genai
from google.genai import types

from config.prompts import TOPIC_DISCOVERY_PROMPT, ARTICLE_GENERATION_PROMPT

logger = logging.getLogger(__name__)

class GeminiClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self.client = None
        if self.api_key and self.api_key != "your_actual_gemini_api_key":
            try:
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini Client with provided key: {e}")

    def _ensure_client(self):
        if not self.client:
            self.api_key = os.environ.get("GEMINI_API_KEY")
            if not self.api_key or self.api_key == "your_actual_gemini_api_key":
                raise ValueError("GEMINI_API_KEY가 설정되지 않았습니다. .env 파일에 유효한 API 키를 입력해주세요.")
            self.client = genai.Client(api_key=self.api_key)

    def _clean_json_text(self, text: str) -> str:
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        return text.strip()

    def discover_topic(
        self,
        blog_name: str,
        theme_name: str,
        keywords: List[str],
        previous_topics: List[str],
        trend_keywords: Optional[List[str]] = None,
        model: str = "gemini-3.6-flash"
    ) -> Dict[str, Any]:
        """Select a fresh, high-CTR long-tail topic combining static and real-time trends."""
        self._ensure_client()
        prev_topics_str = "\n".join(previous_topics) if previous_topics else "(이전 포스팅 이력 없음)"
        trends_str = ", ".join(trend_keywords) if trend_keywords else "(실시간 트렌드 정보 없음)"

        prompt = TOPIC_DISCOVERY_PROMPT.format(
            blog_name=blog_name,
            theme_name=theme_name,
            keywords=", ".join(keywords),
            trend_keywords=trends_str,
            previous_topics=prev_topics_str
        )

        try:
            response = self.client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.8
                )
            )
            raw_text = response.text or "{}"
            return json.loads(self._clean_json_text(raw_text))
        except Exception as e:
            logger.error(f"Error during topic discovery: {e}")
            import random
            selected_kw = random.choice(keywords) if keywords else "핵심 가이드"
            return {
                "keyword": selected_kw,
                "topic": f"{theme_name} 관련 {selected_kw} 상세 활용 및 꿀팁",
                "title_candidate": f"{selected_kw} 완벽 가이드: 꼭 알아야 할 핵심 혜택과 꿀팁"
            }

    def generate_article(
        self,
        theme_name: str,
        keyword: str,
        topic: str,
        model: str = "gemini-3.6-flash"
    ) -> Dict[str, Any]:
        """Generate a full SEO-optimized HTML article with FAQ and tags."""
        self._ensure_client()
        prompt = ARTICLE_GENERATION_PROMPT.format(
            theme_name=theme_name,
            keyword=keyword,
            topic=topic
        )

        try:
            response = self.client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.7
                )
            )
            raw_text = response.text or "{}"
            data = json.loads(self._clean_json_text(raw_text))
            
            content_html = data.get("content_html", "")
            content_html = content_html.replace(
                "<blockquote>", 
                "<blockquote style='border-left: 4px solid #3182ce; padding: 12px 16px; background-color: #f7fafc; margin: 16px 0; border-radius: 4px; color: #2d3748;'>"
            )
            content_html = content_html.replace(
                "<table>",
                "<table style='width:100%; border-collapse:collapse; margin: 16px 0; text-align:left;'>"
            )
            data["content_html"] = content_html
            return data
        except Exception as e:
            logger.error(f"Error generating article: {e}")
            raise

    def generate_image_visual(
        self,
        prompt: str,
        output_path: str,
        model: str = "imagen-3.0-generate-002"
    ) -> bool:
        """Generate an AI visual using Imagen 3."""
        self._ensure_client()
        try:
            logger.info(f"Generating Imagen 3 visual for prompt: {prompt[:60]}...")
            result = self.client.models.generate_images(
                model=model,
                prompt=prompt,
                config=types.GenerateImagesConfig(
                    number_of_images=1,
                    aspect_ratio="16:9",
                    output_mime_type="image/jpeg"
                )
            )
            if result.generated_images:
                image_bytes = result.generated_images[0].image.image_bytes
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                with open(output_path, "wb") as f:
                    f.write(image_bytes)
                logger.info(f"AI visual saved successfully to: {output_path}")
                return True
        except Exception as e:
            logger.warning(f"Imagen 3 generation notice: {e}. Will use elegant gradient fallback.")
            return False
        return False
