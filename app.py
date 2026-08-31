"""
FastAPI Web Dashboard and REST API Server for Tistory Multi-Blog Publisher
"""

import os
import sys
import logging
from typing import Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
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

from core.database import DatabaseManager
from core.scheduler import MultiBlogScheduler
from core.trend_collector import TrendCollector

# Global singletons
db = DatabaseManager()
scheduler_runner = MultiBlogScheduler(use_background=True)
trend_collector = TrendCollector()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("FastAPI 시작: 백그라운드 스케줄러를 가동합니다...")
    scheduler_runner.start()
    yield
    logger.info("FastAPI 종료")

app = FastAPI(title="Tistory Multi-Blog Publisher Dashboard", lifespan=lifespan)

# Static and Templates
THUMBNAILS_DIR = os.path.join(BASE_DIR, "generated", "thumbnails")
os.makedirs(THUMBNAILS_DIR, exist_ok=True)
app.mount("/static/thumbnails", StaticFiles(directory=THUMBNAILS_DIR), name="thumbnails")

templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "web", "templates"))

class TriggerPostRequest(BaseModel):
    blog_id: str = "blog_1"
    is_draft: bool = False

@app.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request):
    stats = db.get_dashboard_stats()
    posts = db.get_all_posts(limit=50)
    blogs = scheduler_runner.config.get("blogs", [])
    trends = trend_collector.get_realtime_trends(limit=12)
    scheduled_jobs = scheduler_runner.get_scheduled_jobs_info()

    # Read last 15 log lines
    logs = []
    if os.path.exists(log_file):
        try:
            with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
                logs = [line.strip() for line in f.readlines()[-15:]]
        except Exception as e:
            logs = [f"Log reading note: {e}"]

    context = {
        "request": request,
        "stats": stats,
        "posts": posts,
        "blogs": blogs,
        "trends": trends,
        "scheduled_jobs": scheduled_jobs,
        "logs": logs
    }

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context=context
    )

@app.post("/api/trigger-post")
async def trigger_post(req: TriggerPostRequest):
    try:
        logger.info(f"수동 포스팅 요청 수신: {req.blog_id} (임시저장={req.is_draft})")
        result = scheduler_runner.run_blog_pipeline(blog_id=req.blog_id, is_draft_override=req.is_draft)
        return result
    except Exception as e:
        logger.error(f"포스팅 실행 중 에러 발생: {e}")
        return JSONResponse(status_code=500, content={"success": False, "error": str(e)})

@app.get("/api/trends")
async def get_trends():
    return trend_collector.get_realtime_trends(limit=15)

@app.get("/api/posts")
async def get_posts(blog_id: Optional[str] = None):
    return db.get_all_posts(blog_id=blog_id, limit=50)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
