# 🕷️ Gumtree Scraper

Monitor Gumtree listings and get notified the moment something new pops up. Runs once or polls continuously, filters by price / location / seller type, and exports to CSV, JSON, or SQLite.

---

## Features

- 🔍 **Keyword & filter matching** — price range, location, seller type, age, exclude terms
- 🔁 **Deduplication** — skips listings already seen in previous runs
- 💾 **Flexible output** — CSV, JSON, and/or SQLite
- 🔔 **Notifications** — email (SMTP) and Discord webhook
- ⏱️ **Scheduling** — run once or poll on an interval
- 🛡️ **Resilient fetching** — retries with exponential backoff, rate limiting, proxy support

---

## Quickstart

```bash
git clone https://github.com/sonbreo/web_scraper.git
cd web_scraper

python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env          # add credentials if using email/Discord alerts
python main.py --once --dry-run
```

---

## Configuration

Edit `config/settings.yaml`:

```yaml
searches:
  - url: "https://www.gumtree.com.au/s-video-games-consoles/melbourne/..."
    keywords: ["nintendo", "switch", "console"]

filters:
  price:
    min: 100
    max: 500
  max_age_days: 7
  exclude_keywords: ["parts only", "broken", "faulty"]
  seller_type: all      # private | dealer | all
  location: null        # e.g. "Melbourne" — substring match on listing location

features:
  notifications:
    email: false
    discord: false
  output:
    csv: true
    json: false
    sqlite: false

scheduling:
  interval_seconds: 900   # 15 minutes
```

Sensitive values (SMTP password, Discord webhook URL) go in `.env`:

```
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=you@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=you@gmail.com
SMTP_TO=alerts@example.com
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
```

---

## CLI Usage

```
python main.py [OPTIONS]
```

| Option | Description |
|---|---|
| `--once` | Run a single scrape and exit |
| `--interval SECONDS` | Poll on a custom interval (overrides config) |
| `--dry-run` | Print results to stdout; no saves or notifications |
| `--min-price N` | Override minimum price filter |
| `--max-price N` | Override maximum price filter |
| `--location TEXT` | Override location substring filter |
| `--seller-type TYPE` | `private`, `dealer`, or `all` |
| `--csv` | Enable CSV output |
| `--json` | Enable JSON output |
| `--sqlite` | Enable SQLite output |
| `--verbose` / `-v` | DEBUG logging |
| `--quiet` / `-q` | Warnings and errors only |
| `--config PATH` | Path to a custom settings file |

### Examples

```bash
# Dry run — see what would be found without saving anything
python main.py --once --dry-run

# Poll every 10 minutes, private sellers only, max $300
python main.py --interval 600 --seller-type private --max-price 300

# One-shot run with CSV + JSON output
python main.py --once --csv --json
```

---

## Output

| File | Description |
|---|---|
| `output/listings.csv` | Appended on each run |
| `output/listings.json` | Appended on each run |
| `output/listings.db` | SQLite — `listings` table, deduped by `listing_id` |
| `output/seen_listings.json` | Tracks seen IDs across runs |

---

## Project Structure

```
web_scraper/
├── main.py                 # Entry point
├── config/
│   └── settings.yaml       # User configuration
├── src/
│   ├── cli.py              # Argument parsing & logging setup
│   ├── runner.py           # Fetch → parse → filter → dedup → store → notify
│   ├── fetcher.py          # HTTP requests, retries, rate limiting
│   ├── pagination.py       # Page iterator
│   ├── parser.py           # HTML parsing & Listing dataclass
│   ├── filters.py          # All filter logic
│   ├── deduplicator.py     # Seen-listings state
│   ├── storage.py          # CSV / JSON / SQLite export
│   ├── notifications.py    # Email & Discord alerts
│   └── scheduler.py        # run_once / run_loop
├── tests/                  # 78 unit tests
└── output/                 # Created on first run
```

---

## Running Tests

```bash
pip install pytest
python -m pytest tests/ -v
```

---

## Note on Blocking

Gumtree blocks requests from cloud/datacenter IP ranges. Run this script from your **home machine** for best results. If you're still getting 403s, try adding a proxy in `config/settings.yaml` under `http.proxies`.
