"""Deduplication and change detection algorithms for GSEIM."""

import hashlib
import re
from gseim.parsers.text_cleaner import canonicalize_url

def normalize_title(title: str) -> str:
    """Normalize title for fuzzy collision avoidance."""
    if not title:
        return ""
    t = re.sub(r"[^\w\s]", "", title.lower())
    return re.sub(r"\s+", " ", t).strip()

def generate_composite_key(organization: str, title: str, url: str) -> str:
    """
    Generate SHA256 key from canonical URL, normalized title, and organization.
    Ensures identical opportunities from the same entity are deduplicated.
    """
    clean_url = canonicalize_url(url)
    clean_t = normalize_title(title)
    clean_org = organization.strip().lower()

    raw_key = f"{clean_org}|{clean_t}|{clean_url}"
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

def generate_content_hash(*content_fields: str) -> str:
    """
    Generate SHA256 hash of core content fields to detect content updates.
    If summary, deadline, or requirements change, hash changes.
    """
    combined = "|".join((field or "").strip().lower() for field in content_fields)
    return hashlib.sha256(combined.encode("utf-8")).hexdigest()
