"""
FastAPI Web Dashboard and REST API Server for Tistory Multi-Blog Publisher
"""

import os
import sys
import yaml
import asyncio
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Form, Response
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from dotenv import load_dotenv

# Ensure root dir is in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

load_dotenv()

# Setup logging
os.makedirs(os.path.join(BASE_DIR, "data"), exist_ok=True)
log_file = os.path.join(BASE_DIR, "data", "scheduler.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] (%(name)s) %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_file, encoding="utf-8")
    ]
)
logger = logging.getLogger("web_server")

import secrets
import base64
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from core.database import DatabaseManager
from core.scheduler import MultiBlogScheduler
from core.trend_collector import TrendCollector
from core.session_manager import session_manager

CONFIG_PATH = os.path.join(BASE_DIR, "config", "config.yaml")

# Global singletons
db = DatabaseManager()
scheduler_runner = MultiBlogScheduler(use_background=True)
trend_collector = TrendCollector()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("FastAPI 시작: 영구 설정 복원 및 백그라운드 스케줄러 가동...")
    try:
        # 1. Restore AI Model
        saved_model = db.get_setting("ai_model")
        if saved_model:
            scheduler_runner.config.setdefault("ai", {})["text_model"] = saved_model
            logger.info(f"💾 [영구복원] AI 모델 복원: {saved_model}")

        # 2. Restore Quality Config
        saved_qc = db.get_setting("quality_config")
        if saved_qc:
            qc_dict = json.loads(saved_qc)
            scheduler_runner.config.setdefault("publishing", {}).update(qc_dict)
            logger.info("💾 [영구복원] 글 품질 설정 복원 완료")

        # 3. Restore Daily Schedule Count
        saved_count = db.get_setting("daily_post_count")
        if saved_count and saved_count.isdigit():
            count = int(saved_count)
            scheduler_runner.update_daily_post_count(count)
            logger.info(f"💾 [영구복원] 일일 발행 스케줄 복원 ({count}회)")
    except Exception as e:
        logger.warning(f"영구 설정 복원 중 참고: {e}")

    scheduler_runner.start()
    yield
    logger.info("FastAPI 종료")

app = FastAPI(title="Tistory Multi-Blog Publisher Dashboard", lifespan=lifespan)

import hashlib

# Security: Hybrid Cookie + Basic Auth Middleware for seamless Mobile PWA and Browser access
class DashboardAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        username = os.environ.get("DASHBOARD_USERNAME", "admin")
        password = os.environ.get("DASHBOARD_PASSWORD", "").strip()

        # Whitelist public routes (Render keep-alive ping, PWA icons & manifest, login page, and static assets)
        path = request.url.path
        if path in [
            "/api/health", "/ping", "/favicon.ico", "/manifest.json", "/sw.js", 
            "/apple-touch-icon.png", "/apple-touch-icon-precomposed.png", "/login", "/logout"
        ] or path.startswith("/static") or path.startswith("/assets"):
            return await call_next(request)

        # If DASHBOARD_PASSWORD is configured, require authentication
        if password:
            expected_token = hashlib.sha256(f"{username}:{password}".encode("utf-8")).hexdigest()
            cookie_token = request.cookies.get("session_auth", "")

            # 1. Check Cookie Session (Mobile PWA & Browser)
            if cookie_token and secrets.compare_digest(cookie_token, expected_token):
                return await call_next(request)

            # 2. Check HTTP Basic Auth Header (API calls / curl)
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Basic "):
                try:
                    encoded_creds = auth_header.split(" ", 1)[1]
                    decoded = base64.b64decode(encoded_creds).decode("utf-8")
                    req_user, req_pass = decoded.split(":", 1)
                    if secrets.compare_digest(req_user, username) and secrets.compare_digest(req_pass, password):
                        return await call_next(request)
                except Exception:
                    pass

            # 3. Not authenticated -> Redirect to /login for web/PWA or 401 for API
            if path.startswith("/api/"):
                return Response(
                    content="Unauthorized: Access to Tistory AI Publisher is protected.",
                    status_code=401,
                    headers={"WWW-Authenticate": 'Basic realm="Tistory Publisher Dashboard"'}
                )
            else:
                return RedirectResponse(url="/login", status_code=302)

        return await call_next(request)

app.add_middleware(DashboardAuthMiddleware)

# Static and Templates
THUMBNAILS_DIR = os.path.join(BASE_DIR, "generated", "thumbnails")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
os.makedirs(THUMBNAILS_DIR, exist_ok=True)
os.makedirs(ASSETS_DIR, exist_ok=True)

app.mount("/assets", StaticFiles(directory=ASSETS_DIR), name="assets")
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "web", "templates"))

