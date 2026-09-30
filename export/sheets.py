"""Google Sheets exporter and live sync engine for GSEIM."""

import os
import logging
from typing import Optional, Dict, Any, List
import pandas as pd

from gseim.config.settings import SPREADSHEET_TITLE, SHEET_TABS
from gseim.export.dashboard import generate_dashboard_metrics, build_dashboard_dataframe
from gseim.export.excel_mirror import get_keywords_dataframe

logger = logging.getLogger("gseim.export.sheets")

class GoogleSheetsExporter:
    """Synchronizes SQLite database intelligence with a 10-tab Google Sheet."""

    def __init__(self, credentials_path: Optional[str] = None):
        self.credentials_path = credentials_path or os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        self.client = None
        self._authenticate()

    def _authenticate(self):
        """Authenticate via service account file or Google Colab user auth."""
        try:
            import gspread
            # Check if running in Google Colab with interactive auth
            try:
                from google.colab import auth
                from google.auth import default
                auth.authenticate_user()
                creds, _ = default()
                self.client = gspread.authorize(creds)
                logger.info("Successfully authenticated via Google Colab OAuth.")
                return
            except ImportError:
                pass

            # Check Service Account JSON
            if self.credentials_path and os.path.exists(self.credentials_path):
                self.client = gspread.service_account(filename=self.credentials_path)
                logger.info(f"Successfully authenticated via Service Account: {self.credentials_path}")
            else:
                logger.warning("No Google credentials provided. Offline Excel mirror will be used.")
        except Exception as e:
            logger.warning(f"Google Sheets authentication notice: {e}")
            self.client = None

    def is_connected(self) -> bool:
        return self.client is not None

    def get_or_create_spreadsheet(self, title: str = SPREADSHEET_TITLE):
        """Find existing workbook or create a new one."""
        if not self.client:
            raise RuntimeError("Google Sheets client is not authenticated.")

        try:
            spreadsheet = self.client.open(title)
            logger.info(f"Opened existing Google Sheet: {title}")
        except Exception:
            spreadsheet = self.client.create(title)
            logger.info(f"Created new Google Sheet: {title}")

        # Ensure all 10 tabs exist
        existing_sheet_names = [ws.title for ws in spreadsheet.worksheets()]
        for tab_name in SHEET_TABS:
            if tab_name not in existing_sheet_names:
                spreadsheet.add_worksheet(title=tab_name, rows=500, cols=20)
                logger.info(f"Created worksheet tab: {tab_name}")

        return spreadsheet

    def sync(self, repo, spreadsheet_title: str = SPREADSHEET_TITLE) -> bool:
        """Push latest database records to all 10 Google Sheet tabs."""
        if not self.is_connected():
            logger.info("Google Sheets not connected; skipping cloud sync. Excel mirror generated.")
            return False

        try:
            sh = self.get_or_create_spreadsheet(spreadsheet_title)

            # 1. Dashboard
            metrics = generate_dashboard_metrics(repo)
            df_dash = build_dashboard_dataframe(metrics)
            self._write_worksheet(sh, "Dashboard", df_dash.values.tolist())

            # 2. New Opportunities
            opps = repo.get_opportunities()
            opp_headers = [
                "ID", "First Seen", "Organization", "Country", "Region", "Type",
                "Opportunity", "Sector", "Startup Stage", "Eligibility",
                "Application Status", "Deadline", "Days Remaining", "Source URL",
                "Source Type", "Last Checked", "Status", "Relevance Score"
            ]
            opp_rows = [[
                o.get("id"), o.get("first_seen"), o.get("organization"), o.get("country"),
                o.get("region"), o.get("type"), o.get("opportunity"), o.get("sector"),
                o.get("startup_stage"), o.get("eligibility"), o.get("application_status"),
                o.get("deadline"), o.get("days_remaining"), o.get("source_url"),
                o.get("source_type"), o.get("last_checked"), o.get("status"), o.get("relevance_score")
            ] for o in opps]
            self._write_worksheet(sh, "New Opportunities", [opp_headers] + opp_rows)

            # 3. Jobs
            jobs = repo.get_jobs()
            job_headers = [
                "Job ID", "First Seen", "Organization", "Country", "Job Title",
                "Function", "Seniority", "Employment", "Location", "Remote",
                "Salary", "Closing Date", "Job URL", "Source", "Relevance Score", "Status"
            ]
            job_rows = [[
                j.get("job_id"), j.get("first_seen"), j.get("organization"), j.get("country"),
                j.get("job_title"), j.get("function"), j.get("seniority"), j.get("employment"),
                j.get("location"), j.get("remote"), j.get("salary"), j.get("closing_date"),
                j.get("job_url"), j.get("source"), j.get("relevance_score"), j.get("status")
            ] for j in jobs]
            self._write_worksheet(sh, "Jobs", [job_headers] + job_rows)

            # 4. Ecosystem Updates
            updates = repo.get_ecosystem_updates()
            upd_headers = ["Date", "Organization", "Country", "Category", "Title", "Summary", "URL"]
            upd_rows = [[u.get("date"), u.get("organization"), u.get("country"), u.get("category"), u.get("title"), u.get("summary"), u.get("url")] for u in updates]
            self._write_worksheet(sh, "Ecosystem Updates", [upd_headers] + upd_rows)

            # 5. Deadlines
            deadlines = repo.get_deadlines()
            dl_headers = ["Opportunity", "Organization", "Type", "Deadline", "Days Remaining", "URL"]
            dl_rows = [[d.get("opportunity"), d.get("organization"), d.get("type"), d.get("deadline"), d.get("days_remaining"), d.get("url")] for d in deadlines]
            self._write_worksheet(sh, "Deadlines", [dl_headers] + dl_rows)

            # 6. Sources
            sources = repo.get_all_sources()
            src_headers = list(sources[0].keys()) if sources else []
            src_rows = [[s.get(k) for k in src_headers] for s in sources]
            self._write_worksheet(sh, "Sources", [src_headers] + src_rows)

            # 7. Keywords
            df_kws = get_keywords_dataframe()
            self._write_worksheet(sh, "Keywords", [df_kws.columns.tolist()] + df_kws.values.tolist())

            # 8. Organizations
            orgs = repo.get_organizations()
            org_headers = list(orgs[0].keys()) if orgs else []
            org_rows = [[o.get(k) for k in org_headers] for o in orgs]
            self._write_worksheet(sh, "Organizations", [org_headers] + org_rows)

            # 9. History
            hist = repo.get_history()
            hist_headers = list(hist[0].keys()) if hist else ["ID", "Entity Type", "Entity ID", "Changed At", "Change Type", "Old Value", "New Value"]
            hist_rows = [[h.get(k) for k in hist_headers] for h in hist]
            self._write_worksheet(sh, "History", [hist_headers] + hist_rows)

            # 10. Run Logs
            logs = repo.get_run_logs()
            log_headers = list(logs[0].keys()) if logs else ["Run ID", "Timestamp", "Duration", "Total Sources", "Success", "Failed"]
            log_rows = [[l.get(k) for k in log_headers] for l in logs]
            self._write_worksheet(sh, "Run Logs", [log_headers] + log_rows)

            logger.info("Successfully synced all 10 tabs to Google Sheets.")
            return True
        except Exception as e:
            logger.error(f"Error during Google Sheets synchronization: {e}")
            return False

    def _write_worksheet(self, spreadsheet, tab_name: str, values: List[List[Any]]):
        """Helper to clear and populate a worksheet tab safely."""
        try:
            ws = spreadsheet.worksheet(tab_name)
            ws.clear()
            if values:
                # Sanitize None values to empty strings
                sanitized = [[str(v) if v is not None else "" for v in row] for row in values]
                ws.update("A1", sanitized)
        except Exception as e:
            logger.warning(f"Failed to update sheet tab {tab_name}: {e}")
