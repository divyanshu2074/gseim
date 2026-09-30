"""Direct HTML and DOM structure collector for GSEIM."""

import logging
import json
from typing import Dict, Any, List
from urllib.parse import urljoin
from bs4 import BeautifulSoup

from gseim.collectors.base import BaseCollector

logger = logging.getLogger("gseim.collectors.html")

class HTMLCollector(BaseCollector):
    """Extracts structured opportunities and jobs from HTML pages."""

    def collect(self, source: Dict[str, Any]) -> List[Dict[str, Any]]:
        records = []
        target_urls = []

        if source.get("opportunities_page"):
            target_urls.append(("opportunity", source["opportunities_page"]))
        if source.get("jobs_page") and source.get("jobs_page") != source.get("opportunities_page"):
            target_urls.append(("job", source["jobs_page"]))
        if not target_urls and source.get("website"):
            target_urls.append(("general", source["website"]))

        for page_type, target_url in target_urls:
            logger.info(f"Scraping HTML for {source.get('organization')} [{page_type}]: {target_url}")
            res = self.fetch(target_url, check_robots=True)
            if not res or not res.text:
                continue

            extracted = self._parse_html_page(res.text, target_url, source, page_type)
            records.extend(extracted)

        return records

    def _parse_html_page(self, html_text: str, base_url: str, source: Dict[str, Any], page_type: str) -> List[Dict[str, Any]]:
        soup = BeautifulSoup(html_text, "lxml")
        records = []

        # 1. Attempt JSON-LD extraction
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string or "{}")
                items = data if isinstance(data, list) else [data]
                for item in items:
                    item_type = item.get("@type", "")
                    if item_type in ["JobPosting", "Event", "Grant", "Organization"]:
                        name = item.get("title") or item.get("name")
                        url = item.get("url") or base_url
                        desc = item.get("description") or ""
                        if name:
                            records.append({
                                "source_id": source.get("source_id"),
                                "organization": source.get("organization"),
                                "country": source.get("country"),
                                "region": source.get("region"),
                                "category": source.get("category"),
                                "title": name.strip(),
                                "url": urljoin(base_url, url),
                                "summary": desc[:1000].strip(),
                                "content_preview": desc[:3000].strip(),
                                "published_date": item.get("datePosted", "") or item.get("startDate", ""),
                                "deadline_hint": item.get("validThrough", "") or item.get("endDate", ""),
                                "collection_method": "HTML_JSONLD"
                            })
            except Exception:
                pass

        # 2. Card/Container Based Extraction
        # Look for standard card containers
        cards = soup.select(
            ".card, .program-card, .opportunity-card, .job-item, .post-item, "
            ".view-content .views-row, article, .item-list li, tr"
        )

        for card in cards[:30]:
            # Find title / link inside card
            link_tag = card.find("a")
            if not link_tag or not link_tag.get("href"):
                continue

            link_url = urljoin(base_url, link_tag["href"])
            title = link_tag.get_text(strip=True)

            if not title or len(title) < 5 or len(title) > 200:
                # Try finding heading inside card
                heading = card.find(["h2", "h3", "h4", "h5", "strong"])
                if heading:
                    title = heading.get_text(strip=True)

            if not title or len(title) < 5:
                continue

            # Extract date if available
            time_tag = card.find("time")
            date_str = time_tag.get_text(strip=True) if time_tag else ""
            if not date_str and time_tag and time_tag.get("datetime"):
                date_str = time_tag["datetime"]

            # Extract text snippet
            snippet = card.get_text(separator=" ", strip=True)

            records.append({
                "source_id": source.get("source_id"),
                "organization": source.get("organization"),
                "country": source.get("country"),
                "region": source.get("region"),
                "category": source.get("category"),
                "title": title,
                "url": link_url,
                "summary": snippet[:800],
                "content_preview": snippet[:2000],
                "published_date": date_str,
                "collection_method": "HTML_DOM"
            })

        # 3. If no cards found, extract page-level item
        if not records:
            page_title = soup.title.string.strip() if soup.title and soup.title.string else ""
            meta_desc = soup.find("meta", attrs={"name": "description"}) or soup.find("meta", attrs={"property": "og:description"})
            summary = meta_desc.get("content", "").strip() if meta_desc else ""
            if not summary:
                p = soup.find("p")
                summary = p.get_text(strip=True) if p else ""

            if page_title:
                records.append({
                    "source_id": source.get("source_id"),
                    "organization": source.get("organization"),
                    "country": source.get("country"),
                    "region": source.get("region"),
                    "category": source.get("category"),
                    "title": page_title,
                    "url": base_url,
                    "summary": summary[:800],
                    "content_preview": soup.get_text(separator=" ", strip=True)[:2500],
                    "published_date": "",
                    "collection_method": "HTML_PAGE"
                })

        return records
