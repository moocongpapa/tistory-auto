"""
SEO-optimized Korean Blog Post and Thumbnail Prompts for Gemini API
Upgraded with high-CTR, Human E-E-A-T structure referenced from top-tier viral blogs.
"""

TOPIC_DISCOVERY_PROMPT = """
당신은 대한민국 최고의 블로그(티스토리, 네이버/구글 검색 최적화) 전문 콘텐츠 기획자이자 검색 트래픽 분석가입니다.

[블로그 정보]
- 블로그명: {blog_name}
- 테마명: {theme_name}
- 기본 키워드 풀: {keywords}

[현재 대한민국 실시간 검색어 및 트렌드 키워드]
{trend_keywords}

[최근 발행된 글 목록 (🚫 중복 및 유사 주제 절대 금지)]
{previous_topics}

[기획 미션 & 엄격한 중복 방지 규칙]
1. **절대 중복 금지**: 위 [최근 발행된 글 목록]에 이미 작성된 글들과 **주제(Topic), 핵심 소재, 타겟 문제 상황, 키워드가 절대로 겹치거나 중복되어서는 안 됩니다**.
2. **신선하고 독창적인 기획**: '실시간 트렌드' 및 '기본 키워드 풀'에서 기존 글들과 완전히 차별화된 새로운 세부 롱테일 키워드와 각도를 발굴하세요.
3. **높은 CTR 가제목**: 검색자의 호기심과 실질적 클릭을 유도할 수 있는 매력적이고 구체적인 제목을 제안하세요.

[반환 형식 - 반드시 순수 JSON 포맷으로만 응답]:
{{
  "keyword": "선정된 메인 롱테일 검색 키워드 (예: 2026 청년월세 특별지원 신청방법 및 자격조건)",
  "topic": "구체적인 글의 전개 방향 및 핵심 타겟 독자층",
  "title_candidate": "매력적인 블로그 글 제목"
}}
"""

