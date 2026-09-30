"""Settings and global constants for GSEIM."""

import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = os.getenv("GSEIM_DB_PATH", str(DATA_DIR / "gseim.sqlite3"))
EXCEL_OUTPUT_PATH = str(DATA_DIR / "global_startup_ecosystem_monitor.xlsx")
SOURCES_SEED_PATH = str(BASE_DIR / "config" / "sources_seed.json")

# Politeness & Networking
USER_AGENT = os.getenv(
    "GSEIM_USER_AGENT",
    "GSEIM-Bot/1.0 (+https://github.com/startup-ecosystem-intelligence/gseim; academic-research)"
)
REQUEST_TIMEOUT = 15  # seconds
RATE_LIMIT_DELAY = 1.0  # seconds between calls to same domain
MAX_RETRIES = 3
BACKOFF_FACTOR = 1.5

# Scoring Thresholds
MIN_OPPORTUNITY_SCORE = 8
MIN_JOB_SCORE = 10
MIN_UPDATE_SCORE = 6

# Google Sheets Configuration
SPREADSHEET_TITLE = "GLOBAL STARTUP ECOSYSTEM MONITOR"
SHEET_TABS = [
    "Dashboard",
    "New Opportunities",
    "Jobs",
    "Ecosystem Updates",
    "Deadlines",
    "Sources",
    "Keywords",
    "Organizations",
    "History",
    "Run Logs"
]
