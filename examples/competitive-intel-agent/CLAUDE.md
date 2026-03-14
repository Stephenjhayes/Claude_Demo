# Competitive Intelligence Agent

## What this is

A daily-running Python agent that monitors a company's competitors across the
web and produces executive-grade intelligence reports. It is fully generic —
the company identity and competitor list live in `company.yaml` (gitignored),
so the same codebase serves any company in any industry.

**Data collection → Claude Opus 4.6 analysis → HTML report + Slack digest**

The primary data source is **Ahrefs Firehose** (`firehose.com`) — a free
real-time web mentions API backed by one of the largest crawlers on the web.
Firecrawl, NewsAPI, and SEC EDGAR supplement it.

---

## Repo layout

```
main.py                      Entry point + CLI (--setup, --bootstrap, --run-now, --schedule)
config.py                    Loads company.yaml + all env vars; single source of truth
company.example.yaml         Template — copy to company.yaml and fill in
requirements.txt

scrapers/
  firehose_scraper.py        Primary: SSE stream from Ahrefs Firehose, auto-generates
                             Lucene rules per competitor from company.yaml
  firecrawl_scraper.py       Supplemental: deep scraping of press rooms, blogs, careers
  news_scraper.py            Supplemental: NewsAPI articles + SEC EDGAR 10-K/10-Q/8-K

storage/
  database.py                SQLite with WAL mode; 3 tables, 24-month rolling retention

analysis/
  analyzer.py                Claude Opus 4.6 (adaptive thinking + streaming);
                             builds prompts at runtime from config — no hardcoded names

reports/
  report_generator.py        Self-contained HTML executive report + markdown daily digest
```

---

## Configuration

### Two files to set up before running

**`company.yaml`** (gitignored — your private config):
```yaml
company:
  name: "Acme Corp"
  industry: "B2B SaaS"
  description: "Acme makes widgets for enterprise customers."

competitors:
  widget_co:
    name: "Widget Co"
    press_room: "https://widgetco.com/news/"
    blog: "https://widgetco.com/blog/"
    products: "https://widgetco.com/products/"
    careers: "https://widgetco.com/careers/"
    ticker: "WDGT"                    # omit if private company
    news_query: "Widget Co enterprise" # optional, defaults to name
    firehose_rules:                    # optional explicit Lucene rules
      - '"Widget Co" AND recent:24h'
```

**`.env`** (gitignored):
```
ANTHROPIC_API_KEY=sk-ant-...
FIREHOSE_MGMT_KEY=fhm_...       # from firehose.com — used only for --bootstrap
FIREHOSE_TAP_TOKEN=fh_...       # printed by --bootstrap, used for daily pulls
FIRECRAWL_API_KEY=fc-...        # optional
NEWS_API_KEY=...                # optional
```

### All overridable env vars

| Variable | Default | Purpose |
|---|---|---|
| `COMPANY_CONFIG` | `./company.yaml` | Path to company config |
| `INTEL_DB_PATH` | `./competitive_intel.db` | SQLite database path |
| `REPORTS_DIR` | `./reports` | Output directory for HTML/MD reports |
| `RETENTION_MONTHS` | `24` | How many months of data to keep |
| `FIREHOSE_SINCE` | `24h` | SSE replay window (max 24h) |
| `FIREHOSE_MAX_EVENTS` | `5000` | Cap per daily pull |
| `FIREHOSE_TAP_NAME` | `competitive-intel` | Name of the Firehose tap |
| `DAILY_RUN_HOUR` | `6` | UTC hour for scheduled runs |
| `DAILY_RUN_MINUTE` | `0` | UTC minute for scheduled runs |

---

## CLI commands

```bash
python main.py --setup           # interactive wizard → creates company.yaml
python main.py --bootstrap       # creates Firehose tap + installs Lucene rules
python main.py --run-now         # full pipeline: collect → analyse → report
python main.py --run-now --news-days 30   # first run: back-fill 30 days of news
python main.py --schedule        # start daily cron at DAILY_RUN_HOUR:DAILY_RUN_MINUTE UTC
python main.py --report-only     # regenerate report from existing DB (no collection)
python main.py --run-now --skip-firehose   # skip Firehose, use other sources only
python main.py --run-now --skip-firecrawl  # skip Firecrawl deep scraping
```

---

## Daily pipeline (what --run-now does)

```
1. init_db()           Create tables if missing; purge records older than 24 months
2. Firehose pull       SSE drain of last 24h buffer → raw_events (source_type=firehose)
3. Firecrawl scrape    Press rooms, blogs, product pages, careers → raw_events
4. News + SEC          NewsAPI articles + SEC EDGAR filings → raw_events
5. Daily snapshots     Claude Opus 4.6 per-competitor: summary, key_signals, sentiment
6. Markdown digest     reports/daily_digest_YYYY-MM-DD.md  (Slack/email ready)
7. Comparison report   Claude Opus 4.6 across all competitors × 24 months of snapshots
8. HTML report         reports/competitive_intel_YYYY-MM-DD.html (self-contained)
```

