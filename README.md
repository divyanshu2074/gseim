# Global Startup Ecosystem Intelligence Monitor (GSEIM)

**GSEIM** is a production-grade, zero-LLM data-collection and intelligence monitoring system designed to discover, track, score, and deduplicate public startup opportunities and ecosystem-level jobs from around the world.

It starts seamlessly on Google Colab or local CLI and scales across hundreds of global sources using deterministic algorithms (polite collectors, regex, and weighted keyword scoring) without generating GenAI token costs or hallucinations.

---

## 1. What GSEIM Monitors

GSEIM monitors publicly available data across 7 global ecosystem categories:
1. **Government**: Ministries, DPIIT, MeitY, SBA, NSF, UKRI, Innovate UK, state startup missions, innovation agencies, public tenders, and startup grants.
2. **Incubators**: University incubators (IITs, IIMs, Oxford, Cambridge, MIT, Stanford, TUM), government TBIs, private incubators, deeptech labs.
3. **Accelerators**: Techstars, Y Combinator, MassChallenge, Plug and Play, 500 Global, regional/sector cohorts.
4. **Ecosystem Organizations**: Startup associations, entrepreneurship networks, founder communities, national councils.
5. **Universities**: Innovation centres, Technology Transfer Offices (TTOs), entrepreneurship fellowships.
6. **Investment Ecosystem**: VC funds, angel networks, seed funds, venture studios (Founders Factory, Antler, SOSV).
7. **Ecosystem Jobs**: Targeted ecosystem roles (*Program Manager, Incubation Manager, Accelerator Manager, Investment Associate, VC Analyst, Ecosystem Manager, Innovation Manager, Strategy / Founder's Office, Technology Transfer Officer*). General non-ecosystem tech/sales roles are automatically disqualified.

---

## 2. Google Sheets Architecture

All intelligence is synchronized outward to a multi-tab Google Sheet (`GLOBAL STARTUP ECOSYSTEM MONITOR`) and mirrored offline to an Excel workbook (`global_startup_ecosystem_monitor.xlsx`):

```text
GLOBAL STARTUP ECOSYSTEM MONITOR
│
├── 1. Dashboard           # Executive summary: Today's new counts, urgent deadlines, country/category breakdowns
├── 2. New Opportunities   # Grants, Accelerators, Incubators, Competitions, Fellowships with deadlines & scores
├── 3. Jobs                # Ecosystem jobs with role function, seniority, remote status, salary & closing date
├── 4. Ecosystem Updates   # Announcements: ₹500 Cr funds, centres of excellence, state policies, MoUs
├── 5. Deadlines           # Filtered view sorted by Days Remaining (closing in 7 / 30 days)
├── 6. Sources             # Source registry with crawl health, status, and failure counters (147+ seed sources)
├── 7. Keywords            # Deterministic scoring dictionaries, category weights, and exclusion lists
├── 8. Organizations       # Tracked institutions and active program counts
├── 9. History             # Change audit log (content updates, modified deadlines, new funding amounts)
└── 10. Run Logs           # Execution metrics: duration, scanned pages, success/failure counts
```

---

## 3. Core Architecture & Pipeline

```text
SOURCE REGISTRY (147+ Seed Sources)
       │
       ▼
COLLECTION LAYER
  ├── RSS / Atom Feeds (feedparser)
  ├── Robots.txt & Sitemaps (ElementTree / XML)
  ├── Static HTML & Microdata (BeautifulSoup / JSON-LD)
  └── Job Portals & ATS APIs (Greenhouse, Lever, Ashby)
       │
       ▼
DETERMINISTIC INTELLIGENCE ENGINE
  ├── Normalization & Canonical URLs
  ├── Date & Deadline Regex Extractor
  ├── Opportunity Classifier & Weighted Scorer (>8 threshold)
  ├── Ecosystem Job Classifier & Negative Filter (>10 threshold)
  └── Composite SHA256 Deduplication & Content Hash Update Detector
       │
       ▼
STORAGE & DELIVERY
  ├── SQLite Database (gseim.sqlite3) [Source-of-truth & Deduplication State]
  ├── Google Sheets (gspread / Google Sheets API)
  └── Excel Workbook Mirror (openpyxl)
```

---

## 4. Quickstart: Local CLI

### Installation
```bash
git clone https://github.com/startup-ecosystem-intelligence/gseim.git
cd gseim
pip install -r requirements.txt
```

### Run Pipeline
```bash
# Run a sample crawl of 15 sources
python main.py --sample 15

# Run only RSS sources
python main.py --method RSS

# Run full pipeline with Google Sheets sync
python main.py --sync-sheets
```

---

## 5. Google Colab Execution

Open `notebooks/GSEIM_Colab_Runner.ipynb` in Google Colab. The 17-cell interactive flow executes:
1. `CELL 1`: Install dependencies
2. `CELL 2`: Authenticate Google account (`google.colab.auth`)
3. `CELL 3`: Load configuration & taxonomies
4. `CELL 4`: Load source database
5. `CELL 5`: Load historical records
6. `CELL 6`: Initialize polite crawler
7. `CELL 7`: Collect RSS
8. `CELL 8`: Collect sitemaps
9. `CELL 9`: Collect HTML & ATS
10. `CELL 10`: Extract opportunities
11. `CELL 11`: Extract jobs
12. `CELL 12`: Classify ecosystem updates
13. `CELL 13`: Deduplicate opportunities
14. `CELL 14`: Detect updates and persist jobs
15. `CELL 15`: Export Excel mirror & sync Google Sheets
16. `CELL 16`: Generate execution report
17. `CELL 17`: Display interactive statistics table

---

## 6. Running Tests

Run the full pytest suite:
```bash
pytest tests/ -v
```
Verifies:
- Opportunity scoring & negative keyword disqualification
- Job role categorization & software developer exclusion
- Date parser & deadline extraction across multiple formats
- Canonical composite key deduplication & content-hash change detection
- Multi-tab Excel export matching the exact 10-tab schema
