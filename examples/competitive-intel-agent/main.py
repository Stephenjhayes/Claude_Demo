"""
Guidewire Competitive Intelligence Agent
========================================

Daily-running agent that:
  1. [Firehose]   Pulls 24h of web mentions via Ahrefs Firehose SSE API (primary)
  2. [Firecrawl]  Deep-scrapes competitor product pages and careers (supplemental)
  3. [News/SEC]   Pulls NewsAPI articles + SEC EDGAR filings
  4. [Claude]     Runs Claude Opus 4.6 (adaptive thinking) per-competitor daily snapshots
  5. [Claude]     Produces a 24-month cross-competitor comparison report
  6. [Reports]    Writes an HTML executive report + a markdown Slack/email digest

Data source hierarchy
---------------------
  Firehose (primary) — Ahrefs crawler coverage, real-time SSE, free, Lucene rules
  Firecrawl (deep)   — structured content extraction for product/careers pages
  NewsAPI   (news)   — additional press coverage
  SEC EDGAR (filing) — 10-K/10-Q/8-K for public competitors (Sapiens, Majesco)

Usage
-----
  # One-time setup: create Firehose tap + install competitor rules
  python main.py --bootstrap

  # Run the full pipeline immediately
  python main.py --run-now

  # Back-fill: pull all 24h Firehose buffer + last 30 days of news
  python main.py --run-now --news-days 30

  # Start the daily scheduler (runs at 06:00 UTC)
  python main.py --schedule

  # Comparison report only (no new scraping, uses existing DB data)
  python main.py --report-only

Environment variables required:
  ANTHROPIC_API_KEY
  FIREHOSE_MGMT_KEY   (fhm_... — for --bootstrap only)
  FIREHOSE_TAP_TOKEN  (fh_...  — for daily pulls)

Optional:
  FIRECRAWL_API_KEY, NEWS_API_KEY, INTEL_DB_PATH, REPORTS_DIR
"""

import argparse
import logging
import sys
from datetime import date

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from config import (
    DAILY_RUN_HOUR,
    DAILY_RUN_MINUTE,
    FIREHOSE_MGMT_KEY,
    FIREHOSE_TAP_TOKEN,
    FIREHOSE_TAP_NAME,
    FIREHOSE_SINCE,
    FIREHOSE_MAX_EVENTS,
    FIRECRAWL_API_KEY,
    RETENTION_MONTHS,
)
from storage.database import init_db, purge_old_records
from scrapers.firehose_scraper import bootstrap as firehose_bootstrap, pull_and_store_events
from scrapers.firecrawl_scraper import scrape_all_competitors, scrape_job_postings
from scrapers.news_scraper import fetch_all_competitor_news, fetch_all_sec_filings
from analysis.analyzer import build_all_daily_snapshots, build_comparison_report
from reports.report_generator import generate_html_report, generate_daily_digest_markdown

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("competitive_intel.log"),
    ],
)
log = logging.getLogger("main")


def run_bootstrap() -> None:
    """
    One-time setup: create the Firehose tap and install all competitor rules.
    Prints the tap token — save it to .env as FIREHOSE_TAP_TOKEN.
    """
    if not FIREHOSE_MGMT_KEY:
        log.error("FIREHOSE_MGMT_KEY is not set. Sign up at https://firehose.com and add it to .env")
        sys.exit(1)

    log.info("Bootstrapping Firehose tap '%s'...", FIREHOSE_TAP_NAME)
    tap_token = firehose_bootstrap(FIREHOSE_MGMT_KEY, FIREHOSE_TAP_NAME)
    print("\n" + "=" * 60)
    print(f"TAP TOKEN (save to .env as FIREHOSE_TAP_TOKEN):\n\n  {tap_token}\n")
    print("=" * 60 + "\n")
    log.info("Bootstrap complete. Rules are live — Firehose will now buffer mentions.")


