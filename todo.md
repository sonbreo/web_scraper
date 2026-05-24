# Gumtree Web Scraper — TODO

## 1. Project Setup
- [x] Define dependencies (requests, BeautifulSoup4, lxml, etc.) in `requirements.txt`
- [ ] Set up virtual environment *(manual step: `python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`)*
- [x] Create project structure (src, tests, config, output dirs)
- [x] Add `.gitignore` for venv, output files, secrets

## 2. Configuration
- [x] Config file or `.env` for user settings (`config/settings.yaml` + `.env.example`)
- [x] Support multiple search queries / categories
- [x] Allow toggling features (notifications, CSV output, etc.)

## 3. HTTP / Request Layer
- [x] Fetch pages with `requests`
- [x] Set realistic User-Agent header to avoid blocks
- [x] Handle HTTP errors (4xx, 5xx) gracefully
- [x] Retry logic with exponential backoff on transient failures
- [x] Rate limiting / delay between requests to be polite
- [x] Support for proxies (optional)
- [x] Session reuse for connection pooling

## 4. Pagination
- [x] Detect total number of result pages
- [x] Iterate through all pages automatically (`iter_pages` generator in `src/pagination.py`)
- [x] Stop early if results fall outside filters (price, date, etc.)

## 5. HTML Parsing
- [x] Identify stable CSS selectors / HTML structure for:
  - [x] Listing title
  - [x] Price
  - [x] Location
  - [x] Date posted / age of listing
  - [x] Listing URL
  - [x] Thumbnail image URL
  - [x] Seller type (private vs dealer)
- [x] Handle missing or malformed fields without crashing
- [x] Handle "price on request" / non-numeric price strings

## 6. Filtering
- [x] Keyword matching (title must contain all / any keywords)
- [x] Price range (min / max)
- [x] Location / radius filter
- [x] Date filter (e.g. only listings posted in last N days)
- [x] Exclude keywords (e.g. "parts only", "broken")
- [x] Seller type filter (private only, dealer only, or both)

## 7. Deduplication
- [x] Track seen listing IDs or URLs across runs
- [x] Skip already-seen listings on repeat runs
- [x] Persist seen-listings state between runs (file or lightweight DB)

## 8. Data Storage
- [x] In-memory representation (list of dicts or dataclass)
- [x] CSV export
- [x] JSON export
- [x] Optional: SQLite database for persistent storage and querying

## 9. Notifications
- [x] Email alert for new matching listings (SMTP / smtplib)
- [ ] Optional: desktop notification (plyer or similar)
- [x] Optional: Slack / Discord webhook
- [x] Only notify for listings not seen in previous runs

## 10. Scheduling / Polling
- [x] Run on an interval (e.g. every 15 minutes)
- [x] CLI flag to run once vs. run continuously
- [x] Log each run with timestamp

## 11. CLI Interface
- [x] Accept search URL or keywords as CLI arguments
- [x] Flags for price range, location, interval, output format
- [x] `--dry-run` mode (print results, no notifications or writes)
- [x] `--verbose` / `--quiet` modes

## 12. Logging
- [x] Use Python `logging` module (not bare `print`)
- [x] Log levels: DEBUG for parsing detail, INFO for run summary, WARNING/ERROR for failures
- [x] Write logs to file and/or stdout

## 13. Error Handling & Robustness
- [x] Catch and log network timeouts without crashing
- [x] Handle Gumtree layout changes gracefully (warn when selectors return nothing)
- [x] Validate config values on startup (bad URL, invalid price range, etc.)

## 14. Testing
- [ ] Unit tests for parsing logic using saved HTML fixtures
- [ ] Unit tests for filtering and deduplication
- [ ] Unit tests for price string cleaning
- [ ] Integration test with a real (or mocked) HTTP request
- [ ] Test edge cases: empty results, single result, all items filtered out

## 15. Documentation
- [ ] README: what it does, how to install, how to configure, how to run
- [ ] Document each config option
- [ ] Add example output (sample CSV / JSON)
