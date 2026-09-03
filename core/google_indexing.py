"""
Google Search Console Indexing API Manager
Automatically submits newly published blog URLs to Google Indexing API for ultra-fast indexing.
"""

import os
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/indexing"]
SERVICE_ACCOUNT_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", "service_account.json")

class GoogleIndexingManager:
    def __init__(self, key_path: str = SERVICE_ACCOUNT_FILE):
        self.key_path = key_path

    def is_configured(self) -> bool:
        return os.path.exists(self.key_path) or bool(os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "").strip())

    def request_indexing(self, url: str, action: str = "URL_UPDATED") -> Dict[str, Any]:
        """Submit URL to Google Indexing API."""
        if not self.is_configured():
            logger.info("Google Service Account 키(service_account.json 또는 GOOGLE_SERVICE_ACCOUNT_JSON)가 없어 빠른 색인 요청을 건너뜁니다. (글 정상 발행에는 영향 없음)")
            return {"status": "SKIPPED", "message": "service_account.json not found"}

        try:
            from google.oauth2 import service_account
            from googleapiclient.discovery import build
        except ImportError:
            logger.info("googleapiclient 패키지가 설치되지 않아 빠른 색인(Indexing API)을 건너뜁니다. (글 정상 발행에는 영향 없음)")
            return {"status": "SKIPPED", "message": "googleapiclient not installed"}

        try:
            env_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "").strip()
            if env_json:
                account_info = json.loads(env_json)
                credentials = service_account.Credentials.from_service_account_info(
                    account_info, scopes=SCOPES
                )
            else:
                credentials = service_account.Credentials.from_service_account_file(
                    self.key_path, scopes=SCOPES
                )

            service = build("indexing", "v3", credentials=credentials)

            body = {
                "url": url,
                "type": action
            }

            response = service.urlNotifications().publish(body=body).execute()
            logger.info(f"Google Indexing API 요청 성공: {url} (응답: {response})")
            return {"status": "SUCCESS", "response": response}
        except Exception as e:
            logger.warning(f"Google Indexing API 요청 참고: {e}")
            return {"status": "ERROR", "error": str(e)}
