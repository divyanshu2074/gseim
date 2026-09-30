"""Metadata and field extractor for jobs and ecosystem opportunities."""

import re
from typing import Optional

def extract_salary(text: str) -> Optional[str]:
    """Extract salary or compensation patterns from text."""
    if not text:
        return None

    # Matches £50,000–£60,000, $80k - $120k, ₹15-25 LPA, €60,000
    patterns = [
        r"(?:[$£€₹]|USD|GBP|EUR|INR)\s*[\d,]+(?:\.\d+)?\s*(?:k|K|LPA|lakhs?|lac)?(?:\s*(?:–|-|to)\s*(?:[$£€₹]|USD|GBP|EUR|INR)?\s*[\d,]+(?:\.\d+)?\s*(?:k|K|LPA|lakhs?|lac)?)?",
        r"[\d,]+\s*(?:LPA|lakhs?|lac)",
    ]

    for pat in patterns:
        m = re.search(pat, text, flags=re.IGNORECASE)
        if m:
            val = m.group(0).strip()
            if len(val) > 2:
                return val
    return None

def extract_remote_status(text: str) -> str:
    """Determine remote eligibility from text."""
    if not text:
        return "No"
    t = text.lower()
    if "fully remote" in t or "100% remote" in t or "remote worldwide" in t:
        return "Remote"
    if "hybrid" in t or "flexible remote" in t:
        return "Hybrid"
    if "remote" in t and "no remote" not in t and "not remote" not in t:
        return "Yes"
    return "No"

def extract_seniority(title: str, text: str = "") -> str:
    """Infer seniority from job title and context."""
    combined = f"{title} {text}".lower()
    if any(k in combined for k in ["head of", "director", "vp ", "vice president", "chief", "managing director"]):
        return "Director / Executive"
    if any(k in combined for k in ["lead", "principal", "senior manager"]):
        return "Lead / Principal"
    if any(k in combined for k in ["senior", "sr."]):
        return "Senior"
    if any(k in combined for k in ["manager", "associate director", "specialist"]):
        return "Mid-Senior"
    if any(k in combined for k in ["associate", "analyst", "coordinator"]):
        return "Associate / Analyst"
    if any(k in combined for k in ["intern", "fellow", "trainee"]):
        return "Entry / Intern"
    return "Mid-Level"

def extract_employment_type(text: str) -> str:
    """Infer full-time, part-time, or contract."""
    t = text.lower()
    if "part-time" in t or "part time" in t:
        return "Part-time"
    if "contract" in t or "consultant" in t:
        return "Contract"
    if "fellowship" in t:
        return "Fellowship"
    return "Full-time"
