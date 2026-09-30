"""Text and URL normalization utilities for GSEIM."""

import re
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode

TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term",
    "utm_content", "fbclid", "gclid", "ref", "source", "mc_cid", "mc_eid"
}

def clean_text(text: str) -> str:
    """Strip HTML tags, extraneous whitespace, and clean unicode artifacts."""
    if not text:
        return ""
    # Strip HTML tags
    cleaned = re.sub(r"<[^>]+>", " ", text)
    # Normalize spaces
    cleaned = re.sub(r"[\r\n\t]+", " ", cleaned)
    cleaned = re.sub(r"\s{2,}", " ", cleaned)
    return cleaned.strip()

def canonicalize_url(url: str) -> str:
    """Normalize URL by stripping tracking parameters, fragments, and standardizing casing."""
    if not url:
        return ""
    try:
        parsed = urlparse(url.strip())
        # Clean query parameters
        query_pairs = parse_qsl(parsed.query)
        cleaned_pairs = [(k, v) for k, v in query_pairs if k.lower() not in TRACKING_PARAMS]
        clean_query = urlencode(cleaned_pairs)

        # Standardize path
        path = parsed.path
        if path.endswith("/") and len(path) > 1:
            path = path[:-1]

        canonical = urlunparse((
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            path,
            "",  # params
            clean_query,
            ""   # fragment
        ))
        return canonical
    except Exception:
        return url.strip()
