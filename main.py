"""Main GSEIM Orchestrator and CLI entry point."""

import sys
import os
import argparse
import time
import logging
from datetime import datetime
from typing import Dict, Any, List

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gseim.config.settings import (
    DB_PATH, SOURCES_SEED_PATH, EXCEL_OUTPUT_PATH, SPREADSHEET_TITLE
)
from gseim.database.repository import GSEIMRepository
from gseim.collectors.rss import RSSCollector
from gseim.collectors.sitemap import SitemapCollector
from gseim.collectors.html import HTMLCollector
from gseim.collectors.ats import ATSCollector
from gseim.classifiers.relevance import evaluate_item_relevance
from gseim.export.dashboard import generate_dashboard_metrics, format_run_report
from gseim.export.excel_mirror import export_to_excel
from gseim.export.sheets import GoogleSheetsExporter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("gseim.main")

class GSEIMOrchestrator:
    """End-to-end crawler, classifier, deduplicator, and export engine."""

    def __init__(self, db_path: str = DB_PATH, seed_path: str = SOURCES_SEED_PATH):
        self.repo = GSEIMRepository(db_path)
        self.repo.load_seed_sources(seed_path)

        # Initialize collectors
        self.rss_collector = RSSCollector()
        self.sitemap_collector = SitemapCollector()
        self.html_collector = HTMLCollector()
        self.ats_collector = ATSCollector()

    def run(
        self,
        sample: int = 0,
        method: str = "ALL",
        sync_sheets: bool = False,
        export_xlsx: bool = True
    ) -> Dict[str, Any]:
        """Execute full crawl, score, persist, and export cycle."""
        start_time = time.time()
        run_id = f"RUN-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        logger.info(f"Starting GSEIM Pipeline execution: {run_id}")

        sources = self.repo.get_active_sources()
        if method != "ALL":
            sources = [s for s in sources if s.get("monitoring_method", "").upper() == method.upper()]

        if sample > 0:
            sources = sources[:sample]

        logger.info(f"Targeting {len(sources)} active sources for collection.")

        pages_scanned = 0
        new_opps = 0
        updated_opps = 0
        new_jobs = 0
        updates_count = 0
        successful_sources = 0
        failed_sources = 0
        error_messages = []

        for src in sources:
            src_id = src.get("source_id")
            src_name = src.get("organization")
            src_method = (src.get("monitoring_method") or "HTML").upper()
            logger.info(f"Processing [{src_method}] {src_id} - {src_name}")

            raw_items = []
            try:
                if src_method == "RSS":
                    raw_items = self.rss_collector.collect(src)
                elif src_method == "SITEMAP":
                    raw_items = self.sitemap_collector.collect(src)
                elif src_method == "ATS":
                    raw_items = self.ats_collector.collect(src)
                else:
                    raw_items = self.html_collector.collect(src)

                pages_scanned += max(1, len(raw_items))
                self.repo.update_source_crawl_status(src_id, success=True)
                successful_sources += 1
            except Exception as e:
                logger.error(f"Error crawling {src_id} ({src_name}): {e}")
                self.repo.update_source_crawl_status(src_id, success=False, error_msg=str(e))
                failed_sources += 1
                error_messages.append(f"{src_id}: {str(e)[:100]}")
                continue

            # Classify & Deduplicate items
            for item in raw_items:
                item_type, classified = evaluate_item_relevance(item)
                if not item_type or not classified:
                    continue

                if item_type == "opportunity":
                    action, opp_id = self.repo.save_opportunity(classified)
                    if action == "NEW":
                        new_opps += 1
                    elif action == "UPDATED":
                        updated_opps += 1
                elif item_type == "job":
                    action, job_id = self.repo.save_job(classified)
                    if action == "NEW":
                        new_jobs += 1
                elif item_type == "update":
                    action, upd_id = self.repo.save_ecosystem_update(classified)
                    if action == "NEW":
                        updates_count += 1

        duration = time.time() - start_time

        # Save run log
        run_metrics = {
            "run_id": run_id,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "duration_seconds": round(duration, 2),
            "sources_total": len(sources),
            "sources_successful": successful_sources,
            "sources_failed": failed_sources,
            "pages_scanned": pages_scanned,
            "new_opportunities": new_opps,
            "updated_opportunities": updated_opps,
            "new_jobs": new_jobs,
            "ecosystem_updates": updates_count,
            "error_summary": "; ".join(error_messages[:5])
        }
        self.repo.log_run(run_metrics)

        # Multi-tab Excel Export
        if export_xlsx:
            export_to_excel(self.repo, EXCEL_OUTPUT_PATH)

        # Google Sheets Synchronization
        if sync_sheets:
            exporter = GoogleSheetsExporter()
            if exporter.is_connected():
                exporter.sync(self.repo, SPREADSHEET_TITLE)
            else:
                logger.info("Google Sheets credentials not found. Results saved to Excel mirror.")

        # Terminal Run Summary Report
        metrics = generate_dashboard_metrics(self.repo)
        report = format_run_report(metrics, duration)
        print("\n" + report + "\n")

        return run_metrics

def main():
    parser = argparse.ArgumentParser(description="Global Startup Ecosystem Intelligence Monitor (GSEIM)")
    parser.add_argument("--sample", type=int, default=0, help="Run a sample of N sources (default: 0 for all)")
    parser.add_argument("--method", type=str, default="ALL", choices=["ALL", "RSS", "SITEMAP", "HTML", "ATS"], help="Filter sources by method")
    parser.add_argument("--sync-sheets", action="store_true", help="Synchronize live to Google Sheets")
    parser.add_argument("--no-excel", action="store_true", help="Disable Excel mirror export")
    parser.add_argument("--db", type=str, default=DB_PATH, help="Path to SQLite database")

    args = parser.parse_args()

    orchestrator = GSEIMOrchestrator(db_path=args.db)
    orchestrator.run(
        sample=args.sample,
        method=args.method,
        sync_sheets=args.sync_sheets,
        export_xlsx=not args.no_excel
    )

if __name__ == "__main__":
    main()
