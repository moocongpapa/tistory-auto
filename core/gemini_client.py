"""
Gemini API Client with Automatic Fallback and Quota Error (429) Handling
"""

import os
import json
import time
import logging
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

from config.prompts import TOPIC_DISCOVERY_PROMPT, ARTICLE_GENERATION_PROMPT

logger = logging.getLogger(__name__)

# Fallback model list in order of priority (3.7 -> 3.5 -> 3.5-lite -> 2.5)
FALLBACK_TEXT_MODELS = [
    "gemini-3.7-flash",
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-2.5-flash",
]

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

    def _extract_and_parse_json(self, text: str) -> Dict[str, Any]:
        """Robustly extract and parse JSON even if Gemini outputs extra text or markdown wrappers."""
        if not text:
            return {}

        cleaned = text.strip()
        # Remove Markdown wrappers if present
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        # 1. First attempt: Direct json.loads with strict=False
        try:
            return json.loads(cleaned, strict=False)
        except Exception:
            pass

        # 2. Second attempt: Extract outermost { ... }
        start_idx = cleaned.find("{")
        end_idx = cleaned.rfind("}")
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            candidate = cleaned[start_idx:end_idx + 1]
            try:
                return json.loads(candidate, strict=False)
            except Exception:
                pass

        # 3. Third attempt: JSONDecoder with strict=False to ignore trailing extra data
        try:
            if start_idx != -1:
                decoder = json.JSONDecoder(strict=False)
                obj, _ = decoder.raw_decode(cleaned[start_idx:])
                if isinstance(obj, dict):
                    return obj
        except Exception as e:
            logger.debug(f"JSON raw_decode parsing failed: {e}")

        # 4. Fourth attempt: Regex extraction fallback for key fields (title, summary, content_html, tags)
        try:
            import re
            extracted = {}
            title_m = re.search(r'"title"\s*:\s*"([^"\\]*(?:\\.[^"\\]*)*)"', cleaned)
            if title_m:
                extracted["title"] = title_m.group(1).replace('\\"', '"').replace('\\n', ' ')

            summary_m = re.search(r'"summary"\s*:\s*"([^"\\]*(?:\\.[^"\\]*)*)"', cleaned)
            if summary_m:
                extracted["summary"] = summary_m.group(1).replace('\\"', '"')

            content_m = re.search(r'"content_html"\s*:\s*"([\s\S]*?)"\s*,\s*"tags"', cleaned)
            if content_m:
                extracted["content_html"] = content_m.group(1).replace('\\"', '"').replace('\\n', '\n')

            tags_m = re.search(r'"tags"\s*:\s*\[(.*?)\]', cleaned, re.DOTALL)
            if tags_m:
                raw_tags = tags_m.group(1)
                extracted["tags"] = [t.strip().strip('"').strip("'") for t in raw_tags.split(",") if t.strip()]

            if extracted.get("title") and (extracted.get("content_html") or extracted.get("summary")):
                logger.info("정규식 폴백 파서로 JSON 주요 필드 안전 복구 성공!")
                return extracted
        except Exception as e:
            logger.debug(f"Regex JSON fallback failed: {e}")

        # 5. Fallback if everything fails
        logger.error(f"Failed to parse JSON from AI response: {cleaned[:200]}...")
        raise ValueError(f"AI 응답에서 유효한 JSON을 파싱할 수 없습니다: {cleaned[:100]}")

    def _call_with_fallback(self, prompt: str, initial_model: str, temperature: float = 0.7) -> str:
        """Call Gemini API with auto-fallback to alternative models upon 429 Quota Exceeded."""
        self._ensure_client()
        models_to_try = [initial_model] + [m for m in FALLBACK_TEXT_MODELS if m != initial_model]

        last_error = None
        for model_name in models_to_try:
            try:
                logger.info(f"Gemini API 호출 시도 중 (모델: {model_name})...")
                response = self.client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        temperature=temperature
                    )
                )
                if response and response.text:
                    return response.text
            except Exception as e:
                err_msg = str(e)
                last_error = e
                if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg or "Quota exceeded" in err_msg:
                    logger.warning(f"모델 [{model_name}] 429 쿼터 초과 발생. 다음 폴백 모델로 자동 전환합니다...")
                    time.sleep(1)
                    continue
                else:
                    logger.error(f"모델 [{model_name}] 호출 중 예외 발생: {e}")
                    time.sleep(1)
                    continue

        raise RuntimeError(f"모든 Gemini 모델 호출 실패. 마지막 에러: {last_error}")

    def discover_topic(
        self,
        blog_name: str,
        theme_name: str,
        keywords: List[str],
        previous_topics: List[str],
        trend_keywords: Optional[List[str]] = None,
        model: str = "gemini-3.5-flash"
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
            raw_text = self._call_with_fallback(prompt, initial_model=model, temperature=0.8)
            return self._extract_and_parse_json(raw_text)
        except Exception as e:
            logger.error(f"주제 발굴 중 오류 발생, 기본 대체 주제 생성: {e}")
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
        model: str = "gemini-3.5-flash",
        quality_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate a full SEO-optimized HTML article with configurable quality options."""
        self._ensure_client()
        
        # Parse quality options with sensible defaults
        qc = quality_config or {}
        min_words = qc.get("min_word_count", 2500)
        max_words = qc.get("max_word_count", 3500)
        
        heading_type = qc.get("heading_count", "4_5")
        if heading_type == "3":
            heading_instruction = "핵심 3대 핵심 소제목(H2) 위주로 간결하고 임팩트 있게 구성"
        elif heading_type == "6_plus":
            heading_instruction = "6개 이상의 세부 소제목(H2/H3)을 통해 기초부터 심화, FAQ까지 완벽히 총망라하는 백과사전식 심층 구성"
        else:
            heading_instruction = "4~5개의 균형 잡힌 본문 소제목(H2) 및 하위 단계별(H3) 실천 가이드로 체계적 구성"

        tone_type = qc.get("tone_style", "friendly_expert")
        if tone_type == "professional":
            tone_instruction = "신뢰도 높은 전문 연구원/공인 전문가 어조 (~입니다, ~바랍니다, ~것을 권장합니다)"
        elif tone_type == "storytelling":
            tone_instruction = "몰입감 높은 1인칭 경험 및 인사이트 공유형 어조 (~했더니, ~느꼈습니다, 생생한 실전 사례)"
        else:
            tone_instruction = "친근하면서도 전문적인 실전 멘토 어조 (~해요, ~합니다, ~해보세요)"

        summary_card_instruction = "글 서두에 필수 포함 (3줄 핵심 요약 카드)" if qc.get("add_summary_card", True) else "생략 가능"
        table_instruction = "본문 중간에 수치/옵션 비교 HTML table 반드시 1개 이상 포함" if qc.get("add_table", True) else "필요 시 선택적 포함"
        faq_instruction = "본문 하단에 독자 주요 질문 FAQ 2~3개 및 명쾌한 답변 섹션 필수 포함" if qc.get("add_faq", True) else "선택적 포함"

        prompt = ARTICLE_GENERATION_PROMPT.format(
            theme_name=theme_name,
            keyword=keyword,
            topic=topic,
            min_word_count=min_words,
            max_word_count=max_words,
            heading_instruction=heading_instruction,
            tone_instruction=tone_instruction,
            summary_card_instruction=summary_card_instruction,
            table_instruction=table_instruction,
            faq_instruction=faq_instruction
        )

        try:
            raw_text = self._call_with_fallback(prompt, initial_model=model, temperature=0.7)
            data = self._extract_and_parse_json(raw_text)
            
            content_html = data.get("content_html", "")
            content_html = content_html.replace(
                "<blockquote>", 
                "<blockquote style='border-left: 4px solid #1d4ed8; padding: 14px 18px; background-color: #eff6ff; margin: 18px 0; border-radius: 6px; color: #1e3a8a;'>"
            )
            content_html = content_html.replace(
                "<table>",
                "<table style='width:100%; border-collapse:collapse; margin: 18px 0; text-align:left; border:1px solid #e2e8f0;'>"
            )
            data["content_html"] = content_html
            return data
        except Exception as e:
            logger.error(f"본문 생성 중 에러 발생: {e}")
            raise

    def generate_image_visual(
        self,
        prompt: str,
        output_path: str,
        model: str = "imagen-3.0-generate-002"
    ) -> bool:
        """Generate an AI visual using Imagen 3 with graceful fallback."""
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
            logger.warning(f"Imagen 3 이미지 생성 알림: {e}. 타이포그래피 그래픽 썸네일로 자동 전환합니다.")
            return False
        return False