# PWA Static Routes
@app.get("/manifest.json")
async def get_manifest():
    return FileResponse(os.path.join(BASE_DIR, "static", "manifest.json"), media_type="application/manifest+json")

@app.get("/sw.js")
async def get_service_worker():
    return FileResponse(os.path.join(BASE_DIR, "static", "sw.js"), media_type="application/javascript")

@app.get("/apple-touch-icon.png")
@app.get("/apple-touch-icon-precomposed.png")
@app.get("/favicon.ico")
async def get_apple_touch_icon():
    return FileResponse(os.path.join(BASE_DIR, "static", "apple-touch-icon.png"), media_type="image/png")

# Authentication Routes (HTML Form + 30-Day Persistent Cookie for Mobile PWA)
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(request=request, name="login.html", context={"request": request, "error": None})

@app.post("/login", response_class=HTMLResponse)
async def process_login(request: Request, username: str = Form("admin"), password: str = Form("")):
    expected_user = os.environ.get("DASHBOARD_USERNAME", "admin")
    expected_pass = os.environ.get("DASHBOARD_PASSWORD", "").strip()

    is_user_valid = secrets.compare_digest(username, expected_user)
    is_pass_valid = secrets.compare_digest(password, expected_pass)

    if is_user_valid and is_pass_valid:
        token = hashlib.sha256(f"{expected_user}:{expected_pass}".encode("utf-8")).hexdigest()
        response = RedirectResponse(url="/", status_code=302)
        response.set_cookie(
            key="session_auth",
            value=token,
            max_age=30 * 86400,  # 30 days
            httponly=True,
            samesite="lax"
        )
        return response

    return templates.TemplateResponse(
        request=request, 
        name="login.html", 
        context={"request": request, "error": "사용자 이름 또는 비밀번호가 올바르지 않습니다."}
    )

@app.get("/logout")
async def process_logout():
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie("session_auth")
    return response

@app.get("/api/latest-post-event")
async def get_latest_post_event(last_id: int = 0):
    """Returns the newest published post if newer than last_id for PWA real-time push notification."""
    latest_posts = db.get_all_posts(limit=1)
    if not latest_posts:
        return {"has_new": False}
    
    newest = dict(latest_posts[0])
    curr_id = newest.get("id", 0)
    if curr_id > last_id:
        blogs = scheduler_runner.config.get("blogs", [])
        blogs_map = {b["id"]: b for b in blogs}
        b_info = blogs_map.get(newest.get("blog_id"), {})
        
        return {
            "has_new": True,
            "post": {
                "id": curr_id,
                "title": newest.get("title", ""),
                "blog_name": b_info.get("name", newest.get("blog_id")),
                "theme": newest.get("theme", ""),
                "url": newest.get("post_url") or f"https://{b_info.get('subdomain', '')}.tistory.com",
                "thumbnail_path": newest.get("thumbnail_path", ""),
                "published_at": newest.get("created_at", "")
            }
        }
    return {"has_new": False}

class TriggerPostRequest(BaseModel):
    blog_id: str = "blog_1"
    is_draft: bool = False

class UpdateModelRequest(BaseModel):
    model_name: str

@app.api_route("/", methods=["GET", "HEAD"], response_class=HTMLResponse)
async def dashboard_home(request: Request):
    stats = db.get_dashboard_stats()
    posts = db.get_all_posts(limit=200)
    blogs = scheduler_runner.config.get("blogs", [])
    trends = trend_collector.get_realtime_trends(limit=12)
    scheduled_jobs = scheduler_runner.get_scheduled_jobs_info()
    current_model = scheduler_runner.config.get("ai", {}).get("text_model", "gemini-3.5-flash")

    # Map blogs by ID for instant lookup
    blogs_map = {b["id"]: b for b in blogs}
    enriched_posts = []
    for p in posts:
        p_dict = dict(p)
        b_info = blogs_map.get(p_dict.get("blog_id"), {})
        p_dict["blog_name"] = b_info.get("name", p_dict.get("blog_id"))
        p_dict["blog_subdomain"] = b_info.get("subdomain", "")
        p_dict["blog_language"] = b_info.get("language", "ko")
        enriched_posts.append(p_dict)

    # Read last 20 log lines
    logs = []
    if os.path.exists(log_file):
        try:
            with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
                logs = [line.strip() for line in f.readlines()[-20:]]
        except Exception as e:
            logs = [f"Log reading note: {e}"]

    quality_config = scheduler_runner.config.get("publishing", {})
    daily_post_count = scheduler_runner.get_daily_post_count()
    activities = db.get_recent_activities(limit=30)
    session_info = session_manager.get_session_info()

    context = {
        "request": request,
        "stats": stats,
        "posts": enriched_posts,
        "blogs": blogs,
        "blogs_map": blogs_map,
        "trends": trends,
        "scheduled_jobs": scheduled_jobs,
        "current_model": current_model,
        "quality_config": quality_config,
        "daily_post_count": daily_post_count,
        "activities": activities,
        "logs": logs,
        "session_info": session_info
    }

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context=context
    )

