# 티스토리 다중 블로그 5채널 자동 포스팅 시스템

Gemini API(실시간 검색 결합 + SEO 전문 본문 + AI 썸네일)와 Playwright(카카오 세션 영구 유지 자동화 브라우저), APScheduler(24/7 예약 자동 발행)를 결합한 **완전 자동화 티스토리 블로그 운영 솔루션**입니다.

---

## 📁 주요 디렉터리 구조

```
tistory-auto-publisher/
├── config/
│   ├── config.yaml          # 5개 블로그 서브도메인, 10개 테마, 스케줄 설정
│   └── prompts.py           # SEO 최적화 및 주제 발굴용 전문 프롬프트
├── core/
│   ├── database.py          # SQLite DB 관리 (포스팅 이력, 중복 방지)
│   ├── gemini_client.py     # Gemini API 클라이언트 (주제발굴, 본문, 썸네일)
│   ├── thumbnail.py         # Pillow 기반 고화질 타이포그래피 썸네일 생성
│   ├── tistory_bot.py       # Playwright 기반 티스토리 자동 로그인/글쓰기 봇
│   ├── scheduler.py         # 5개 블로그 24시간 자동 발행 스케줄러
├── session_data/            # 브라우저 카카오 로그인 세션 저장소 (영구 유지)
├── generated/               # 생성된 썸네일 및 임시 이미지
├── scripts/
│   ├── setup_login.py       # [최초 1회] 카카오 로그인 세션 저장 스크립트
│   ├── test_post_single.py  # [테스트용] 특정 블로그 1회 즉시 포스팅 실행
│   └── run_scheduler.py     # [단독 실행] 5개 블로그 자동 스케줄러 단독 구동
├── .env                     # API 키 설정 (GEMINI_API_KEY)
├── app.py                   # FastAPI 웹 대시보드 및 즉시 발행 트리거 서버
└── requirements.txt
```

---

## 🚀 빠른 시작 가이드 (Quick Start)

### 1. API 키 설정 (.env)
프로젝트 루트 폴더에 `.env` 파일을 생성하고 발급받은 Gemini API 키를 입력합니다.
```env
GEMINI_API_KEY=AIzaSy...
```

### 2. 블로그 정보 설정 (config/config.yaml)
`config/config.yaml` 파일에서 본인이 운영 중인 5개 티스토리 블로그의 서브도메인을 입력합니다.
```yaml
blogs:
  - id: "blog_1"
    name: "IT & 테크 트렌드"
    subdomain: "본인_블로그1_서브도메인"  # https://xxxx.tistory.com 의 xxxx 부분
    themes:
      - name: "AI 및 생산성 도구 가이드"
      - name: "소프트웨어 및 IT 기기 리뷰/추천"
    schedule_times: ["07:00", "13:00", "19:00"]
```

### 3. [최초 1회 실행] 카카오 로그인 세션 저장
실제 티스토리 에디터에 자동으로 글을 올리기 위해 카카오 로그인을 1회 수행합니다.
```bash
python scripts/setup_login.py
```
> 브라우저가 열리면 카카오 로그인 후 콘솔에서 Enter를 누르면 `session_data/`에 세션 정보가 저장됩니다.

### 4. 웹 대시보드 및 서버 실행
```bash
python app.py
```
> 브라우저에서 `http://localhost:8000`으로 접속하여 실시간 트렌드 확인 및 즉시 포스팅을 테스트할 수 있습니다.