---

## Database schema

Three tables in `competitive_intel.db`:

**`raw_events`** — every piece of collected intelligence
- `competitor_id` — slug matching a key in `company.yaml`
- `source_type` — `firehose | press_room | blog | products | careers | news | sec`
- `url`, `title`, `content`, `published_at`, `scraped_at`
- `metadata` — JSON blob (domain, tags, language, word_count, etc.)

**`daily_snapshots`** — one Claude-generated summary per competitor per day
- `snapshot_date` (YYYY-MM-DD), `competitor_id`
- `summary` — 2-3 sentence prose
- `key_signals` — JSON list of bullet strings
- `sentiment_score` — float -1.0 to 1.0 (negative = bad for your company)
- UNIQUE on `(snapshot_date, competitor_id)` — safe to re-run

**`comparisons`** — one cross-competitor report per day
- `report_date`, `period_months`, `narrative`, `insights` (JSON), `html_path`
- UNIQUE on `(report_date, period_months)` — safe to re-run

---

## How Firehose works

Firehose delivers matching pages via Server-Sent Events (SSE). You define
Lucene rules; Firehose buffers up to 24h of matching events.

**Bootstrap (one-time):**
1. `--bootstrap` calls `POST /v1/taps` to create a named tap
2. Installs one Lucene rule per competitor, e.g.:
   - `"Duck Creek Technologies" AND recent:24h`  (tag: `duck_creek`)
   - `title:"Duck Creek" AND recent:24h`          (tag: `duck_creek`)
3. Prints the `fh_...` tap token — save this to `.env`

**Daily pull:**
- `GET /v1/stream?since=24h&limit=5000` via SSE
- Each event's `tags` field is mapped back to a `competitor_id` via `TAG_TO_COMPETITOR`
- Events stored as `raw_events` with `source_type=firehose`

**Custom rules** — add `firehose_rules:` to a competitor in `company.yaml` to
override auto-generated rules with hand-crafted Lucene queries.

---

## How Claude analysis works

`analysis/analyzer.py` makes two Claude Opus 4.6 calls per daily run:

**1. Per-competitor daily snapshot** (`build_daily_snapshot`)
- Fetches yesterday's `raw_events` for one competitor (capped at ~60K chars)
- System prompt built at runtime from `COMPANY_NAME`, `COMPANY_INDUSTRY`, `COMPANY_DESCRIPTION`
- Returns JSON: `{summary, key_signals, sentiment_score, watch_items}`
- Upserted into `daily_snapshots`

**2. Cross-competitor comparison** (`build_comparison_report`)
- Reads all `daily_snapshots` across all competitors for the last 24 months
- Budgets context evenly across competitors (~80K chars total)
- Returns JSON: `{executive_narrative, competitor_rankings, market_themes, strategic_insights, hiring_signals, deal_activity, product_moves}`
- Both calls use `thinking: {type: "adaptive"}` and streaming to avoid timeouts

---

## Architecture decisions

- **`company.yaml` is gitignored** — competitive config is private; `company.example.yaml` is the committed template
- **All secrets in `.env`** — never in yaml or code
- **`config.py` is the only import** that touches both yaml and env — everything else imports from `config`
- **`--setup` defers config import** — the interactive wizard runs before `config.py` loads so it can create `company.yaml` from scratch
- **SQLite with WAL mode** — simple, no server, handles concurrent reads fine for this workload
- **Upserts everywhere** — all DB writes use `INSERT ... ON CONFLICT DO UPDATE` so re-running a day is safe
- **Firecrawl is optional** — agent degrades gracefully if `FIRECRAWL_API_KEY` is absent; Firehose covers most use cases alone
- **Streaming for Claude calls** — avoids HTTP timeouts on large 24-month context windows

---

## Adding a new data source

1. Create `scrapers/your_source.py` — return raw text, call `insert_raw_event()` with an appropriate `source_type`
2. Import and call it in `main.py` inside `run_daily_pipeline()`
3. No other changes needed — the analyzer picks up all `raw_events` regardless of source

## Adding a new competitor

Edit `company.yaml` — add an entry under `competitors:`. Then run
`python main.py --bootstrap` to sync the new Firehose rules. No code changes.

## Changing the Claude model

Set `CLAUDE_MODEL` in `config.py`. The agent uses `claude-opus-4-6` by default
with `thinking: {type: "adaptive"}`. Do not use `budget_tokens` — it is
deprecated on Opus 4.6 and Sonnet 4.6.
