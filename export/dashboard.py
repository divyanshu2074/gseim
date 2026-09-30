"""Dashboard calculations and run report generator for GSEIM."""

from datetime import datetime, date
from typing import Dict, Any, List
from collections import Counter
import pandas as pd

def generate_dashboard_metrics(repo) -> Dict[str, Any]:
    """Calculate aggregated metrics across all tables for the Dashboard tab."""
    opps = repo.get_opportunities()
    jobs = repo.get_jobs()
    updates = repo.get_ecosystem_updates()
    deadlines = repo.get_deadlines()
    sources = repo.get_all_sources()

    today_str = date.today().strftime("%d-%m-%Y")

    # Today's counts
    new_opps_today = sum(1 for o in opps if o.get("first_seen") == today_str and o.get("status") == "New")
    updated_opps_today = sum(1 for o in opps if o.get("status") == "Updated")
    new_jobs_today = sum(1 for j in jobs if j.get("first_seen") == today_str and j.get("status") == "New")
    updates_today = sum(1 for u in updates if u.get("date") == today_str)

    # Deadlines breakdown
    closing_7_days = sum(1 for d in deadlines if d.get("days_remaining") is not None and 0 <= d["days_remaining"] <= 7)
    closing_30_days = sum(1 for d in deadlines if d.get("days_remaining") is not None and 0 <= d["days_remaining"] <= 30)

    # Breakdown by Country
    all_countries = [o.get("country") for o in opps if o.get("country")] + [j.get("country") for j in jobs if j.get("country")]
    country_counts = Counter(all_countries).most_common(12)

    # Category breakdown (Opportunities)
    opp_categories = Counter([o.get("type", "Other") for o in opps]).most_common(8)

    # Job functions breakdown
    job_functions = Counter([j.get("function", "Other") for j in jobs]).most_common(8)

    # Sources health
    total_sources = len(sources)
    active_sources = sum(1 for s in sources if s.get("active"))
    success_sources = sum(1 for s in sources if s.get("status") == "Success")
    failed_sources = sum(1 for s in sources if s.get("status") == "Failed")

    return {
        "today_str": today_str,
        "new_opps_today": new_opps_today,
        "updated_opps_today": updated_opps_today,
        "new_jobs_today": new_jobs_today,
        "updates_today": updates_today,
        "total_opps": len(opps),
        "total_jobs": len(jobs),
        "closing_7_days": closing_7_days,
        "closing_30_days": closing_30_days,
        "country_counts": country_counts,
        "opp_categories": opp_categories,
        "job_functions": job_functions,
        "total_sources": total_sources,
        "active_sources": active_sources,
        "success_sources": success_sources,
        "failed_sources": failed_sources
    }

def build_dashboard_dataframe(metrics: Dict[str, Any]) -> pd.DataFrame:
    """Construct formatted 2D table representing the executive Dashboard sheet."""
    rows = [
        ["GLOBAL STARTUP ECOSYSTEM MONITOR - DASHBOARD", "", "", ""],
        ["Generated", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "", ""],
        ["", "", "", ""],
        ["METRIC", "VALUE", "SECTION", "DETAILS"],
        ["New Opportunities (Today)", metrics["new_opps_today"], "Summary", "Filtered by >8 relevance score"],
        ["Updated Opportunities", metrics["updated_opps_today"], "Summary", "Detected via content hash changes"],
        ["New Ecosystem Jobs (Today)", metrics["new_jobs_today"], "Summary", "Filtered by >10 role relevance score"],
        ["Ecosystem Announcements", metrics["updates_today"], "Summary", "Funds, centres of excellence, policies"],
        ["Total Tracked Opportunities", metrics["total_opps"], "Database", "Active & Historical"],
        ["Total Tracked Jobs", metrics["total_jobs"], "Database", "Active & Historical"],
        ["", "", "", ""],
        ["DEADLINE HORIZON", "OPPORTUNITIES", "", ""],
        ["Closing within 7 days", metrics["closing_7_days"], "Urgent", "Prioritize application review"],
        ["Closing within 30 days", metrics["closing_30_days"], "Medium", "Review cohorts and deadlines"],
        ["", "", "", ""],
        ["SOURCE HEALTH", "COUNT", "", ""],
        ["Total Registered Sources", metrics["total_sources"], "Sources", "Curated global registry"],
        ["Active Sources Monitored", metrics["active_sources"], "Sources", "Scheduled for continuous crawl"],
        ["Successful in Last Run", metrics["success_sources"], "Sources", "200 OK responses parsed"],
        ["Failed in Last Run", metrics["failed_sources"], "Sources", "Network timeouts or robots exclusions"],
        ["", "", "", ""],
        ["TOP COUNTRIES", "COUNT", "OPPORTUNITY TYPES", "COUNT"]
    ]

    max_len = max(len(metrics["country_counts"]), len(metrics["opp_categories"]))
    for i in range(max_len):
        country_name, c_cnt = metrics["country_counts"][i] if i < len(metrics["country_counts"]) else ("", "")
        cat_name, cat_cnt = metrics["opp_categories"][i] if i < len(metrics["opp_categories"]) else ("", "")
        rows.append([country_name, c_cnt, cat_name, cat_cnt])

    return pd.DataFrame(rows)

def format_run_report(metrics: Dict[str, Any], duration: float = 0.0) -> str:
    """Generate exact ASCII terminal run summary report."""
    date_header = datetime.now().strftime("%d %B %Y")
    lines = [
        "=====================================",
        "GLOBAL ECOSYSTEM MONITOR",
        f"{date_header}",
        "=====================================",
        "Sources:",
        f"  Total: {metrics['total_sources']}",
        f"  Successful: {metrics['success_sources']}",
        f"  Failed: {metrics['failed_sources']}",
        "",
        "Results:",
        f"  New opportunities: {metrics['new_opps_today']}",
        f"  Updated opportunities: {metrics['updated_opps_today']}",
        f"  New jobs: {metrics['new_jobs_today']}",
        f"  Ecosystem updates: {metrics['updates_today']}",
        "",
        "Categories:"
    ]
    for cat, cnt in metrics["opp_categories"][:6]:
        lines.append(f"  {cat}: {cnt}")

    lines.append("")
    lines.append("Jobs:")
    for fn, cnt in metrics["job_functions"][:6]:
        lines.append(f"  {fn}: {cnt}")

    lines.append("")
    lines.append("Deadlines:")
    lines.append(f"  Closing within 7 days: {metrics['closing_7_days']}")
    lines.append(f"  Closing within 30 days: {metrics['closing_30_days']}")
    if duration > 0:
        lines.append(f"Execution Time: {duration:.2f}s")
    lines.append("=====================================")

    return "\n".join(lines)
