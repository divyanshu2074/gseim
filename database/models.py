"""SQLite schema definitions for GSEIM."""

CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS sources (
    source_id TEXT PRIMARY KEY,
    organization TEXT NOT NULL,
    country TEXT,
    region TEXT,
    category TEXT,
    website TEXT,
    opportunities_page TEXT,
    jobs_page TEXT,
    rss TEXT,
    sitemap TEXT,
    monitoring_method TEXT,
    frequency TEXT DEFAULT 'Daily',
    active INTEGER DEFAULT 1,
    last_checked TEXT,
    status TEXT DEFAULT 'Pending',
    failure_count INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS opportunities (
    id TEXT PRIMARY KEY,
    first_seen TEXT NOT NULL,
    organization TEXT NOT NULL,
    country TEXT,
    region TEXT,
    type TEXT,
    opportunity TEXT NOT NULL,
    sector TEXT,
    startup_stage TEXT,
    eligibility TEXT,
    application_status TEXT DEFAULT 'Open',
    deadline TEXT,
    deadline_iso TEXT,
    days_remaining INTEGER,
    source_url TEXT NOT NULL,
    source_type TEXT,
    last_checked TEXT NOT NULL,
    status TEXT DEFAULT 'New',
    relevance_score INTEGER DEFAULT 0,
    composite_hash TEXT UNIQUE NOT NULL,
    content_hash TEXT NOT NULL,
    summary TEXT
);

CREATE TABLE IF NOT EXISTS jobs (
    job_id TEXT PRIMARY KEY,
    first_seen TEXT NOT NULL,
    organization TEXT NOT NULL,
    country TEXT,
    region TEXT,
    job_title TEXT NOT NULL,
    function TEXT,
    seniority TEXT,
    employment TEXT,
    location TEXT,
    remote TEXT,
    salary TEXT,
    closing_date TEXT,
    closing_iso TEXT,
    days_remaining INTEGER,
    job_url TEXT NOT NULL,
    source TEXT,
    relevance_score INTEGER DEFAULT 0,
    status TEXT DEFAULT 'New',
    composite_hash TEXT UNIQUE NOT NULL,
    content_hash TEXT NOT NULL,
    summary TEXT
);

CREATE TABLE IF NOT EXISTS ecosystem_updates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    organization TEXT NOT NULL,
    country TEXT,
    category TEXT,
    title TEXT NOT NULL,
    summary TEXT,
    url TEXT,
    composite_hash TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    changed_at TEXT NOT NULL,
    change_type TEXT NOT NULL,
    old_value TEXT,
    new_value TEXT
);

CREATE TABLE IF NOT EXISTS run_logs (
    run_id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,
    duration_seconds REAL,
    sources_total INTEGER,
    sources_successful INTEGER,
    sources_failed INTEGER,
    pages_scanned INTEGER,
    new_opportunities INTEGER,
    updated_opportunities INTEGER,
    new_jobs INTEGER,
    ecosystem_updates INTEGER,
    error_summary TEXT
);

CREATE INDEX IF NOT EXISTS idx_opp_composite ON opportunities(composite_hash);
CREATE INDEX IF NOT EXISTS idx_job_composite ON jobs(composite_hash);
CREATE INDEX IF NOT EXISTS idx_upd_composite ON ecosystem_updates(composite_hash);
CREATE INDEX IF NOT EXISTS idx_opp_deadline ON opportunities(deadline_iso);
CREATE INDEX IF NOT EXISTS idx_job_closing ON jobs(closing_iso);
"""
