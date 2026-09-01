"""
Real-time Trend Collector (Google Trends RSS & Web Trending Topics)
"""

import logging
import feedparser
import urllib.parse
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

GOOGLE_TRENDS_KR_RSS = "https://trends.google.com/trending/rss?geo=KR"

class TrendCollector:
    def __init__(self):
        pass

    def get_realtime_trends(self, limit: int = 15) -> List[Dict[str, Any]]:
        """Fetch live trending queries from Google Trends Korea RSS."""
        trends = []
        try:
            feed = feedparser.parse(GOOGLE_TRENDS_KR_RSS)
            for entry in feed.entries[:limit]:
                title = entry.get("title", "").strip()
                approx_traffic = entry.get("ht_approx_traffic", "")
                news_items = []
                # News item summaries if present
                if "ht_news_item_title" in entry:
                    news_items.append(entry["ht_news_item_title"])

                if title:
                    trends.append({
                        "query": title,
                        "traffic": approx_traffic,
                        "news_headlines": news_items,
                        "source": "Google Trends KR"
                    })
            logger.info(f"Fetched {len(trends)} real-time trends from Google Trends KR.")
        except Exception as e:
            logger.warning(f"Failed to fetch Google Trends RSS: {e}")

        # Fallback keywords if feed is empty or blocked
        if not trends:
            trends = [
                {"query": "청년도약계좌 신청조건", "traffic": "10K+", "news_headlines": []},
                {"query": "생성형 AI 업무 활용법", "traffic": "10K+", "news_headlines": []},
                {"query": "연말정산 환급 꿀팁", "traffic": "10K+", "news_headlines": []},
                {"query": "간헐적 단식 식단 가이드", "traffic": "10K+", "news_headlines": []},
                {"query": "생산성 향상 시간 관리법", "traffic": "10K+", "news_headlines": []},
            ]
        return trends

    def get_trend_keywords_list(self, limit: int = 10) -> List[str]:
        trends = self.get_realtime_trends(limit=limit)
        return [t["query"] for t in trends if t.get("query")]
