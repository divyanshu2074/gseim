"""Sitemap and robots.txt discovery collector for GSEIM."""

import logging
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse, urljoin
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup

from gseim.collectors.base import BaseCollector

logger = logging.getLogger("gseim.collectors.sitemap")

RELEVANT_PATH_KEYWORDS = [
    "program", "grant", "challenge", "accelerat", "incubat",
    "cohort", "fellow", "fund", "career", "job", "opportunit",
    "call-for", "apply", "tender", "scheme"
]

class SitemapCollector(BaseCollector):
    """Discovers sitemaps via robots.txt and traverses prioritized URLs."""

    def discover_sitemap_urls(self, website_url: str) -> List[str]:
        """Discover sitemap locations from robots.txt or standard paths."""
        parsed = urlparse(website_url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        robots_url = f"{base}/robots.txt"
        sitemaps = []

        try:
            res = self.session.get(robots_url, timeout=5)
            if res.status_code == 200:
                for line in res.text.splitlines():
                    if line.strip().lower().startswith("sitemap:"):
                        parts = line.split(":", 1)
                        if len(parts) > 1:
                            sitemap_url = parts[1].strip()
                            if sitemap_url:
                                sitemaps.append(sitemap_url)
        except Exception as e:
            logger.debug(f"Error checking robots.txt for sitemap on {website_url}: {e}")

        if not sitemaps:
            sitemaps.append(f"{base}/sitemap.xml")
            sitemaps.append(f"{base}/sitemap_index.xml")

        return list(dict.fromkeys(sitemaps))

    def parse_sitemap_xml(self, sitemap_url: str, max_depth: int = 2) -> List[Dict[str, str]]:
        """Parse sitemap XML, handling nested sitemap index hierarchies."""
        if max_depth <= 0:
            return []

        res = self.fetch(sitemap_url, check_robots=False)
        if not res or not res.content:
            return []

        urls = []
        try:
            root = ET.fromstring(res.content)
            # Remove XML namespace prefix if present
            namespace = ""
            if "}" in root.tag:
                namespace = root.tag.split("}")[0] + "}"

            # Check if this is a sitemapindex
            if "sitemapindex" in root.tag.lower():
                for sitemap_node in root.findall(f"{namespace}sitemap"):
                    loc_node = sitemap_node.find(f"{namespace}loc")
                    if loc_node is not None and loc_node.text:
                        sub_url = loc_node.text.strip()
                        # Only follow sub-sitemaps that might contain pages or posts
                        if any(kw in sub_url.lower() for kw in ["post", "page", "program", "main", "content", "default"]):
                            urls.extend(self.parse_sitemap_xml(sub_url, max_depth - 1))
            else:
                # Regular urlset
                for url_node in root.findall(f"{namespace}url"):
                    loc_node = url_node.find(f"{namespace}loc")
                    lastmod_node = url_node.find(f"{namespace}lastmod")

                    if loc_node is not None and loc_node.text:
                        loc = loc_node.text.strip()
                        lastmod = lastmod_node.text.strip() if lastmod_node is not None and lastmod_node.text else ""
                        urls.append({"url": loc, "lastmod": lastmod})
        except Exception as e:
            logger.debug(f"Failed to parse sitemap XML {sitemap_url}: {e}")

        return urls

    def is_relevant_url(self, url: str) -> bool:
        """Check if URL slug likely points to an opportunity, program, or job."""
        url_lower = url.lower()
        return any(kw in url_lower for kw in RELEVANT_PATH_KEYWORDS)

    def extract_page_summary(self, url: str) -> Optional[Dict[str, Any]]:
        """Download page HTML and extract metadata/title/summary."""
        res = self.fetch(url, check_robots=True)
        if not res or not res.text:
            return None

        soup = BeautifulSoup(res.text, "lxml")
        title = soup.title.string.strip() if soup.title and soup.title.string else ""
        if not title:
            h1 = soup.find("h1")
            title = h1.get_text(strip=True) if h1 else ""

        # Meta description
        meta_desc = soup.find("meta", attrs={"name": "description"}) or soup.find("meta", attrs={"property": "og:description"})
        summary = meta_desc.get("content", "").strip() if meta_desc else ""

        if not summary:
            # Fallback to first paragraph
            p = soup.find("p")
            summary = p.get_text(strip=True) if p else ""

        return {
            "title": title,
            "summary": summary[:1000],
            "text": soup.get_text(separator=" ", strip=True)[:3000]
        }

    def collect(self, source: Dict[str, Any], max_items: int = 15) -> List[Dict[str, Any]]:
        target_sitemaps = []
        if source.get("sitemap"):
            target_sitemaps.append(source["sitemap"])
        elif source.get("website"):
            target_sitemaps = self.discover_sitemap_urls(source["website"])

        logger.info(f"Checking sitemaps for {source.get('organization')}")
        all_urls = []
        for sm_url in target_sitemaps:
            urls = self.parse_sitemap_xml(sm_url)
            if urls:
                all_urls.extend(urls)
                break

        # Filter for relevant URLs
        relevant_items = [u for u in all_urls if self.is_relevant_url(u["url"])]
        logger.info(f"Found {len(relevant_items)} relevant URLs out of {len(all_urls)} in sitemap for {source.get('organization')}")

        records = []
        for item in relevant_items[:max_items]:
            page_data = self.extract_page_summary(item["url"])
            if not page_data or not page_data["title"]:
                continue

            records.append({
                "source_id": source.get("source_id"),
                "organization": source.get("organization"),
                "country": source.get("country"),
                "region": source.get("region"),
                "category": source.get("category"),
                "title": page_data["title"],
                "url": item["url"],
                "summary": page_data["summary"],
                "content_preview": page_data.get("text", ""),
                "published_date": item.get("lastmod", ""),
                "collection_method": "Sitemap"
            })

        return records