def run_daily_pipeline(
    *,
    news_days: int = 1,
    skip_firehose: bool = False,
    skip_firecrawl: bool = False,
    report_only: bool = False,
) -> None:
    """Full daily pipeline — collect → analyse → report."""
    today = date.today().isoformat()
    log.info("=" * 60)
    log.info("Competitive Intel Daily Run — %s", today)
    log.info("=" * 60)

    # ── 0. DB init & housekeeping ─────────────────────────────────
    init_db()
    purge_old_records()

    if not report_only:
        # ── 1. Firehose — primary mention stream ──────────────────
        if not skip_firehose:
            if FIREHOSE_TAP_TOKEN:
                log.info("Phase 1: Firehose SSE pull (since=%s)", FIREHOSE_SINCE)
                try:
                    fh_counts = pull_and_store_events(
                        FIREHOSE_TAP_TOKEN,
                        since=FIREHOSE_SINCE,
                        max_events=FIREHOSE_MAX_EVENTS,
                    )
                    log.info("Firehose totals: %s", fh_counts)
                except Exception as exc:
                    log.error("Firehose pull failed: %s", exc)
            else:
                log.warning(
                    "FIREHOSE_TAP_TOKEN not set. Run `python main.py --bootstrap` first, "
                    "then add the token to .env"
                )

        # ── 2. Firecrawl — deep page scraping (supplemental) ──────
        if not skip_firecrawl and FIRECRAWL_API_KEY:
            log.info("Phase 2: Firecrawl deep scraping (product pages, careers)")
            try:
                web_counts = scrape_all_competitors()
                log.info("Firecrawl totals: %s", web_counts)

                job_counts = scrape_job_postings()
                log.info("Careers scraping: %s", job_counts)
            except Exception as exc:
                log.error("Firecrawl phase failed: %s", exc)
        elif not FIRECRAWL_API_KEY:
            log.info("Phase 2: Firecrawl skipped (FIRECRAWL_API_KEY not set)")

        # ── 3. News & SEC filings ─────────────────────────────────
        log.info("Phase 3: News & SEC filings (last %d days)", news_days)
        try:
            news_counts = fetch_all_competitor_news(days_back=news_days)
            log.info("News totals: %s", news_counts)

            sec_counts = fetch_all_sec_filings(days_back=max(news_days, 7))
            log.info("SEC filings: %s", sec_counts)
        except Exception as exc:
            log.error("News/SEC phase failed: %s", exc)

        # ── 4. Per-competitor daily snapshots ─────────────────────
        log.info("Phase 4: Claude Opus 4.6 — daily competitor snapshots")
        try:
            snapshots = build_all_daily_snapshots(
                snapshot_date=today,
                lookback_days=news_days,
            )
            log.info("Snapshots built for %d competitors", len(snapshots))
        except Exception as exc:
            log.error("Snapshot phase failed: %s", exc)
            snapshots = {}

        # ── 5. Daily markdown digest ──────────────────────────────
        if snapshots:
            try:
                md_path = generate_daily_digest_markdown(snapshots, digest_date=today)
                log.info("Daily digest → %s", md_path)
            except Exception as exc:
                log.error("Digest generation failed: %s", exc)

    # ── 6. Cross-competitor comparison report (24 months) ─────────
    log.info("Phase 5: Claude Opus 4.6 — 24-month comparison report")
    try:
        comparison = build_comparison_report(
            report_date=today,
            period_months=RETENTION_MONTHS,
        )
        if comparison:
            html_path = generate_html_report(
                comparison,
                report_date=today,
                period_months=RETENTION_MONTHS,
            )
            log.info("HTML report → %s", html_path)

            from storage.database import upsert_comparison
            upsert_comparison(
                report_date=today,
                period_months=RETENTION_MONTHS,
                narrative=comparison.get("executive_narrative", ""),
                insights=comparison.get("strategic_insights", []),
                html_path=html_path,
            )
    except Exception as exc:
        log.error("Comparison report phase failed: %s", exc)

    log.info("Daily pipeline complete — %s", today)


def _parse_args():
    parser = argparse.ArgumentParser(
        description="Guidewire Competitive Intelligence Agent"
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--bootstrap",
        action="store_true",
        help="One-time setup: create Firehose tap + install competitor rules",
    )
    mode.add_argument(
        "--run-now",
        action="store_true",
        help="Run the full pipeline immediately then exit",
    )
    mode.add_argument(
        "--schedule",
        action="store_true",
        help=f"Start the daily scheduler (runs at {DAILY_RUN_HOUR:02d}:{DAILY_RUN_MINUTE:02d} UTC)",
    )
    parser.add_argument(
        "--news-days",
        type=int,
        default=1,
        help="Days of news/SEC data to pull (default: 1; use 30 for first run)",
    )
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="Skip all data collection; only run the comparison report on existing DB data",
    )
    parser.add_argument(
        "--skip-firehose",
        action="store_true",
        help="Skip Firehose pull (useful for testing other phases)",
    )
    parser.add_argument(
        "--skip-firecrawl",
        action="store_true",
        help="Skip Firecrawl deep scraping",
    )
    return parser.parse_args()


def main():
    args = _parse_args()

    if args.bootstrap:
        run_bootstrap()
        return

    if args.run_now:
        run_daily_pipeline(
            news_days=args.news_days,
            skip_firehose=args.skip_firehose,
            skip_firecrawl=args.skip_firecrawl,
            report_only=args.report_only,
        )
        return

    if args.schedule:
        log.info(
            "Starting scheduler — daily at %02d:%02d UTC",
            DAILY_RUN_HOUR,
            DAILY_RUN_MINUTE,
        )
        scheduler = BlockingScheduler(timezone="UTC")
        scheduler.add_job(
            run_daily_pipeline,
            CronTrigger(hour=DAILY_RUN_HOUR, minute=DAILY_RUN_MINUTE),
            kwargs={"news_days": 1},
            id="daily_ci_pipeline",
            name="Competitive Intel Daily",
            replace_existing=True,
        )
        try:
            scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            log.info("Scheduler stopped.")
        return

    log.info("No action specified. Use --bootstrap, --run-now, or --schedule.")
    log.info("Run 'python main.py --help' for usage.")


if __name__ == "__main__":
    main()
