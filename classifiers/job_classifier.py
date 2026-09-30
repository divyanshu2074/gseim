"""Deterministic Job classifier and ecosystem role scorer for GSEIM."""

import re
from typing import Dict, Any, Optional
from datetime import date

from gseim.config.keywords import JOB_FUNCTIONS, JOB_WEIGHTS, EXCLUDE_JOBS
from gseim.config.settings import MIN_JOB_SCORE
from gseim.parsers.date_parser import extract_deadline, format_date_display, calculate_days_remaining
from gseim.parsers.metadata_parser import (
    extract_salary, extract_remote_status, extract_seniority, extract_employment_type
)

def detect_job_function(title: str, text: str) -> str:
    """Identify the specific ecosystem function (Incubation, Acceleration, Investment, etc.)."""
    combined = f"{title} {text}".lower()
    best_fn = "Ecosystem"
    max_matches = 0

    for fn_name, keywords in JOB_FUNCTIONS.items():
        matches = sum(1 for kw in keywords if re.search(r"\b" + re.escape(kw) + r"\b", combined))
        # Prioritize title match
        title_matches = sum(2 for kw in keywords if re.search(r"\b" + re.escape(kw) + r"\b", title.lower()))
        total = matches + title_matches

        if total > max_matches:
            max_matches = total
            best_fn = fn_name

    return best_fn

def calculate_job_score(title: str, text: str) -> int:
    """Calculate weighted ecosystem relevance score for job candidate."""
    title_lower = title.lower()
    combined = f"{title} {text}".lower()

    # Disqualify common non-ecosystem tech/sales roles
    for neg in EXCLUDE_JOBS:
        if re.search(r"\b" + re.escape(neg) + r"\b", title_lower):
            return -10

    score = 0
    # Positive ecosystem job weights
    for term, weight in JOB_WEIGHTS.items():
        if re.search(r"\b" + re.escape(term) + r"\b", title_lower):
            score += weight * 2
        elif re.search(r"\b" + re.escape(term) + r"\b", combined):
            score += weight

    return score

def classify_job(raw_item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Evaluate and classify an ecosystem job posting."""
    title = raw_item.get("title", "")
    text = f"{raw_item.get('summary', '')} {raw_item.get('content_preview', '')}"

    score = calculate_job_score(title, text)
    if score < MIN_JOB_SCORE:
        return None

    fn = detect_job_function(title, text)
    seniority = extract_seniority(title, text)
    employment = raw_item.get("employment_type") or extract_employment_type(text)
    location = raw_item.get("location") or raw_item.get("country", "Unknown")
    remote = extract_remote_status(f"{location} {text}")
    salary = extract_salary(text) or "Competitive / Not Disclosed"

    closing_iso = extract_deadline(text)
    closing_display = format_date_display(closing_iso) if closing_iso else "Rolling"
    days_left = calculate_days_remaining(closing_iso) if closing_iso else None

    today_str = date.today().strftime("%d-%m-%Y")

    return {
        "organization": raw_item.get("organization", "Unknown"),
        "country": raw_item.get("country", "Global"),
        "region": raw_item.get("region", "Global"),
        "job_title": title,
        "function": fn,
        "seniority": seniority,
        "employment": employment,
        "location": location,
        "remote": remote,
        "salary": salary,
        "closing_date": closing_display,
        "closing_iso": closing_iso,
        "days_remaining": days_left,
        "job_url": raw_item.get("url", ""),
        "source": raw_item.get("collection_method", "Official Website"),
        "last_checked": today_str,
        "relevance_score": score,
        "summary": raw_item.get("summary", "")[:500]
    }
