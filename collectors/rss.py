"""RSS and Atom feed collector for GSEIM."""

import logging
from typing import Dict, Any, List
import feedparser

from gseim.collectors.base import BaseCollector

logger = logging.getLogger("gseim.collectors.rss")

class RSSCollector(BaseCollector):
    """Collects ecosystem announcements and opportunities from RSS/Atom feeds."""

    def collect(self, source: Dict[str, Any]) -> List[Dict[str, Any]]:
        feed_url = source.get("rss")
        if not feed_url:
            return []

        logger.info(f"Fetching RSS feed for {source.get('organization')}: {feed_url}")
        res = self.fetch(feed_url, check_robots=False)  # RSS feeds are public syndications
        if not res or not res.text:
            return []

        parsed = feedparser.parse(res.text)
        records = []

        for entry in parsed.entries:
            title = entry.get("title", "").strip()
            link = entry.get("link", "").strip()
            if not title or not link:
                continue

            summary = entry.get("summary", "") or entry.get("description", "")
            published = entry.get("published", "") or entry.get("updated", "")

            # Tags / categories
            tags = [t.get("term", "") for t in entry.get("tags", []) if t.get("term")]

            records.append({
                "source_id": source.get("source_id"),
                "organization": source.get("organization"),
                "country": source.get("country"),
                "region": source.get("region"),
                "category": source.get("category"),
                "title": title,
                "url": link,
                "summary": summary,
                "published_date": published,
                "tags": tags,
                "collection_method": "RSS"
            })

        logger.info(f"Extracted {len(records)} entries from RSS feed: {feed_url}")
        return records
