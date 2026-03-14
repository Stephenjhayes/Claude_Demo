"""
Guidewire Competitive Intelligence Agent
========================================

Daily-running agent that:
  1. Scrapes competitor press rooms, blogs, and careers pages via Firecrawl
  2. Pulls news via NewsAPI and SEC filings via EDGAR
  3. Asks Claude Opus 4.6 to analyse each competitor's daily signals
  4. Produces a 24-month cross-competitor comparison report
  5. Writes an HTML executive report + a markdown Slack digest

Usage
-----
  # Run once (immediately)
  python main.py --run-now

  # Start the daily scheduler (runs at 06:00 UTC)
  python main.py --schedule

  # Back-fill news for the last 30 days (useful on first run)
  python main.py --run-now --news-days 30

  # Comparison report only (no new scraping)
  python main.py --report-only

Environment variables required:
  ANTHROPIC_API_KEY
  FIRECRAWL_API_KEY

Optional:
  NEWS_API_KEY      — enhances news coverage via newsapi.org
  INTEL_DB_PATH     — defaults to ./competitive_intel.db
  REPORTS_DIR       — defaults to ./reports
"""

import argparse
import logging
import sys
from datetime import date, datetime

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from config import DAILY_RUN_HOUR, DAILY_RUN_MINUTE, RETENTION_MONTHS
from storage.database import init_db, purge_old_records
from scrapers.firecrawl_scraper import scrape_all_competitors, scrape_job_postings
from scrapers.news_scraper import fetch_all_competitor_news, fetch_all_sec_filings
from analysis.analyzer import build_all_daily_snapshots, build_comparison_report
from reports.report_generator import (
    generate_html_report,
    generate_daily_digest_markdown,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("competitive_intel.log"),
    ],
)
log = logging.getLogger("main")


def run_daily_pipeline(
    *,
    news_days: int = 1,
    skip_scraping: bool = False,
    report_only: bool = False,
) -> None:
    """Full daily pipeline — scrape → analyse → report."""
    today = date.today().isoformat()
    log.info("=" * 60)
    log.info("Competitive Intel Daily Run — %s", today)
    log.info("=" * 60)

    # ── 0. DB init & housekeeping ─────────────────────────────────
    init_db()
    purge_old_records()

    if not report_only:
        # ── 1. Scrape web properties via Firecrawl ────────────────
        if not skip_scraping:
            log.info("Phase 1: Web scraping via Firecrawl")
            try:
                web_counts = scrape_all_competitors()
                log.info("Firecrawl totals: %s", web_counts)

                job_counts = scrape_job_postings()
                log.info("Careers scraping: %s", job_counts)
            except Exception as exc:
                log.error("Firecrawl phase failed: %s", exc)

        # ── 2. News & SEC filings ─────────────────────────────────
        log.info("Phase 2: News & SEC filings (last %d days)", news_days)
        try:
            news_counts = fetch_all_competitor_news(days_back=news_days)
            log.info("News totals: %s", news_counts)

            sec_days = max(news_days, 7)
            sec_counts = fetch_all_sec_filings(days_back=sec_days)
            log.info("SEC filings: %s", sec_counts)
        except Exception as exc:
            log.error("News/SEC phase failed: %s", exc)

        # ── 3. Per-competitor daily snapshots ─────────────────────
        log.info("Phase 3: Claude Opus 4.6 — daily competitor snapshots")
        try:
            snapshots = build_all_daily_snapshots(
                snapshot_date=today,
                lookback_days=news_days,
            )
            log.info("Snapshots built for %d competitors", len(snapshots))
        except Exception as exc:
            log.error("Snapshot phase failed: %s", exc)
            snapshots = {}

        # ── 4. Daily markdown digest ──────────────────────────────
        if snapshots:
            try:
                md_path = generate_daily_digest_markdown(snapshots, digest_date=today)
                log.info("Daily digest written to: %s", md_path)
            except Exception as exc:
                log.error("Digest generation failed: %s", exc)

    # ── 5. Cross-competitor comparison report (24 months) ─────────
    log.info("Phase 4: Claude Opus 4.6 — 24-month comparison report")
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
            log.info("HTML report written to: %s", html_path)

            # Persist the report record
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
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--run-now",
        action="store_true",
        help="Run the full pipeline immediately then exit",
    )
    group.add_argument(
        "--schedule",
        action="store_true",
        help=f"Start the daily scheduler (runs at {DAILY_RUN_HOUR:02d}:{DAILY_RUN_MINUTE:02d} UTC)",
    )
    parser.add_argument(
        "--news-days",
        type=int,
        default=1,
        help="How many days of news/SEC data to pull (default: 1)",
    )
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="Skip scraping; only run the comparison report on existing DB data",
    )
    parser.add_argument(
        "--skip-scraping",
        action="store_true",
        help="Skip Firecrawl scraping; only pull news + run analysis",
    )
    return parser.parse_args()


def main():
    args = _parse_args()

    if args.run_now:
        run_daily_pipeline(
            news_days=args.news_days,
            skip_scraping=args.skip_scraping,
            report_only=args.report_only,
        )
        return

    if args.schedule:
        log.info(
            "Starting scheduler — will run daily at %02d:%02d UTC",
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

    # Default: print help if no flags given
    log.info("No action specified. Use --run-now or --schedule.")
    log.info("Run 'python main.py --help' for usage.")


if __name__ == "__main__":
    main()
