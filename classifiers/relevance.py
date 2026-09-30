"""Unified relevance and classification dispatcher for GSEIM."""

import re
from typing import Dict, Any, Tuple, Optional
from datetime import date

from gseim.classifiers.opportunity_classifier import classify_opportunity
from gseim.classifiers.job_classifier import classify_job
from gseim.config.keywords import UPDATE_KEYWORDS

def detect_ecosystem_update(raw_item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Detect ecosystem announcements (new funds, centres of excellence, state policies)."""
    title = raw_item.get("title", "")
    summary = raw_item.get("summary", "") or raw_item.get("content_preview", "")
    combined = f"{title} {summary}".lower()

    if any(re.search(r"\b" + re.escape(kw) + r"\b", combined) for kw in UPDATE_KEYWORDS):
        today_str = date.today().strftime("%d-%m-%Y")
        return {
            "date": today_str,
            "organization": raw_item.get("organization", "Unknown"),
            "country": raw_item.get("country", "Global"),
            "category": raw_item.get("category", "Ecosystem News"),
            "title": title.strip(),
            "summary": summary[:400].strip(),
            "url": raw_item.get("url", "")
        }
    return None

def evaluate_item_relevance(raw_item: Dict[str, Any]) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    """
    Route item to Job, Opportunity, or Ecosystem Update classifier.
    Returns (item_type, classified_record) or (None, None).
    """
    title = raw_item.get("title", "")
    url = raw_item.get("url", "").lower()

    # Prioritize Job if URL has /careers, /jobs, or title indicates job
    is_job_context = any(j in url for j in ["job", "career", "lever", "greenhouse", "ashby"]) or \
                     any(kw in title.lower() for kw in ["manager", "associate", "analyst", "director", "officer", "lead"])

    if is_job_context:
        job = classify_job(raw_item)
        if job:
            return ("job", job)

    # Opportunity Evaluation
    opp = classify_opportunity(raw_item)
    if opp:
        return ("opportunity", opp)

    # Secondary Job Evaluation (if not caught earlier)
    if not is_job_context:
        job = classify_job(raw_item)
        if job:
            return ("job", job)

    # Ecosystem Update Evaluation
    update = detect_ecosystem_update(raw_item)
    if update:
        return ("update", update)

    return (None, None)
