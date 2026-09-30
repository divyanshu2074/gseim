"""Deterministic Opportunity classifier and relevance scorer for GSEIM."""

import re
from typing import Dict, Any, Optional, Tuple
from datetime import date

from gseim.config.keywords import (
    CATEGORY_KEYWORDS, OPPORTUNITY_WEIGHTS, EXCLUDE_OPPORTUNITIES,
    SECTOR_KEYWORDS, STAGES
)
from gseim.config.settings import MIN_OPPORTUNITY_SCORE
from gseim.parsers.date_parser import extract_deadline, format_date_display, calculate_days_remaining

def detect_category(text: str) -> str:
    """Identify the primary opportunity type (Grant, Accelerator, Incubator, etc.)."""
    t_lower = text.lower()
    best_cat = "Opportunity"
    max_count = 0

    for category, keywords in CATEGORY_KEYWORDS.items():
        count = sum(1 for kw in keywords if re.search(r"\b" + re.escape(kw) + r"\b", t_lower))
        if count > max_count:
            max_count = count
            best_cat = category

    return best_cat if max_count > 0 else "Opportunity"

def detect_sector(text: str) -> str:
    """Identify startup sector (DeepTech, AI/ML, ClimateTech, etc.)."""
    t_lower = text.lower()
    for sector, keywords in SECTOR_KEYWORDS.items():
        if any(re.search(r"\b" + re.escape(kw) + r"\b", t_lower) for kw in keywords):
            return sector
    return "Sector Agnostic"

def detect_stage(text: str) -> str:
    """Identify startup development stage."""
    t_lower = text.lower()
    if "ideation" in t_lower or "idea stage" in t_lower:
        return "Ideation"
    if "pre-seed" in t_lower or "pre seed" in t_lower:
        return "Pre-Seed"
    if "seed" in t_lower:
        return "Seed"
    if "series a" in t_lower or "early stage" in t_lower:
        return "Early Stage"
    if "growth" in t_lower or "scaleup" in t_lower:
        return "Growth / Scaleup"
    return "All Stages"

def calculate_opportunity_score(title: str, text: str) -> int:
    """Compute weighted relevance score using title and text context."""
    combined = f"{title} {text}".lower()

    # Immediate negative exclusion
    if any(neg in combined for neg in EXCLUDE_OPPORTUNITIES):
        return -10

    score = 0
    # Positive weights
    for term, weight in OPPORTUNITY_WEIGHTS.items():
        if re.search(r"\b" + re.escape(term) + r"\b", combined):
            # Double weight if in title
            if re.search(r"\b" + re.escape(term) + r"\b", title.lower()):
                score += weight * 2
            else:
                score += weight

    return score

def extract_eligibility(text: str) -> str:
    """Extract brief eligibility condition if mentioned."""
    m = re.search(r"(?:eligibility|who can apply|criteria)[\s:]+([^\n\.\r]{10,120})", text, flags=re.IGNORECASE)
    if m:
        return m.group(1).strip()
    return "Startups & innovators in target sector"

def classify_opportunity(raw_item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Evaluate and classify an opportunity candidate."""
    title = raw_item.get("title", "")
    text = f"{raw_item.get('summary', '')} {raw_item.get('content_preview', '')}"

    score = calculate_opportunity_score(title, text)
    if score < MIN_OPPORTUNITY_SCORE:
        return None

    cat = detect_category(f"{title} {text}")
    sector = detect_sector(f"{title} {text}")
    stage = detect_stage(f"{title} {text}")

    # Deadline extraction
    deadline_iso = raw_item.get("deadline_hint") or extract_deadline(text)
    deadline_display = format_date_display(deadline_iso) if deadline_iso else "Rolling / Open"
    days_left = calculate_days_remaining(deadline_iso) if deadline_iso else None

    # Application status
    if days_left is not None and days_left < 0:
        app_status = "Closed"
    else:
        app_status = "Open"

    today_str = date.today().strftime("%d-%m-%Y")

    return {
        "organization": raw_item.get("organization", "Unknown"),
        "country": raw_item.get("country", "Global"),
        "region": raw_item.get("region", "Global"),
        "type": cat,
        "opportunity": title,
        "sector": sector,
        "startup_stage": stage,
        "eligibility": extract_eligibility(text),
        "application_status": app_status,
        "deadline_iso": deadline_iso,
        "deadline": deadline_display,
        "days_remaining": days_left,
        "source_url": raw_item.get("url", ""),
        "source_type": raw_item.get("collection_method", "Official Website"),
        "last_checked": today_str,
        "relevance_score": score,
        "summary": raw_item.get("summary", "")[:500]
    }