@app.get("/api/activities")
async def get_activities_api(limit: int = 30):
    return {"activities": db.get_recent_activities(limit=limit)}

class DirectLoginRequest(BaseModel):
    email: str
    password: str

class ImportSessionRequest(BaseModel):
    session_json: str

@app.get("/api/session/status")
async def get_session_status():
    return session_manager.get_session_info()

@app.post("/api/session/qr/start")
async def start_qr_session():
    return await asyncio.to_thread(session_manager.start_qr_session)

@app.get("/api/session/qr/check")
async def check_qr_session(session_id: str):
    return await asyncio.to_thread(session_manager.poll_qr_session, session_id)

@app.post("/api/session/login")
async def direct_login_api(req: DirectLoginRequest):
    return await asyncio.to_thread(session_manager.direct_login, req.email, req.password)

@app.post("/api/session/login/confirm-2fa")
async def confirm_2fa_api():
    return await asyncio.to_thread(session_manager.confirm_2fa_manually)

@app.post("/api/session/import")
async def import_session_api(req: ImportSessionRequest):
    return session_manager.import_session_json(req.session_json)

@app.get("/guide", response_class=HTMLResponse)
async def guide_page(request: Request):
    blogs = scheduler_runner.config.get("blogs", [])
    adsense_cfg = scheduler_runner.config.get("adsense", {})
    current_model = scheduler_runner.config.get("ai", {}).get("text_model", "gemini-3.5-flash")
    scheduled_jobs = scheduler_runner.get_scheduled_jobs_info()
    
    context = {
        "request": request,
        "blogs": blogs,
        "adsense": adsense_cfg,
        "current_model": current_model,
        "scheduled_jobs": scheduled_jobs
    }
    return templates.TemplateResponse(
        request=request,
        name="guide.html",
        context=context
    )

@app.post("/api/trigger-post")
async def trigger_post(req: TriggerPostRequest):
    try:
        logger.info(f"수동 포스팅 요청 수신: {req.blog_id} (임시저장={req.is_draft})")
        # Run Playwright Sync in separate worker thread to avoid asyncio event loop conflict
        result = await asyncio.to_thread(
            scheduler_runner.run_blog_pipeline,
            blog_id=req.blog_id,
            is_draft_override=req.is_draft
        )
        return result
    except Exception as e:
        logger.error(f"포스팅 실행 중 에러 발생: {e}")
        return JSONResponse(status_code=500, content={"success": False, "error": str(e)})

class UpdateQualityRequest(BaseModel):
    min_word_count: int = 2500
    max_word_count: int = 3500
    heading_count: str = "4_5"
    tone_style: str = "friendly_expert"
    add_table: bool = True
    add_faq: bool = True
    add_summary_card: bool = True

@app.post("/api/set-quality")
async def set_quality(req: UpdateQualityRequest):
    try:
        logger.info(f"글 품질 설정 업데이트 요청: {req.dict()}")
        
        # Update in-memory config
        pub_cfg = scheduler_runner.config.setdefault("publishing", {})
        pub_cfg["min_word_count"] = req.min_word_count
        pub_cfg["max_word_count"] = req.max_word_count
        pub_cfg["heading_count"] = req.heading_count
        pub_cfg["tone_style"] = req.tone_style
        pub_cfg["add_table"] = req.add_table
        pub_cfg["add_faq"] = req.add_faq
        pub_cfg["add_summary_card"] = req.add_summary_card
        
        # Persist to Database (Supabase) so settings survive redeploy/restart
        try:
            db.set_setting("quality_config", json.dumps(req.dict()))
        except Exception as db_err:
            logger.warning(f"DB 글 품질 설정 저장 실패: {db_err}")

        # Update config.yaml file
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                cfg = yaml.safe_load(f) or {}
            c_pub = cfg.setdefault("publishing", {})
            c_pub["min_word_count"] = req.min_word_count
            c_pub["max_word_count"] = req.max_word_count
            c_pub["heading_count"] = req.heading_count
            c_pub["tone_style"] = req.tone_style
            c_pub["add_table"] = req.add_table
            c_pub["add_faq"] = req.add_faq
            c_pub["add_summary_card"] = req.add_summary_card
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                yaml.dump(cfg, f, allow_unicode=True, default_flow_style=False)
                
        return {"success": True, "message": "글 품질 및 생성 설정이 성공적으로 저장되었습니다."}
    except Exception as e:
        logger.error(f"품질 설정 변경 중 오류: {e}")
        return JSONResponse(status_code=500, content={"success": False, "error": str(e)})

