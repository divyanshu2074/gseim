"""Unit tests for date and deadline parser."""

from datetime import date
from gseim.parsers.date_parser import (
    extract_deadline, parse_date_to_iso, calculate_days_remaining, format_date_display
)

def test_parse_date_to_iso():
    assert parse_date_to_iso("25 September 2026") == "2026-09-25"
    assert parse_date_to_iso("15-Nov-2026") == "2026-11-15"
    assert parse_date_to_iso("2026-10-20") == "2026-10-20"
    assert parse_date_to_iso("1st October 2026") == "2026-10-01"

def test_extract_deadline_patterns():
    snippet_1 = "The cohort begins in December. Applications close: 15 October 2026. Submit now."
    assert extract_deadline(snippet_1) == "2026-10-15"

    snippet_2 = "Apply by 30-Nov-2026 for seed funding."
    assert extract_deadline(snippet_2) == "2026-11-30"

    snippet_3 = "Submission deadline is 12/10/2026. Late submissions will be rejected."
    assert extract_deadline(snippet_3) in ["2026-10-12", "2026-12-10"]

def test_calculate_days_remaining():
    ref_date = date(2026, 9, 29)
    # Deadline on 5 Oct 2026 -> 6 days remaining
    days = calculate_days_remaining("2026-10-05", reference_date=ref_date)
    assert days == 6

    # Deadline in past
    days_past = calculate_days_remaining("2026-09-20", reference_date=ref_date)
    assert days_past == -9

def test_format_date_display():
    assert format_date_display("2026-11-15") == "15-Nov-2026"
    assert format_date_display("2026-10-05") == "05-Oct-2026"
