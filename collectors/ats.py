"""Specialized ATS (Applicant Tracking System) adapters for GSEIM."""

import logging
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse

from gseim.collectors.base import BaseCollector

logger = logging.getLogger("gseim.collectors.ats")

class ATSCollector(BaseCollector):
    """Direct API / structured endpoint adapter for common job platforms (Lever, Greenhouse, Ashby, SmartRecruiters)."""

    def identify_ats(self, url: str) -> Optional[str]:
        """Detect which ATS platform hosts the careers board."""
        if not url:
            return None
        u = url.lower()
        if "lever.co" in u:
            return "lever"
        if "greenhouse.io" in u:
            return "greenhouse"
        if "ashbyhq.com" in u:
            return "ashby"
        if "smartrecruiters.com" in u:
            return "smartrecruiters"
        return None

    def _extract_board_name(self, url: str) -> str:
        """Extract company/board identifier from ATS URL."""
        parsed = urlparse(url)
        path_parts = [p for p in parsed.path.strip("/").split("/") if p]
        return path_parts[0] if path_parts else ""

    def collect_lever(self, board_id: str, source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Query Lever public API: api.lever.co/v0/postings/{board_id}?mode=json"""
        api_url = f"https://api.lever.co/v0/postings/{board_id}?mode=json"
        res = self.fetch(api_url, check_robots=False)
        if not res:
            return []

        jobs = []
        try:
            data = res.json()
            for item in data:
                title = item.get("text", "")
                url = item.get("hostedUrl", "")
                categories = item.get("categories", {})
                location = categories.get("location", "")
                commitment = categories.get("commitment", "")
                team = categories.get("team", "")
                description = item.get("descriptionPlain", "") or item.get("additionalPlain", "")

                jobs.append({
                    "source_id": source.get("source_id"),
                    "organization": source.get("organization"),
                    "country": source.get("country"),
                    "region": source.get("region"),
                    "category": "Ecosystem Job",
                    "title": title,
                    "url": url,
                    "location": location,
                    "employment_type": commitment,
                    "department": team,
                    "summary": description[:800],
                    "content_preview": description[:2000],
                    "published_date": str(item.get("createdAt", "")),
                    "collection_method": "ATS_LEVER"
                })
        except Exception as e:
            logger.warning(f"Error parsing Lever API for {board_id}: {e}")

        return jobs

    def collect_greenhouse(self, board_id: str, source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Query Greenhouse public API: boards-api.greenhouse.io/v1/boards/{board_id}/jobs?content=true"""
        api_url = f"https://boards-api.greenhouse.io/v1/boards/{board_id}/jobs?content=true"
        res = self.fetch(api_url, check_robots=False)
        if not res:
            return []

        jobs = []
        try:
            data = res.json()
            job_list = data.get("jobs", [])
            for item in job_list:
                title = item.get("title", "")
                url = item.get("absolute_url", "")
                loc = item.get("location", {}).get("name", "")
                content = item.get("content", "")
                updated_at = item.get("updated_at", "")

                jobs.append({
                    "source_id": source.get("source_id"),
                    "organization": source.get("organization"),
                    "country": source.get("country"),
                    "region": source.get("region"),
                    "category": "Ecosystem Job",
                    "title": title,
                    "url": url,
                    "location": loc,
                    "summary": content[:800],
                    "content_preview": content[:2000],
                    "published_date": updated_at,
                    "collection_method": "ATS_GREENHOUSE"
                })
        except Exception as e:
            logger.warning(f"Error parsing Greenhouse API for {board_id}: {e}")

        return jobs

    def collect_ashby(self, board_id: str, source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Query Ashby posting API: api.ashbyhq.com/posting-api/job-board/{board_id}"""
        api_url = f"https://api.ashbyhq.com/posting-api/job-board/{board_id}"
        res = self.fetch(api_url, check_robots=False)
        if not res:
            return []

        jobs = []
        try:
            data = res.json()
            postings = data.get("jobs", [])
            for item in postings:
                title = item.get("title", "")
                url = item.get("jobUrl", "")
                loc = item.get("location", "")
                comp = item.get("employmentType", "")
                desc = item.get("descriptionHtml", "")

                jobs.append({
                    "source_id": source.get("source_id"),
                    "organization": source.get("organization"),
                    "country": source.get("country"),
                    "region": source.get("region"),
                    "category": "Ecosystem Job",
                    "title": title,
                    "url": url,
                    "location": loc,
                    "employment_type": comp,
                    "summary": desc[:800],
                    "content_preview": desc[:2000],
                    "published_date": item.get("publishedAt", ""),
                    "collection_method": "ATS_ASHBY"
                })
        except Exception as e:
            logger.warning(f"Error parsing Ashby API for {board_id}: {e}")

        return jobs

    def collect(self, source: Dict[str, Any]) -> List[Dict[str, Any]]:
        target_url = source.get("jobs_page") or source.get("website")
        if not target_url:
            return []

        platform = self.identify_ats(target_url)
        if not platform:
            return []

        board_id = self._extract_board_name(target_url)
        if not board_id:
            return []

        logger.info(f"Targeting ATS [{platform}] board '{board_id}' for {source.get('organization')}")
        results = []
        if platform == "lever":
            results = self.collect_lever(board_id, source)
        elif platform == "greenhouse":
            results = self.collect_greenhouse(board_id, source)
        elif platform == "ashby":
            results = self.collect_ashby(board_id, source)

        # Fallback to direct HTML card scraping if ATS API returned no results
        if not results:
            logger.info(f"ATS API returned 0 items; falling back to DOM extraction for {target_url}")
            from gseim.collectors.html import HTMLCollector
            html_collector = HTMLCollector(user_agent=self.user_agent, timeout=self.timeout)
            results = html_collector.collect(source)

        return results
