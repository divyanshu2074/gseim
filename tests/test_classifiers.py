"""Unit tests for deterministic opportunity and job classifiers."""

import pytest
from gseim.classifiers.opportunity_classifier import (
    classify_opportunity, calculate_opportunity_score, detect_category, detect_sector
)
from gseim.classifiers.job_classifier import (
    classify_job, calculate_job_score, detect_job_function
)
from gseim.classifiers.relevance import evaluate_item_relevance

def test_opportunity_classifier_positive():
    item = {
        "title": "Call for Applications: 2027 ClimateTech Seed Accelerator Cohort",
        "summary": "We are offering equity-free grants up to $100k and 6 months mentorship for early stage startups. Applications close 15 November 2026.",
        "content_preview": "Startups incorporated in Singapore or Southeast Asia working on carbon capture and renewable energy.",
        "url": "https://example.com/apply-2027",
        "organization": "ABC Climate Hub",
        "country": "Singapore",
        "region": "Southeast Asia",
        "collection_method": "RSS"
    }

    opp = classify_opportunity(item)
    assert opp is not None
    assert opp["type"] in ["Accelerator", "Grant"]
    assert opp["sector"] == "ClimateTech"
    assert opp["relevance_score"] >= 12
    assert "ABC Climate Hub" in opp["organization"]
    assert opp["deadline"] != ""

def test_opportunity_negative_filtering():
    # Should be rejected due to negative filter
    disqualified_item = {
        "title": "High school student essay competition with promotional offer",
        "summary": "Submit your essay to win consumer discount coupons.",
        "content_preview": "Open to high school students.",
        "url": "https://example.com/essay",
        "organization": "Consumer Deals"
    }
    score = calculate_opportunity_score(disqualified_item["title"], disqualified_item["summary"])
    assert score < 0
    assert classify_opportunity(disqualified_item) is None

def test_job_classifier_positive():
    job_item = {
        "title": "Senior Program Manager – Startup Accelerator",
        "summary": "Looking for an incubation and cohort manager to lead our deeptech founder programs.",
        "content_preview": "Manage deal flow, founder relations, and mentorship networks in London. Salary: £55,000–£65,000.",
        "url": "https://jobs.lever.co/example/123",
        "organization": "Techstars UK",
        "country": "UK",
        "region": "Europe",
        "collection_method": "ATS_LEVER"
    }

    job = classify_job(job_item)
    assert job is not None
    assert job["function"] in ["Acceleration", "Incubation"]
    assert job["seniority"] in ["Senior", "Lead / Principal"]
    assert "£" in job["salary"]
    assert job["relevance_score"] >= 14

def test_job_classifier_negative():
    # Software Engineer at a startup should NOT be classified as an ecosystem management job
    tech_job = {
        "title": "Senior Software Engineer – Python / React",
        "summary": "Join our fast-growing startup to build backend microservices and databases.",
        "content_preview": "Experience with AWS and Kubernetes required.",
        "url": "https://example.com/jobs/dev",
        "organization": "Cool Startup",
        "collection_method": "HTML"
    }

    score = calculate_job_score(tech_job["title"], tech_job["summary"])
    assert score <= 0
    assert classify_job(tech_job) is None

def test_evaluate_item_relevance_routing():
    # Test routing to job
    job_item = {
        "title": "Incubation Manager",
        "summary": "Lead our technology business incubator programs.",
        "url": "https://example.com/careers/incubation-mgr",
        "organization": "IIT Incubator"
    }
    kind, res = evaluate_item_relevance(job_item)
    assert kind == "job"
    assert res["job_title"] == "Incubation Manager"

    # Test routing to opportunity
    opp_item = {
        "title": "DST Seed Support Call for Proposals 2026",
        "summary": "Grant funding opportunity for deeptech startups. Applications open.",
        "url": "https://dst.gov.in/proposals",
        "organization": "DST India"
    }
    kind, res = evaluate_item_relevance(opp_item)
    assert kind == "opportunity"
    assert res["type"] == "Grant"
