"""SQLite repository and persistence layer for GSEIM."""

import sqlite3
import json
import logging
from datetime import datetime, date
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

from gseim.database.models import CREATE_TABLES_SQL
from gseim.database.deduplication import generate_composite_key, generate_content_hash
from gseim.config.settings import DB_PATH, SOURCES_SEED_PATH

logger = logging.getLogger("gseim.database")

class GSEIMRepository:
    """Manages SQLite database connections, schema migrations, and deduplication logic."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        """Create a sqlite3 connection with row factory enabled."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        """Execute table creation and indices."""
        with self.get_connection() as conn:
            conn.executescript(CREATE_TABLES_SQL)
            conn.commit()

    def load_seed_sources(self, seed_path: str = SOURCES_SEED_PATH) -> int:
        """Seed sources table from JSON file if empty or missing records."""
        if not Path(seed_path).exists():
            logger.warning(f"Seed file not found: {seed_path}")
            return 0

        with open(seed_path, "r", encoding="utf-8") as f:
            sources_data = json.load(f)

        count = 0
        with self.get_connection() as conn:
            cursor = conn.cursor()
            for src in sources_data:
                cursor.execute("""
                    INSERT INTO sources (
                        source_id, organization, country, region, category,
                        website, opportunities_page, jobs_page, rss, sitemap,
                        monitoring_method, frequency, active, status, failure_count
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Active', 0)
                    ON CONFLICT(source_id) DO UPDATE SET
                        website=excluded.website,
                        opportunities_page=excluded.opportunities_page,
                        jobs_page=excluded.jobs_page,
                        rss=excluded.rss,
                        sitemap=excluded.sitemap,
                        monitoring_method=excluded.monitoring_method
                """, (
                    src.get("source_id"),
                    src.get("organization"),
                    src.get("country"),
                    src.get("region"),
                    src.get("category"),
                    src.get("website"),
                    src.get("opportunities_page"),
                    src.get("jobs_page"),
                    src.get("rss"),
                    src.get("sitemap"),
                    src.get("monitoring_method", "HTML"),
                    src.get("frequency", "Daily"),
                    1 if src.get("active", True) else 0
                ))
                count += 1
            conn.commit()

        logger.info(f"Loaded/Updated {count} sources in database.")
        return count

    def get_active_sources(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Retrieve active sources to crawl."""
        query = "SELECT * FROM sources WHERE active = 1 ORDER BY source_id ASC"
        if limit:
            query += f" LIMIT {limit}"

        with self.get_connection() as conn:
            rows = conn.execute(query).fetchall()
            return [dict(r) for r in rows]

    def update_source_crawl_status(self, source_id: str, success: bool, error_msg: Optional[str] = None):
        """Update last_checked timestamp and failure count."""
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self.get_connection() as conn:
            if success:
                conn.execute("""
                    UPDATE sources
                    SET last_checked = ?, status = 'Success', failure_count = 0
                    WHERE source_id = ?
                """, (now_str, source_id))
            else:
                conn.execute("""
                    UPDATE sources
                    SET last_checked = ?, status = 'Failed', failure_count = failure_count + 1
                    WHERE source_id = ?
                """, (now_str, source_id))
            conn.commit()

    def _next_opportunity_id(self, date_str: str, cursor: sqlite3.Cursor) -> str:
        """Generate structured ID like OPP-YYYYMMDD-001."""
        prefix = f"OPP-{date_str}-"
        cursor.execute("SELECT id FROM opportunities WHERE id LIKE ? ORDER BY id DESC LIMIT 1", (f"{prefix}%",))
        last_row = cursor.fetchone()
        if last_row:
            last_seq = int(last_row[0].split("-")[-1])
            next_seq = last_seq + 1
        else:
            next_seq = 1
        return f"{prefix}{next_seq:03d}"

    def _next_job_id(self, date_str: str, cursor: sqlite3.Cursor) -> str:
        """Generate structured ID like JOB-YYYYMMDD-001."""
        prefix = f"JOB-{date_str}-"
        cursor.execute("SELECT job_id FROM jobs WHERE job_id LIKE ? ORDER BY job_id DESC LIMIT 1", (f"{prefix}%",))
        last_row = cursor.fetchone()
        if last_row:
            last_seq = int(last_row[0].split("-")[-1])
            next_seq = last_seq + 1
        else:
            next_seq = 1
        return f"{prefix}{next_seq:03d}"

    def save_opportunity(self, opp: Dict[str, Any]) -> Tuple[str, str]:
        """
        Deduplicate and persist opportunity.
        Returns (action, id) where action is 'NEW', 'UPDATED', or 'UNCHANGED'.
        """
        composite_hash = generate_composite_key(
            opp.get("organization", ""),
            opp.get("opportunity", ""),
            opp.get("source_url", "")
        )
        content_hash = generate_content_hash(
            opp.get("summary", ""),
            opp.get("deadline", ""),
            opp.get("eligibility", "")
        )

        today_dt = date.today()
        today_date_str = today_dt.strftime("%Y%m%d")
        today_display = today_dt.strftime("%d-%m-%Y")

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, content_hash FROM opportunities WHERE composite_hash = ?", (composite_hash,))
            existing = cursor.fetchone()

            if not existing:
                opp_id = self._next_opportunity_id(today_date_str, cursor)
                cursor.execute("""
                    INSERT INTO opportunities (
                        id, first_seen, organization, country, region, type,
                        opportunity, sector, startup_stage, eligibility,
                        application_status, deadline, deadline_iso, days_remaining,
                        source_url, source_type, last_checked, status,
                        relevance_score, composite_hash, content_hash, summary
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'New', ?, ?, ?, ?)
                """, (
                    opp_id,
                    today_display,
                    opp.get("organization"),
                    opp.get("country"),
                    opp.get("region"),
                    opp.get("type"),
                    opp.get("opportunity"),
                    opp.get("sector"),
                    opp.get("startup_stage"),
                    opp.get("eligibility"),
                    opp.get("application_status", "Open"),
                    opp.get("deadline"),
                    opp.get("deadline_iso"),
                    opp.get("days_remaining"),
                    opp.get("source_url"),
                    opp.get("source_type"),
                    today_display,
                    opp.get("relevance_score", 0),
                    composite_hash,
                    content_hash,
                    opp.get("summary")
                ))
                conn.commit()
                return ("NEW", opp_id)
            else:
                opp_id = existing[0]
                prev_content_hash = existing[1]
                if prev_content_hash != content_hash:
                    cursor.execute("""
                        UPDATE opportunities
                        SET content_hash = ?, status = 'Updated', last_checked = ?,
                            deadline = ?, deadline_iso = ?, days_remaining = ?,
                            eligibility = ?, application_status = ?, summary = ?
                        WHERE id = ?
                    """, (
                        content_hash, today_display,
                        opp.get("deadline"), opp.get("deadline_iso"), opp.get("days_remaining"),
                        opp.get("eligibility"), opp.get("application_status", "Open"),
                        opp.get("summary"), opp_id
                    ))
                    # Record in history table
                    cursor.execute("""
                        INSERT INTO history (entity_type, entity_id, changed_at, change_type, old_value, new_value)
                        VALUES ('Opportunity', ?, ?, 'Content Update', ?, ?)
                    """, (opp_id, today_display, prev_content_hash, content_hash))
                    conn.commit()
                    return ("UPDATED", opp_id)
                else:
                    cursor.execute("UPDATE opportunities SET last_checked = ? WHERE id = ?", (today_display, opp_id))
                    conn.commit()
                    return ("UNCHANGED", opp_id)

    def save_job(self, job: Dict[str, Any]) -> Tuple[str, str]:
        """
        Deduplicate and persist ecosystem job.
        Returns (action, id) where action is 'NEW', 'UPDATED', or 'UNCHANGED'.
        """
        composite_hash = generate_composite_key(
            job.get("organization", ""),
            job.get("job_title", ""),
            job.get("job_url", "")
        )
        content_hash = generate_content_hash(
            job.get("summary", ""),
            job.get("closing_date", ""),
            job.get("salary", "")
        )

        today_dt = date.today()
        today_date_str = today_dt.strftime("%Y%m%d")
        today_display = today_dt.strftime("%d-%m-%Y")

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT job_id, content_hash FROM jobs WHERE composite_hash = ?", (composite_hash,))
            existing = cursor.fetchone()

            if not existing:
                job_id = self._next_job_id(today_date_str, cursor)
                cursor.execute("""
                    INSERT INTO jobs (
                        job_id, first_seen, organization, country, region,
                        job_title, function, seniority, employment, location,
                        remote, salary, closing_date, closing_iso, days_remaining,
                        job_url, source, relevance_score, status,
                        composite_hash, content_hash, summary
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'New', ?, ?, ?)
                """, (
                    job_id,
                    today_display,
                    job.get("organization"),
                    job.get("country"),
                    job.get("region"),
                    job.get("job_title"),
                    job.get("function"),
                    job.get("seniority"),
                    job.get("employment"),
                    job.get("location"),
                    job.get("remote"),
                    job.get("salary"),
                    job.get("closing_date"),
                    job.get("closing_iso"),
                    job.get("days_remaining"),
                    job.get("job_url"),
                    job.get("source"),
                    job.get("relevance_score", 0),
                    composite_hash,
                    content_hash,
                    job.get("summary")
                ))
                conn.commit()
                return ("NEW", job_id)
            else:
                job_id = existing[0]
                prev_content_hash = existing[1]
                if prev_content_hash != content_hash:
                    cursor.execute("""
                        UPDATE jobs
                        SET content_hash = ?, status = 'Updated',
                            salary = ?, closing_date = ?, closing_iso = ?,
                            days_remaining = ?, summary = ?
                        WHERE job_id = ?
                    """, (
                        content_hash,
                        job.get("salary"), job.get("closing_date"), job.get("closing_iso"),
                        job.get("days_remaining"), job.get("summary"), job_id
                    ))
                    cursor.execute("""
                        INSERT INTO history (entity_type, entity_id, changed_at, change_type, old_value, new_value)
                        VALUES ('Job', ?, ?, 'Content Update', ?, ?)
                    """, (job_id, today_display, prev_content_hash, content_hash))
                    conn.commit()
                    return ("UPDATED", job_id)
                else:
                    return ("UNCHANGED", job_id)

    def save_ecosystem_update(self, update: Dict[str, Any]) -> Tuple[str, Optional[int]]:
        """Deduplicate and insert ecosystem announcement."""
        composite_hash = generate_composite_key(
            update.get("organization", ""),
            update.get("title", ""),
            update.get("url", "")
        )

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM ecosystem_updates WHERE composite_hash = ?", (composite_hash,))
            if cursor.fetchone():
                return ("UNCHANGED", None)

            cursor.execute("""
                INSERT INTO ecosystem_updates (
                    date, organization, country, category, title, summary, url, composite_hash
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                update.get("date"),
                update.get("organization"),
                update.get("country"),
                update.get("category"),
                update.get("title"),
                update.get("summary"),
                update.get("url"),
                composite_hash
            ))
            conn.commit()
            return ("NEW", cursor.lastrowid)

    def log_run(self, run_metrics: Dict[str, Any]):
        """Persist execution statistics to run_logs table."""
        with self.get_connection() as conn:
            conn.execute("""
                INSERT INTO run_logs (
                    run_id, timestamp, duration_seconds, sources_total,
                    sources_successful, sources_failed, pages_scanned,
                    new_opportunities, updated_opportunities, new_jobs,
                    ecosystem_updates, error_summary
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                run_metrics.get("run_id"),
                run_metrics.get("timestamp"),
                run_metrics.get("duration_seconds"),
                run_metrics.get("sources_total"),
                run_metrics.get("sources_successful"),
                run_metrics.get("sources_failed"),
                run_metrics.get("pages_scanned"),
                run_metrics.get("new_opportunities"),
                run_metrics.get("updated_opportunities"),
                run_metrics.get("new_jobs"),
                run_metrics.get("ecosystem_updates"),
                run_metrics.get("error_summary", "")
            ))
            conn.commit()

    # Query Helpers for Sheets & Dashboards
    def get_opportunities(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            rows = conn.execute("SELECT * FROM opportunities ORDER BY first_seen DESC, relevance_score DESC").fetchall()
            return [dict(r) for r in rows]

    def get_jobs(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            rows = conn.execute("SELECT * FROM jobs ORDER BY first_seen DESC, relevance_score DESC").fetchall()
            return [dict(r) for r in rows]

    def get_ecosystem_updates(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            rows = conn.execute("SELECT * FROM ecosystem_updates ORDER BY id DESC").fetchall()
            return [dict(r) for r in rows]

    def get_deadlines(self) -> List[Dict[str, Any]]:
        """Retrieve active opportunities that have valid upcoming deadlines."""
        with self.get_connection() as conn:
            rows = conn.execute("""
                SELECT opportunity, organization, type, deadline, days_remaining, source_url as url
                FROM opportunities
                WHERE days_remaining IS NOT NULL AND days_remaining >= 0
                ORDER BY days_remaining ASC
            """).fetchall()
            return [dict(r) for r in rows]

    def get_all_sources(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            rows = conn.execute("SELECT * FROM sources ORDER BY source_id ASC").fetchall()
            return [dict(r) for r in rows]

    def get_organizations(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            rows = conn.execute("""
                SELECT organization, country, region, category, website, COUNT(source_id) as source_count
                FROM sources
                GROUP BY organization
                ORDER BY organization ASC
            """).fetchall()
            return [dict(r) for r in rows]

    def get_history(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            rows = conn.execute("SELECT * FROM history ORDER BY id DESC LIMIT 500").fetchall()
            return [dict(r) for r in rows]

    def get_run_logs(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            rows = conn.execute("SELECT * FROM run_logs ORDER BY timestamp DESC LIMIT 100").fetchall()
            return [dict(r) for r in rows]
