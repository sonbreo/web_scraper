# Gumtree Web Scraper — TODO

## 1. Project Setup
- [ ] Define dependencies (requests, BeautifulSoup4, lxml, etc.) in `requirements.txt`
- [ ] Set up virtual environment
- [ ] Create project structure (src, tests, config, output dirs)
- [ ] Add `.gitignore` for venv, output files, secrets

## 2. Configuration
- [ ] Config file or `.env` for user settings (search URL, keywords, price range, location, etc.)
- [ ] Support multiple search queries / categories
- [ ] Allow toggling features (notifications, CSV output, etc.)

## 3. HTTP / Request Layer
- [ ] Fetch pages with `requests` (or `httpx` for async)
- [ ] Set realistic User-Agent header to avoid blocks
- [ ] Handle HTTP errors (4xx, 5xx) gracefully
- [ ] Retry logic with exponential backoff on transient failures
- [ ] Rate limiting / delay between requests to be polite
- [ ] Support for proxies (optional)
- [ ] Session reuse for connection pooling

## 4. Pagination
- [ ] Detect total number of result pages
- [ ] Iterate through all pages automatically
- [ ] Stop early if results fall outside filters (price, date, etc.)

## 5. HTML Parsing
- [ ] Identify stable CSS selectors / HTML structure for:
  - [ ] Listing title
  - [ ] Price
  - [ ] Location
  - [ ] Date posted / age of listing
  - [ ] Listing URL
  - [ ] Thumbnail image URL
  - [ ] Seller type (private vs dealer)
- [ ] Handle missing or malformed fields without crashing
- [ ] Handle "price on request" / non-numeric price strings

## 6. Filtering
- [ ] Keyword matching (title must contain all / any keywords)
- [ ] Price range (min / max)
- [ ] Location / radius filter
- [ ] Date filter (e.g. only listings posted in last N days)
- [ ] Exclude keywords (e.g. "parts only", "broken")
- [ ] Seller type filter (private only, dealer only, or both)

## 7. Deduplication
- [ ] Track seen listing IDs or URLs across runs
- [ ] Skip already-seen listings on repeat runs
- [ ] Persist seen-listings state between runs (file or lightweight DB)

## 8. Data Storage
- [ ] In-memory representation (list of dicts or dataclass)
- [ ] CSV export
- [ ] JSON export
- [ ] Optional: SQLite database for persistent storage and querying

## 9. Notifications
- [ ] Email alert for new matching listings (SMTP / smtplib)
- [ ] Optional: desktop notification (plyer or similar)
- [ ] Optional: Slack / Discord webhook
- [ ] Only notify for listings not seen in previous runs

## 10. Scheduling / Polling
- [ ] Run on an interval (e.g. every 15 minutes)
- [ ] CLI flag to run once vs. run continuously
- [ ] Log each run with timestamp

## 11. CLI Interface
- [ ] Accept search URL or keywords as CLI arguments
- [ ] Flags for price range, location, interval, output format
- [ ] `--dry-run` mode (print results, no notifications or writes)
- [ ] `--verbose` / `--quiet` modes

## 12. Logging
- [ ] Use Python `logging` module (not bare `print`)
- [ ] Log levels: DEBUG for parsing detail, INFO for run summary, WARNING/ERROR for failures
- [ ] Write logs to file and/or stdout

## 13. Error Handling & Robustness
- [ ] Catch and log network timeouts without crashing
- [ ] Handle Gumtree layout changes gracefully (warn when selectors return nothing)
- [ ] Validate config values on startup (bad URL, invalid price range, etc.)

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
