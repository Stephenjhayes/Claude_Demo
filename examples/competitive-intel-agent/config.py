"""
Competitor configuration and data-source URLs for the Guidewire competitive
intelligence agent.  All secrets are read from environment variables — never
hardcode API keys.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ── API keys ──────────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]

# Firehose (https://firehose.com) — primary real-time web mentions source (free)
# FIREHOSE_MGMT_KEY  : fhm_... key used to create taps and install rules (one-time bootstrap)
# FIREHOSE_TAP_TOKEN : fh_...  key used for streaming + rule queries (daily pulls)
# Run `python main.py --bootstrap` once to create the tap and get the tap token.
FIREHOSE_MGMT_KEY  = os.getenv("FIREHOSE_MGMT_KEY", "")
FIREHOSE_TAP_TOKEN = os.getenv("FIREHOSE_TAP_TOKEN", "")
FIREHOSE_TAP_NAME  = os.getenv("FIREHOSE_TAP_NAME", "guidewire-ci")

# Firecrawl — deep page scraping for structured content (product pages, careers)
# Falls back gracefully if key is absent.
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY", "")

NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")          # optional, enhances news coverage

# ── Model ─────────────────────────────────────────────────────────────────────
CLAUDE_MODEL = "claude-opus-4-6"

# ── Storage ───────────────────────────────────────────────────────────────────
DB_PATH = os.getenv("INTEL_DB_PATH", "competitive_intel.db")
REPORTS_DIR = os.getenv("REPORTS_DIR", "reports")
RETENTION_MONTHS = 24          # keep 24 months of history

# ── Competitors ───────────────────────────────────────────────────────────────
COMPETITORS = {
    "duck_creek": {
        "name": "Duck Creek Technologies",
        "press_room": "https://www.duckcreek.com/news/",
        "blog": "https://www.duckcreek.com/blog/",
        "products": "https://www.duckcreek.com/products/",
        "careers": "https://www.duckcreek.com/company/careers/",
        "ticker": None,                  # private (Vista Equity)
        "news_query": "Duck Creek Technologies insurance",
    },
    "sapiens": {
        "name": "Sapiens International",
        "press_room": "https://www.sapiens.com/news-room/",
        "blog": "https://www.sapiens.com/blog/",
        "products": "https://www.sapiens.com/solution/",
        "careers": "https://www.sapiens.com/about/careers/",
        "ticker": "SPNS",
        "news_query": "Sapiens International insurance software",
    },
    "majesco": {
        "name": "Majesco",
        "press_room": "https://www.majesco.com/news/",
        "blog": "https://www.majesco.com/blog/",
        "products": "https://www.majesco.com/solutions/",
        "careers": "https://www.majesco.com/company/careers/",
        "ticker": "MJCO",
        "news_query": "Majesco insurance platform cloud",
    },
    "insurity": {
        "name": "Insurity",
        "press_room": "https://www.insurity.com/news/",
        "blog": "https://www.insurity.com/blog/",
        "products": "https://www.insurity.com/solutions/",
        "careers": "https://www.insurity.com/careers/",
        "ticker": None,                  # private (GI Partners)
        "news_query": "Insurity insurance software P&C",
    },
    "applied_systems": {
        "name": "Applied Systems",
        "press_room": "https://www1.appliedsystems.com/en-us/news/",
        "blog": "https://www1.appliedsystems.com/en-us/company/blog/",
        "products": "https://www1.appliedsystems.com/en-us/solutions/",
        "careers": "https://www1.appliedsystems.com/en-us/company/careers/",
        "ticker": None,                  # private
        "news_query": "Applied Systems insurance agency management",
    },
    "one_shield": {
        "name": "OneShield Software",
        "press_room": "https://www.oneshield.com/news/",
        "blog": "https://www.oneshield.com/blog/",
        "products": "https://www.oneshield.com/solutions/",
        "careers": "https://www.oneshield.com/company/careers/",
        "ticker": None,
        "news_query": "OneShield insurance policy administration",
    },
}

# ── Firecrawl scraping targets per competitor ─────────────────────────────────
# Ordered by priority; scraper will attempt each in turn.
SCRAPE_TARGETS = ["press_room", "blog", "products"]

# ── Firehose pull window ──────────────────────────────────────────────────────
# How far back to replay the Firehose buffer on each daily run.
# Firehose buffers up to 24h; use "24h" for a full day of mentions.
FIREHOSE_SINCE = os.getenv("FIREHOSE_SINCE", "24h")
FIREHOSE_MAX_EVENTS = int(os.getenv("FIREHOSE_MAX_EVENTS", "5000"))

# ── SEC EDGAR ─────────────────────────────────────────────────────────────────
SEC_EDGAR_BASE = "https://www.sec.gov"
SEC_COMPANY_SEARCH = "https://efts.sec.gov/LATEST/search-index?q={query}&dateRange=custom&startdt={start}&enddt={end}&forms=10-K,10-Q,8-K"

# ── Scheduling ────────────────────────────────────────────────────────────────
DAILY_RUN_HOUR = 6     # run at 06:00 UTC every day
DAILY_RUN_MINUTE = 0
