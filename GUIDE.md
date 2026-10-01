# Complete User Guide: Running GSEIM

This guide covers everything you need to set up, run, customize, and automate the **Global Startup Ecosystem Intelligence Monitor (GSEIM)**.

---

## Table of Contents
1. [System Architecture Overview](#1-system-architecture-overview)
2. [Prerequisites](#2-prerequisites)
3. [Local Installation](#3-local-installation)
4. [Running via CLI (Command Line)](#4-running-via-cli-command-line)
5. [Setting Up Google Sheets Sync](#5-setting-up-google-sheets-sync)
6. [Running on Google Colab (Cloud)](#6-running-on-google-colab-cloud)
7. [Automating Daily Runs (GitHub Actions & Cron)](#7-automating-daily-runs-github-actions--cron)
8. [Understanding the Outputs & 10-Tab Schema](#8-understanding-the-outputs--10-tab-schema)
9. [Customizing Taxonomies, Scoring & Adding Sources](#9-customizing-taxonomies-scoring--adding-sources)
10. [Running the Test Suite](#10-running-the-test-suite)

---

## 1. System Architecture Overview

GSEIM operates as a 4-stage pipeline with **zero GenAI / zero LLM token costs**:

```
[147+ Global Sources] (Government, Incubators, Accelerators, ATS boards)
         │
         ▼
[Polite Ingestion Layer] (RSS/Atom + robots.txt/Sitemaps + HTML + Lever/Greenhouse/Ashby ATS)
         │
         ▼
[Deterministic Scoring Engine] (Weighted keyword scoring + date regex + role classifiers)
         │
         ▼
[Deduplication & Change Detection] (SHA-256 Composite keys & Content hashes)
         │
         ▼
[Delivery & Persistence] (SQLite DB + Multi-tab Google Sheets + Offline Excel Mirror)
```

---

## 2. Prerequisites

- **Python 3.10 to 3.13** installed on your system.
- **Git** installed.
- *(Optional)* A Google account with Google Sheets enabled if you want real-time cloud spreadsheet synchronization.

---

## 3. Local Installation

### Step 1: Clone the repository
```bash
git clone https://github.com/divyanshu2074/gseim.git
cd gseim
```

### Step 2: Create a virtual environment (Recommended)
```bash
# On Windows:
python -m venv venv
venv\Scripts\activate

# On macOS/Linux:
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install dependencies
```bash
pip install -r requirements.txt
```

---

## 4. Running via CLI (Command Line)

The primary entry point is `main.py`.

### Quick Test (Sample of 15 sources)
Runs a fast test crawl on the first 15 registered sources:
```bash
python main.py --sample 15
```

### Filter by Collection Method
You can restrict execution to specific protocols:
```bash
# Crawl only RSS feeds (Fastest, ~15-30 seconds)
python main.py --method RSS

# Crawl only XML sitemaps
python main.py --method SITEMAP

# Crawl only ATS job platforms (Lever, Greenhouse, Ashby)
python main.py --method ATS

# Crawl only HTML web pages
python main.py --method HTML
```

### Full Crawl of All 147+ Global Sources
```bash
python main.py
```

### Output After Run
At the end of every run, GSEIM:
1. Updates the SQLite database at `data/gseim.sqlite3`.
2. Generates an updated multi-tab Excel workbook at `data/global_startup_ecosystem_monitor.xlsx`.
3. Displays a formatted terminal run report:
```text
=====================================
GLOBAL ECOSYSTEM MONITOR
01 October 2026
=====================================
Sources:
  Total: 147
  Successful: 14
  Failed: 0

Results:
  New opportunities: 11
  Updated opportunities: 0
  New jobs: 0
  Ecosystem updates: 0

Categories:
  Investment: 6
  Grant: 2
  Opportunity: 1
  Accelerator: 1
  Competition: 1
=====================================
```

---

## 5. Setting Up Google Sheets Sync

GSEIM can automatically sync to a live Google Sheet titled **`GLOBAL STARTUP ECOSYSTEM MONITOR`** containing all 10 tabs.

### Option A: Service Account (Recommended for Automated/Headless Servers)
1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a project and enable the **Google Sheets API** and **Google Drive API**.
3. Create a **Service Account** and download its JSON key.
4. Rename the downloaded key to `service_account.json` and place it in the `gseim/` root directory (it is already in `.gitignore` so it won't be pushed to GitHub).
5. Share your Google Sheet with the `client_email` found inside `service_account.json` with **Editor** permissions.
6. Run:
```bash
python main.py --sync-sheets
```

### Option B: Offline Excel Mirror (Zero Setup)
If no Google credentials are provided, GSEIM automatically creates:
`data/global_startup_ecosystem_monitor.xlsx`
You can open this directly in Microsoft Excel, Apple Numbers, or import it into Google Drive manually anytime.

---

## 6. Running on Google Colab (Cloud)

If you don't want to run the crawler on your local machine, use Google Colab:

1. Open [Google Colab](https://colab.research.google.com/).
2. Click **File** $\rightarrow$ **Upload notebook** and upload:
   `notebooks/GSEIM_Colab_Runner.ipynb`
3. Execute the 17 cells sequentially:
   - **Cell 1**: Installs lightweight dependencies (`feedparser`, `openpyxl`, `gspread`, etc.).
   - **Cell 2**: Interactively authenticates with your Google Account via `google.colab.auth.authenticate_user()`.
   - **Cells 3–5**: Loads configuration, seed registry, and historical SQLite records.
   - **Cells 6–9**: Executes collectors across RSS, sitemaps, HTML, and ATS boards.
   - **Cells 10–12**: Runs weighted scoring and classifiers.
   - **Cells 13–14**: Deduplicates opportunities and jobs using SHA-256 composite keys.
   - **Cell 15**: Synchronizes all 10 tabs to your Google Sheet and generates the Excel mirror.
   - **Cells 16–17**: Displays the run report and upcoming deadlines table inline.

> [!TIP]
> **Persistent Colab Storage**: In Google Colab, you can mount Google Drive (`drive.mount('/content/drive')`) and point `GSEIM_DB_PATH` to `/content/drive/MyDrive/gseim.sqlite3` so your historical crawl database persists across Colab sessions.

---

## 7. Automating Daily Runs (GitHub Actions & Cron)

### GitHub Actions (Run Every Morning at 06:00 UTC)
You can create a `.github/workflows/daily_crawler.yml` file in your repository:

```yaml
name: GSEIM Daily Intelligence Monitor

on:
  schedule:
    - cron: '0 6 * * *'  # Runs daily at 06:00 UTC
  workflow_dispatch:      # Allows manual trigger button in GitHub UI

jobs:
  crawl:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run Crawler
        env:
          GOOGLE_APPLICATION_CREDENTIALS: ${{ secrets.GCP_SA_KEY }}
        run: |
          python main.py --sync-sheets

      - name: Archive Excel Artifact
        uses: actions/upload-artifact@v4
        with:
          name: ecosystem-monitor-excel
          path: data/global_startup_ecosystem_monitor.xlsx
```

---

## 8. Understanding the Outputs & 10-Tab Schema

| Tab # | Sheet Name | Description & Key Fields |
|---|---|---|
| **1** | `Dashboard` | Executive summary metrics: Today's new counts, upcoming deadlines within 7 and 30 days, country and category breakdowns. |
| **2** | `New Opportunities` | All active grants, accelerators, cohorts, competitions with fields: `ID` (`OPP-YYYYMMDD-XXX`), `Organization`, `Country`, `Type`, `Opportunity`, `Sector`, `Startup Stage`, `Eligibility`, `Application Status`, `Deadline`, `Relevance Score`. |
| **3** | `Jobs` | Ecosystem-specific roles: `Job ID` (`JOB-YYYYMMDD-XXX`), `Organization`, `Country`, `Job Title`, `Function` (Incubation, Acceleration, Investment, etc.), `Seniority`, `Employment`, `Location`, `Remote`, `Salary`, `Closing Date`. |
| **4** | `Ecosystem Updates` | High-level ecosystem announcements: `Date`, `Organization`, `Country`, `Category`, `Title`, `Summary`, `URL`. |
| **5** | `Deadlines` | Active opportunities sorted by `Days Remaining` for daily urgency tracking. |
| **6** | `Sources` | Live source registry with all 147+ sources, monitoring methods, frequency, and crawl health status. |
| **7** | `Keywords` | Active keyword taxonomy, scoring weights (+8, +10), and negative filter lists. |
| **8** | `Organizations` | Master directory of tracked institutions and their program counts. |
| **9** | `History` | Audit trail recording content updates, deadline extensions, or funding revisions. |
| **10** | `Run Logs` | Chronological audit log of each run: duration, scanned pages, new/updated items. |

---

## 9. Customizing Taxonomies, Scoring & Adding Sources

### Adding a New Source
Open `config/sources_seed.json` and append your source:
```json
{
  "source_id": "SRC-CUSTOM-001",
  "organization": "Example Innovation Hub",
  "country": "India",
  "region": "South Asia",
  "category": "Incubator",
  "website": "https://example.com",
  "opportunities_page": "https://example.com/programs",
  "jobs_page": "https://example.com/careers",
  "rss": "https://example.com/feed",
  "sitemap": null,
  "monitoring_method": "RSS",
  "frequency": "Daily",
  "active": true
}
```

### Modifying Keywords & Scoring Weights
Edit `config/keywords.py`:
- **Opportunity Category Keywords**: Add new category names or terms to `CATEGORY_KEYWORDS`.
- **Positive Weights**: Adjust `OPPORTUNITY_WEIGHTS` or `JOB_WEIGHTS` to boost specific terms (e.g. `"grant up to": 8`).
- **Negative Exclusions**: Add non-ecosystem terms to `EXCLUDE_JOBS` or `EXCLUDE_OPPORTUNITIES` to automatically disqualify unwanted roles.

### Adjusting Relevance Thresholds
Edit `config/settings.py`:
- `MIN_OPPORTUNITY_SCORE`: Default `8`. Increase to `12` for stricter filtering.
- `MIN_JOB_SCORE`: Default `10`.
- `RATE_LIMIT_DELAY`: Default `1.0` seconds between requests to the same domain.

---

## 10. Running the Test Suite

Run the full pytest suite locally:
```bash
python -m pytest tests/ -v
```

All 19 tests will execute, verifying:
- Opportunity scoring & negative keyword disqualification
- Job role categorization & software developer exclusion
- Date parser & deadline extraction across multiple formats
- Canonical composite key deduplication & content-hash change detection
- Multi-tab Excel export matching the exact 10-tab schema
- Mocked network collectors (RSS, HTML, ATS)
