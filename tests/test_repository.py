"""Integration tests for SQLite repository and deduplication."""

import tempfile
import os
import gc
import pytest
from gseim.database.repository import GSEIMRepository

@pytest.fixture
def temp_repo():
    fd, path = tempfile.mkstemp(suffix=".sqlite3")
    os.close(fd)
    repo = GSEIMRepository(db_path=path)
    yield repo
    del repo
    gc.collect()
    try:
        if os.path.exists(path):
            os.remove(path)
    except PermissionError:
        pass

def test_opportunity_lifecycle_and_history(temp_repo):
    opp_v1 = {
        "organization": "Test Accelerator",
        "country": "India",
        "region": "South Asia",
        "type": "Accelerator",
        "opportunity": "Fall 2026 Batch",
        "sector": "DeepTech",
        "startup_stage": "Seed",
        "eligibility": "Incorporated startups",
        "application_status": "Open",
        "deadline": "15-Oct-2026",
        "deadline_iso": "2026-10-15",
        "days_remaining": 16,
        "source_url": "https://test.com/apply",
        "source_type": "Official Website",
        "relevance_score": 14,
        "summary": "Join our 3-month cohort."
    }

    # 1. First insert -> NEW
    action, opp_id = temp_repo.save_opportunity(opp_v1)
    assert action == "NEW"
    assert opp_id.startswith("OPP-")

    # 2. Identical insert -> UNCHANGED
    action2, opp_id2 = temp_repo.save_opportunity(opp_v1)
    assert action2 == "UNCHANGED"
    assert opp_id2 == opp_id

    # 3. Content update -> UPDATED
    opp_v2 = dict(opp_v1)
    opp_v2["deadline"] = "30-Oct-2026"
    opp_v2["deadline_iso"] = "2026-10-30"
    opp_v2["summary"] = "Join our 3-month cohort. Funding increased to $100k."

    action3, opp_id3 = temp_repo.save_opportunity(opp_v2)
    assert action3 == "UPDATED"
    assert opp_id3 == opp_id

    # Verify history table recorded the change
    history = temp_repo.get_history()
    assert len(history) == 1
    assert history[0]["entity_id"] == opp_id
    assert history[0]["change_type"] == "Content Update"

def test_job_lifecycle(temp_repo):
    job_v1 = {
        "organization": "Innovation Lab",
        "country": "UK",
        "region": "Europe",
        "job_title": "Incubation Manager",
        "function": "Incubation",
        "seniority": "Mid-Senior",
        "employment": "Full-time",
        "location": "London",
        "remote": "Hybrid",
        "salary": "£50,000",
        "closing_date": "20-Oct-2026",
        "closing_iso": "2026-10-20",
        "days_remaining": 21,
        "job_url": "https://test.com/job/123",
        "source": "ATS_LEVER",
        "relevance_score": 16,
        "summary": "Manage incubator operations."
    }

    action, job_id = temp_repo.save_job(job_v1)
    assert action == "NEW"
    assert job_id.startswith("JOB-")

    action2, job_id2 = temp_repo.save_job(job_v1)
    assert action2 == "UNCHANGED"
    assert job_id2 == job_id

def test_deadlines_retrieval(temp_repo):
    opp = {
        "organization": "Gov Grant",
        "country": "USA",
        "region": "North America",
        "type": "Grant",
        "opportunity": "Seed Grant 2026",
        "deadline": "10-Oct-2026",
        "deadline_iso": "2026-10-10",
        "days_remaining": 11,
        "source_url": "https://gov.com/grant",
        "relevance_score": 15,
        "summary": "Non-dilutive grant."
    }
    temp_repo.save_opportunity(opp)

    deadlines = temp_repo.get_deadlines()
    assert len(deadlines) >= 1
    assert deadlines[0]["opportunity"] == "Seed Grant 2026"
    assert deadlines[0]["days_remaining"] == 11