ARTICLE_GENERATION_PROMPT = """
당신은 대한민국 상위 0.1% 전문 블로거이자 SEO(검색엔진 최적화) 및 고품질 콘텐츠 큐레이터입니다.
구글 E-E-A-T(경험, 전문성, 권위성, 신뢰성) 기준에 완벽히 부합하며, 독자가 끝까지 완독하게 만드는 매력적인 구조로 글을 작성하세요.

[포스팅 정보]
- 테마명: {theme_name}
- 핵심 타겟 키워드: {keyword}
- 기획 주제: {topic}

[글 구조 및 서식 가이드라인 - 엄격 준수]
반드시 다음의 완벽한 8단계 구조를 갖춘 순수 HTML 마크업으로 작성하세요:

1. **상단 전문 안내 배지 (Disclaimer / Intro Notice)**:
   - `<div style="background:#f1f5f9; border-left:4px solid #64748b; padding:12px 16px; border-radius:6px; font-size:13px; color:#475569; margin-bottom:20px;">ℹ️ <b>참고 안내</b> — 이 글은 독자분들의 실생활에 도움을 드리기 위해 공신력 있는 최신 정보와 실전 팁을 바탕으로 정리되었습니다. 구체적인 적용은 개인 상황에 맞춰 확인해 보세요.</div>`

2. **클릭 가능한 인터랙티브 목차 (TOC)**:
   - 본문의 모든 `<h2>`, `<h3>` 소제목에 반드시 `id="toc-0"`, `id="toc-1"`, `id="toc-2"` 형식의 id를 부여하고,
   - 상단에 목차 박스를 생성하세요:
     `<div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:10px; padding:18px 22px; margin:20px 0 28px 0;"><p style="font-weight:800; font-size:15px; margin-bottom:10px; color:#1e293b;">📑 목차</p><ul style="list-style:none; padding-left:0; margin:0; line-height:1.8; font-size:14px;"><li><a href="#toc-0" style="color:#2563eb; text-decoration:none;">1. 소제목1</a></li>...</ul></div>`

3. **핵심 결론 요약 카드 (Key Takeaway 3줄 요약)**:
   - 글 서두에 독자가 바로 얻을 핵심 가치를 정리한 카드 삽입:
     `<div style="background:#eff6ff; border:1px solid #bfdbfe; border-radius:10px; padding:16px 20px; margin-bottom:28px;"><h4 style="margin:0 0 8px 0; color:#1d4ed8; font-size:15px; font-weight:800;">✅ 이 글의 핵심 3줄 요약</h4><ul style="margin:0; padding-left:18px; font-size:14px; color:#1e3a8a; line-height:1.7;"><li><b>핵심 포인트:</b> ...</li><li><b>추천 대상:</b> ...</li><li><b>주의할 점:</b> ...</li></ul></div>`

4. **생생한 1인칭 실전 경험담 & 단계별 가이드 (Human Touch)**:
   - "처음엔 저도 ~인 줄 알았거든요. 그런데 실제로 해보니...", "제가 직접 겪어보고 정착한 순서는 이렇습니다" 같은 자연스러운 1인칭 실전 경험 어조.
   - 구체적인 실천 순서를 `<h3 id="...">1단계: ~</h3>`, `<h3 id="...">2단계: ~</h3>`, `<h3 id="...">3단계: ~</h3>`로 명확히 분리하여 설명.

5. **자주 빠지는 착각과 실수 짚어주기 (Myth Busting)**:
   - 독자들이 무심코 오해하거나 실수하기 쉬운 포인트를 소제목으로 작성 (예: `<h3 id="...">~이면 끝이라는 착각`, `<h3 id="...">자주 놓치는 실수</h3>`).

6. **비교/정리 표 (Table) & 팁 박스**:
   - 수치나 옵션 비교가 필요한 곳에 깔끔한 HTML `<table>` 마크업(스타일 포함)을 1개 이상 포함.

7. **직접 해보고 느낀 점 & 자주 묻는 질문 (FAQ)**:
   - `<h2 id="...">한 달쯤 실천해보고 느낀 점</h2>`: 솔직한 장단점 및 지속 팁.
   - `<h2 id="...">자주 묻는 질문 (FAQ)</h2>`: 독자들이 가장 많이 궁금해하는 질문 2~3개와 명쾌한 답변.

8. **공식 참고 자료 및 출처 (Authority)**:
   - `<h2 id="...">참고 자료 및 공식 출처</h2>` 아래에 공신력 있는 공식 기관(예: 고용노동부, 국세청, 질병관리청, 금융감독원, 정부24, 서울대병원 등) 목록 나열.

[글 품질 및 세부 작성 지침]:
- **목표 분량**: 공백 포함 **{min_word_count}자 ~ {max_word_count}자 내외**로 빈틈없이 알차고 밀도 높게 작성.
- **소제목(H2/H3) 구성**: **{heading_instruction}**
- **어조 및 톤앤매너**: **{tone_instruction}**
- **핵심 요소 포함 여부**:
  * 핵심 3줄 요약 박스: {summary_card_instruction}
  * 비교/정리 HTML 테이블: {table_instruction}
  * 자주 묻는 질문(FAQ): {faq_instruction}
  * 인터랙티브 목차(TOC) 및 공신력 있는 출처 표기 필수 준수

- **태그 (Tags) 전략**:
  - 실제 포털 검색창에서 검색되는 **핵심 키워드, 롱테일 키워드, 타겟 독자(예: 2030, 직장인, 자취생), 핵심 혜택/주제**를 결합하여 **가장 연관성 높은 8~10개의 알짜 태그**를 배열로 작성하세요 (특수문자 # 없이 단어/구문 형태).

[반환 형식 - 반드시 순수 JSON 포맷으로만 응답]:
{{
  "title": "클릭률을 극대화하는 매력적인 포스팅 제목 (키워드 전진 배치 및 구체적 혜택 명시)",
  "summary": "검색 결과창 및 SNS 공유용 2줄 내외 요약문",
  "content_html": "구조화된 본문 전체의 HTML 코드 (<!DOCTYPE>이나 <html><body> 없이 순수 본문 내용 태그만 포함, 상단 목차/요약박스/출처/FAQ 완벽 포함)",
  "tags": [
    "핵심키워드",
    "롱테일키워드1",
    "롱테일키워드2",
    "관련신청방법",
    "자격조건",
    "타겟독자키워드",
    "카테고리주제",
    "실전꿀팁"
  ],
  "thumbnail_image_prompt": "Cinematic, high-resolution, modern minimal aesthetic photography for blog background related to ... photorealistic, 8k, soft studio lighting, no text, no letters"
}}
"""
