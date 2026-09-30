"""Excel (.xlsx) exporter creating an identical multi-tab mirror of the Google Sheet."""

import logging
from pathlib import Path
from typing import Optional
import pandas as pd

from gseim.config.settings import EXCEL_OUTPUT_PATH
from gseim.config.keywords import (
    CATEGORY_KEYWORDS, OPPORTUNITY_WEIGHTS, JOB_FUNCTIONS, JOB_WEIGHTS,
    EXCLUDE_JOBS, EXCLUDE_OPPORTUNITIES
)
from gseim.export.dashboard import generate_dashboard_metrics, build_dashboard_dataframe

logger = logging.getLogger("gseim.export.excel")

def get_keywords_dataframe() -> pd.DataFrame:
    """Build reference DataFrame for the Keywords tab."""
    rows = []
    for cat, kws in CATEGORY_KEYWORDS.items():
        rows.append({"Type": "Opportunity Category", "Category/Function": cat, "Keywords": ", ".join(kws), "Weight": "Categorical"})
    for fn, kws in JOB_FUNCTIONS.items():
        rows.append({"Type": "Job Function", "Category/Function": fn, "Keywords": ", ".join(kws), "Weight": "Functional"})
    for term, w in OPPORTUNITY_WEIGHTS.items():
        rows.append({"Type": "Opportunity Scoring Weight", "Category/Function": "Weight", "Keywords": term, "Weight": f"+{w}"})
    for term, w in JOB_WEIGHTS.items():
        rows.append({"Type": "Job Scoring Weight", "Category/Function": "Weight", "Keywords": term, "Weight": f"+{w}"})
    for excl in EXCLUDE_JOBS:
        rows.append({"Type": "Negative Filter (Job)", "Category/Function": "Exclusion", "Keywords": excl, "Weight": "-10 / Disqualify"})
    for excl in EXCLUDE_OPPORTUNITIES:
        rows.append({"Type": "Negative Filter (Opportunity)", "Category/Function": "Exclusion", "Keywords": excl, "Weight": "-10 / Disqualify"})
    return pd.DataFrame(rows)

def export_to_excel(repo, output_path: str = EXCEL_OUTPUT_PATH) -> str:
    """Generate multi-tab Excel workbook matching the 10-tab GSEIM Google Sheet schema."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    logger.info(f"Generating Excel mirror workbook at: {output_path}")

    # 1. Dashboard Tab
    metrics = generate_dashboard_metrics(repo)
    df_dashboard = build_dashboard_dataframe(metrics)

    # 2. New Opportunities Tab
    opps = repo.get_opportunities()
    opp_records = []
    for o in opps:
        opp_records.append({
            "ID": o.get("id"),
            "First Seen": o.get("first_seen"),
            "Organization": o.get("organization"),
            "Country": o.get("country"),
            "Region": o.get("region"),
            "Type": o.get("type"),
            "Opportunity": o.get("opportunity"),
            "Sector": o.get("sector"),
            "Startup Stage": o.get("startup_stage"),
            "Eligibility": o.get("eligibility"),
            "Application Status": o.get("application_status"),
            "Deadline": o.get("deadline"),
            "Days Remaining": o.get("days_remaining"),
            "Source URL": o.get("source_url"),
            "Source Type": o.get("source_type"),
            "Last Checked": o.get("last_checked"),
            "Status": o.get("status"),
            "Relevance Score": o.get("relevance_score")
        })
    df_opps = pd.DataFrame(opp_records)

    # 3. Jobs Tab
    jobs = repo.get_jobs()
    job_records = []
    for j in jobs:
        job_records.append({
            "Job ID": j.get("job_id"),
            "First Seen": j.get("first_seen"),
            "Organization": j.get("organization"),
            "Country": j.get("country"),
            "Job Title": j.get("job_title"),
            "Function": j.get("function"),
            "Seniority": j.get("seniority"),
            "Employment": j.get("employment"),
            "Location": j.get("location"),
            "Remote": j.get("remote"),
            "Salary": j.get("salary"),
            "Closing Date": j.get("closing_date"),
            "Job URL": j.get("job_url"),
            "Source": j.get("source"),
            "Relevance Score": j.get("relevance_score"),
            "Status": j.get("status")
        })
    df_jobs = pd.DataFrame(job_records)

    # 4. Ecosystem Updates Tab
    updates = repo.get_ecosystem_updates()
    update_records = []
    for u in updates:
        update_records.append({
            "Date": u.get("date"),
            "Organization": u.get("organization"),
            "Country": u.get("country"),
            "Category": u.get("category"),
            "Title": u.get("title"),
            "Summary": u.get("summary"),
            "URL": u.get("url")
        })
    df_updates = pd.DataFrame(update_records)

    # 5. Deadlines Tab
    deadlines = repo.get_deadlines()
    df_deadlines = pd.DataFrame(deadlines)

    # 6. Sources Tab
    sources = repo.get_all_sources()
    df_sources = pd.DataFrame(sources)

    # 7. Keywords Tab
    df_keywords = get_keywords_dataframe()

    # 8. Organizations Tab
    orgs = repo.get_organizations()
    df_orgs = pd.DataFrame(orgs)

    # 9. History Tab
    history = repo.get_history()
    df_history = pd.DataFrame(history)

    # 10. Run Logs Tab
    run_logs = repo.get_run_logs()
    df_run_logs = pd.DataFrame(run_logs)

    # Write all sheets
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        df_dashboard.to_excel(writer, sheet_name="Dashboard", index=False, header=False)
        df_opps.to_excel(writer, sheet_name="New Opportunities", index=False)
        df_jobs.to_excel(writer, sheet_name="Jobs", index=False)
        df_updates.to_excel(writer, sheet_name="Ecosystem Updates", index=False)
        df_deadlines.to_excel(writer, sheet_name="Deadlines", index=False)
        df_sources.to_excel(writer, sheet_name="Sources", index=False)
        df_keywords.to_excel(writer, sheet_name="Keywords", index=False)
        df_orgs.to_excel(writer, sheet_name="Organizations", index=False)
        df_history.to_excel(writer, sheet_name="History", index=False)
        df_run_logs.to_excel(writer, sheet_name="Run Logs", index=False)

    logger.info(f"Excel workbook exported successfully: {output_path}")
    return output_path
