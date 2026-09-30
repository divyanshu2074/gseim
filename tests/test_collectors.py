"""Unit tests for collectors with mocked networking."""

from unittest.mock import MagicMock, patch
import pytest
from gseim.collectors.rss import RSSCollector
from gseim.collectors.sitemap import SitemapCollector
from gseim.collectors.html import HTMLCollector
from gseim.collectors.ats import ATSCollector

SAMPLE_RSS_XML = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Startup Hub RSS</title>
    <link>https://example.com</link>
    <description>Ecosystem Updates</description>
    <item>
      <title>Call for Applications: DeepTech Seed Cohort 2027</title>
      <link>https://example.com/cohort-2027</link>
      <description>Applications open for seed deeptech startups. Up to $100k non-dilutive grant.</description>
      <pubDate>Mon, 29 Sep 2026 10:00:00 GMT</pubDate>
    </item>
  </channel>
</rss>
"""

SAMPLE_HTML = """
<!DOCTYPE html>
<html>
<head><title>Programs &amp; Grants</title></head>
<body>
  <div class="card program-card">
    <h3><a href="/program/ai-accelerator">2027 AI Innovation Accelerator</a></h3>
    <p>Join our 4-month accelerator. Equity-free funding and mentorship. Deadline: 20-Nov-2026.</p>
    <time datetime="2026-09-29">29-Sep-2026</time>
  </div>
</body>
</html>
"""

def test_rss_collector_mocked():
    collector = RSSCollector()
    mock_resp = MagicMock()
    mock_resp.text = SAMPLE_RSS_XML
    mock_resp.status_code = 200

    with patch.object(collector, "fetch", return_value=mock_resp):
        source = {
            "source_id": "TEST-001",
            "organization": "Test Hub",
            "country": "USA",
            "region": "North America",
            "category": "Accelerator",
            "rss": "https://example.com/feed.xml"
        }
        items = collector.collect(source)
        assert len(items) == 1
        assert "DeepTech Seed Cohort 2027" in items[0]["title"]
        assert items[0]["collection_method"] == "RSS"

def test_html_collector_mocked():
    collector = HTMLCollector()
    mock_resp = MagicMock()
    mock_resp.text = SAMPLE_HTML
    mock_resp.status_code = 200

    with patch.object(collector, "fetch", return_value=mock_resp):
        source = {
            "source_id": "TEST-002",
            "organization": "Test Agency",
            "country": "India",
            "region": "South Asia",
            "category": "Government",
            "opportunities_page": "https://example.com/programs"
        }
        items = collector.collect(source)
        assert len(items) >= 1
        assert any("2027 AI Innovation Accelerator" in i["title"] for i in items)

def test_ats_platform_identification():
    collector = ATSCollector()
    assert collector.identify_ats("https://jobs.lever.co/techstars") == "lever"
    assert collector.identify_ats("https://boards.greenhouse.io/masschallenge") == "greenhouse"
    assert collector.identify_ats("https://jobs.ashbyhq.com/entrepreneur-first") == "ashby"
    assert collector.identify_ats("https://example.com/careers") is None
