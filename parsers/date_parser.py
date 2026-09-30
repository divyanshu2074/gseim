"""Deterministic date and deadline parsing for GSEIM."""

import re
from datetime import datetime, date
from typing import Optional, Tuple
from dateutil import parser as date_parser

DEADLINE_PREFIX_PATTERNS = [
    r"(?:applications?\s+close[ds]?|application\s+deadline|submission\s+deadline|deadline\s+is|deadline|apply\s+by|closing\s+date|last\s+date(?:\s+to\s+apply)?|due\s+date)[\s:]+([A-Za-z0-9,\s/\.-]{4,35})",
    r"(?:until|before)\s+([0-9]{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+\s+202[4-9])",
    r"([0-9]{1,2}[/-][0-9]{1,2}[/-]202[4-9])",
]

MONTH_NAMES = [
    "january", "february", "march", "april", "may", "june",
    "july", "august", "september", "october", "november", "december",
    "jan", "feb", "mar", "apr", "jun", "jul", "aug", "sep", "oct", "nov", "dec"
]

def parse_date_to_iso(text: str) -> Optional[str]:
    """Parse text into a clean YYYY-MM-DD format."""
    if not text:
        return None
    try:
        # Clean ordinal suffixes like 1st, 2nd, 3rd, 4th
        cleaned = re.sub(r"(\d+)(st|nd|rd|th)", r"\1", text.strip(), flags=re.IGNORECASE)
        # Parse fuzzy date
        dt = date_parser.parse(cleaned, fuzzy=True)
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return None

def format_date_display(iso_date: str) -> str:
    """Format YYYY-MM-DD into DD-MMM-YYYY (e.g. 15-Nov-2026)."""
    if not iso_date:
        return ""
    try:
        dt = datetime.strptime(iso_date, "%Y-%m-%d")
        return dt.strftime("%d-%b-%Y")
    except Exception:
        return iso_date

def extract_deadline(text: str) -> Optional[str]:
    """Extract application deadline from text using regex and context matching."""
    if not text:
        return None

    for pattern in DEADLINE_PREFIX_PATTERNS:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            candidate = match.group(1).strip()
            # Verify candidate contains a month name or digit
            has_month = any(m in candidate.lower() for m in MONTH_NAMES)
            has_digit = any(c.isdigit() for c in candidate)
            if has_month or has_digit:
                parsed = parse_date_to_iso(candidate)
                if parsed:
                    return parsed

    return None

def calculate_days_remaining(deadline_iso: Optional[str], reference_date: Optional[date] = None) -> Optional[int]:
    """Calculate integer days remaining until deadline."""
    if not deadline_iso:
        return None

    try:
        target = datetime.strptime(deadline_iso, "%Y-%m-%d").date()
        ref = reference_date or date.today()
        diff = (target - ref).days
        return diff
    except Exception:
        return None