class UpdateScheduleCountRequest(BaseModel):
    daily_post_count: int

@app.post("/api/update-daily-schedule-count")
async def update_daily_schedule_count(req: UpdateScheduleCountRequest):
    try:
        res = scheduler_runner.update_daily_post_count(req.daily_post_count)
        # Persist to Database (Supabase)
        try:
            db.set_setting("daily_post_count", str(req.daily_post_count))
        except Exception as db_err:
            logger.warning(f"DB 스케줄 설정 저장 실패: {db_err}")
        return res
    except Exception as e:
        logger.error(f"일일 발행 횟수 변경 오류: {e}")
        return JSONResponse(status_code=500, content={"success": False, "error": str(e)})

@app.post("/api/set-model")
async def set_model(req: UpdateModelRequest):
    try:
        model = req.model_name.strip()
        logger.info(f"AI 텍스트 모델 변경 요청: {model}")
        
        # Update in-memory config
        scheduler_runner.config.setdefault("ai", {})["text_model"] = model

        # Persist to Database (Supabase)
        try:
            db.set_setting("ai_model", model)
        except Exception as db_err:
            logger.warning(f"DB 모델 설정 저장 실패: {db_err}")
        
        # Update config.yaml file
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                cfg = yaml.safe_load(f) or {}
            cfg.setdefault("ai", {})["text_model"] = model
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                yaml.dump(cfg, f, allow_unicode=True, default_flow_style=False)
                
        return {"success": True, "model": model, "message": f"AI 모델이 '{model}'(으)로 변경되었습니다."}
    except Exception as e:
        logger.error(f"모델 변경 중 오류: {e}")
        return JSONResponse(status_code=500, content={"success": False, "error": str(e)})

@app.post("/api/logs/clear")
async def clear_all_logs_api():
    """Clear both DB activity logs and raw terminal log file upon user request."""
    try:
        success_db = db.clear_activity_logs()
        
        # Truncate scheduler.log
        success_file = False
        log_file = os.path.join(BASE_DIR, "data", "scheduler.log")
        try:
            with open(log_file, "w", encoding="utf-8") as f:
                f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [INFO] 사용자에 의해 시스템 로그가 초기화되었습니다.\n")
            success_file = True
        except Exception as e:
            logger.error(f"로그 파일 비우기 실패: {e}")

        return {
            "success": success_db or success_file,
            "message": "누적된 활동 리포트 및 시스템 로그가 모두 정상적으로 초기화되었습니다."
        }
    except Exception as e:
        logger.error(f"로그 초기화 실패: {e}")
        return JSONResponse(status_code=500, content={"success": False, "error": str(e)})

@app.api_route("/api/health", methods=["GET", "HEAD"])
@app.api_route("/ping", methods=["GET", "HEAD"])
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "service": "Tistory Auto Publisher",
        "message": "Render Keep-Alive Heartbeat OK"
    }

@app.get("/api/trends")
async def get_trends():
    return trend_collector.get_realtime_trends(limit=15)

@app.get("/api/logs")
async def get_logs(limit: int = 50):
    log_file = os.path.join(BASE_DIR, "data", "scheduler.log")
    logs = []
    if os.path.exists(log_file):
        with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
            logs = [line.strip() for line in f.readlines() if line.strip()][-limit:]
    return {"logs": logs}

class DeletePostsRequest(BaseModel):
    post_ids: List[int]

@app.post("/api/posts/delete")
async def delete_selected_posts(req: DeletePostsRequest):
    try:
        deleted_count = db.delete_posts(req.post_ids)
        return {"success": True, "deleted_count": deleted_count}
    except Exception as e:
        logger.error(f"포스트 삭제 오류: {e}")
        return JSONResponse(status_code=500, content={"success": False, "error": str(e)})

@app.post("/api/posts/delete-all")
async def delete_all_posts():
    try:
        deleted_count = db.delete_all_posts()
        return {"success": True, "deleted_count": deleted_count}
    except Exception as e:
        logger.error(f"전체 포스트 삭제 오류: {e}")
        return JSONResponse(status_code=500, content={"success": False, "error": str(e)})

if __name__ == "__main__":
    import uvicorn
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 8000))
    logger.info(f"Starting server on {host}:{port}...")
    uvicorn.run("app:app", host=host, port=port, proxy_headers=True, forwarded_allow_ips="*")
