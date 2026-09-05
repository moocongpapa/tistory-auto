"""
Multi-Channel Real-time Notification Engine for Tistory Multi-Blog Publisher
Supports:
1. Telegram Bot (Instant smartphone lock-screen push alerts)
2. Discord Webhook (Rich embed cards)
3. Web Notification Integration
"""

import os
import logging
import requests
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class NotificationManager:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

    def get_telegram_creds(self):
        token = (
            os.environ.get("TELEGRAM_BOT_TOKEN")
            or self.config.get("notifications", {}).get("telegram", {}).get("bot_token")
            or self.config.get("notifications", {}).get("telegram", {}).get("token", "")
        )
        chat_id = (
            os.environ.get("TELEGRAM_CHAT_ID")
            or self.config.get("notifications", {}).get("telegram", {}).get("chat_id", "")
        )
        return str(token).strip(), str(chat_id).strip()

    def get_discord_webhook(self):
        url = (
            os.environ.get("DISCORD_WEBHOOK_URL")
            or self.config.get("notifications", {}).get("discord", {}).get("webhook_url", "")
        )
        return str(url).strip()

    def is_configured(self) -> bool:
        t_token, t_chat = self.get_telegram_creds()
        d_url = self.get_discord_webhook()
        return bool((t_token and t_chat) or d_url)

    def send_post_notification(
        self,
        blog_name: str,
        title: str,
        category: str,
        url: str,
        word_count: int = 0,
        is_draft: bool = False,
        is_hot_issue: bool = False
    ) -> Dict[str, bool]:
        """Send post publication alert to Telegram and/or Discord."""
        results = {"telegram": False, "discord": False}

        # 1. Telegram
        token, chat_id = self.get_telegram_creds()
        if token and chat_id:
            try:
                hot_tag = "🔥 [실시간 핫이슈] " if is_hot_issue else ""
                action_text = "임시저장(비공개 보관)" if is_draft else "공개 발행 완료 🎉"
                words_str = f" ({word_count:,}자)" if word_count > 0 else ""

                text = (
                    f"📢 <b>[{blog_name}] 새 글 {action_text}</b>\n\n"
                    f"📌 <b>제목:</b> {hot_tag}{title}\n"
                    f"🏷️ <b>카테고리:</b> {category}{words_str}\n"
                    f"🔗 <b>포스팅 확인:</b> <a href=\"{url}\">{url}</a>"
                )

                resp = requests.post(
                    f"https://api.telegram.org/bot{token}/sendMessage",
                    json={
                        "chat_id": chat_id,
                        "text": text,
                        "parse_mode": "HTML",
                        "disable_web_page_preview": False
                    },
                    timeout=8
                )
                if resp.status_code == 200:
                    logger.info("📱 [텔레그램] 실시간 모바일 푸시 알림 전송 성공!")
                    results["telegram"] = True
                else:
                    logger.warning(f"텔레그램 푸시 실패 ({resp.status_code}): {resp.text}")
            except Exception as e:
                logger.warning(f"텔레그램 푸시 발송 예외: {e}")

        # 2. Discord Webhook
        discord_url = self.get_discord_webhook()
        if discord_url:
            try:
                hot_tag = "🔥 [실시간 핫이슈] " if is_hot_issue else ""
                action_text = "임시저장" if is_draft else "공개 발행 완료"
                embed = {
                    "title": f"🎉 [{blog_name}] {hot_tag}새 글 {action_text}!",
                    "description": f"**{title}**\n\n🏷️ 카테고리: `{category}`\n🔗 [블로그 바로가기]({url})",
                    "color": 0x4f46e5 if not is_draft else 0xf59e0b,
                    "url": url,
                    "footer": {"text": "Tistory Multi-Blog AI Publisher"}
                }
                resp = requests.post(
                    discord_url,
                    json={"embeds": [embed]},
                    timeout=8
                )
                if resp.status_code in (200, 204):
                    logger.info("🎮 [디스코드] 실시간 웹훅 알림 전송 성공!")
                    results["discord"] = True
                else:
                    logger.warning(f"디스코드 웹훅 실패 ({resp.status_code}): {resp.text}")
            except Exception as e:
                logger.warning(f"디스코드 웹훅 발송 예외: {e}")

        return results

    def send_error_notification(self, blog_name: str, title: str, error_msg: str) -> Dict[str, bool]:
        """Send critical failure alert (e.g. Kakao login expired)."""
        results = {"telegram": False, "discord": False}

        token, chat_id = self.get_telegram_creds()
        if token and chat_id:
            try:
                text = (
                    f"🚨 <b>[{blog_name}] 자동 발행 실패 알림</b>\n\n"
                    f"📌 <b>키워드:</b> {title}\n"
                    f"⚠️ <b>원인:</b> {error_msg}\n\n"
                    f"👉 웹 대시보드에 접속하여 카카오 세션을 확인해주세요."
                )
                resp = requests.post(
                    f"https://api.telegram.org/bot{token}/sendMessage",
                    json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"},
                    timeout=8
                )
                if resp.status_code == 200:
                    results["telegram"] = True
            except Exception as e:
                logger.warning(f"텔레그램 에러 알림 발송 예외: {e}")

        discord_url = self.get_discord_webhook()
        if discord_url:
            try:
                embed = {
                    "title": f"🚨 [{blog_name}] 자동 발행 오류 발생",
                    "description": f"**키워드:** {title}\n\n⚠️ **원인:** {error_msg}\n\n대시보드에서 상태를 확인하세요.",
                    "color": 0xef4444,
                    "footer": {"text": "Tistory Multi-Blog AI Publisher"}
                }
                resp = requests.post(discord_url, json={"embeds": [embed]}, timeout=8)
                if resp.status_code in (200, 204):
                    results["discord"] = True
            except Exception as e:
                logger.warning(f"디스코드 에러 알림 발송 예외: {e}")

        return results

    def send_test_message(self) -> Dict[str, Any]:
        """Sends a verification test message to all configured channels."""
        token, chat_id = self.get_telegram_creds()
        discord_url = self.get_discord_webhook()

        report = {
            "telegram": {"configured": bool(token and chat_id), "success": False, "error": None},
            "discord": {"configured": bool(discord_url), "success": False, "error": None}
        }

        if token and chat_id:
            try:
                msg = (
                    "🔔 <b>[티스토리 자동 발행기] 테스트 알림 성공!</b>\n\n"
                    "앞으로 글이 발행되거나 세션 만료 등의 이벤트가 발생할 때마다 "
                    "스마트폰 텔레그램으로 실시간 푸시 알림이 전송됩니다. 🚀"
                )
                resp = requests.post(
                    f"https://api.telegram.org/bot{token}/sendMessage",
                    json={"chat_id": chat_id, "text": msg, "parse_mode": "HTML"},
                    timeout=8
                )
                if resp.status_code == 200:
                    report["telegram"]["success"] = True
                else:
                    report["telegram"]["error"] = f"HTTP {resp.status_code}: {resp.text}"
            except Exception as e:
                report["telegram"]["error"] = str(e)

        if discord_url:
            try:
                embed = {
                    "title": "🔔 티스토리 자동 발행기 알림 테스트 성공!",
                    "description": "디스코드 웹훅 연결이 정상 작동 중입니다. 글 발행 시 실시간으로 알림 카드가 전송됩니다.",
                    "color": 0x10b981
                }
                resp = requests.post(discord_url, json={"embeds": [embed]}, timeout=8)
                if resp.status_code in (200, 204):
                    report["discord"]["success"] = True
                else:
                    report["discord"]["error"] = f"HTTP {resp.status_code}: {resp.text}"
            except Exception as e:
                report["discord"]["error"] = str(e)

        return report
