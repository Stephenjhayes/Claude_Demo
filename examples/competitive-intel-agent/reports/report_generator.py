"""
HTML and Markdown report generator — fully generic, driven by company.yaml.
"""

import json
import os
from datetime import date, datetime, timedelta
from pathlib import Path

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import REPORTS_DIR, COMPETITORS, COMPANY_NAME

THREAT_COLOUR = {
    "low": "#28a745",
    "medium": "#ffc107",
    "high": "#fd7e14",
    "critical": "#dc3545",
}
MOMENTUM_ICON = {
    "declining": "↘",
    "stable": "→",
    "growing": "↗",
    "accelerating": "🚀",
}

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{company_name} Competitive Intelligence Report — {report_date}</title>
<style>
  :root {{
    --primary: #003DA5;
    --primary-light: #E8EFF9;
    --text: #212529;
    --muted: #6c757d;
    --border: #dee2e6;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
         background: #f8f9fa; color: var(--text); line-height: 1.6; }}
  header {{ background: var(--primary); color: #fff; padding: 1.5rem 2rem; }}
  header h1 {{ font-size: 1.5rem; font-weight: 700; }}
  header p  {{ opacity: 0.8; font-size: 0.9rem; margin-top: 0.25rem; }}
  .container {{ max-width: 1100px; margin: 2rem auto; padding: 0 1rem; }}
  .card {{ background: #fff; border-radius: 8px; border: 1px solid var(--border);
           padding: 1.5rem; margin-bottom: 1.5rem; }}
  .card h2 {{ font-size: 1.1rem; color: var(--primary);
              border-bottom: 2px solid var(--primary-light);
              padding-bottom: 0.5rem; margin-bottom: 1rem; }}
  p {{ margin-bottom: 0.75rem; }}
  ul {{ padding-left: 1.25rem; margin-bottom: 0.75rem; }}
  li {{ margin-bottom: 0.35rem; }}
  .grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; }}
  .grid-3 {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; }}
  @media (max-width: 768px) {{ .grid-2, .grid-3 {{ grid-template-columns: 1fr; }} }}

  .ranking-table {{ width: 100%; border-collapse: collapse; font-size: 0.9rem; }}
  .ranking-table th {{ background: var(--primary-light); padding: 0.6rem 0.8rem;
                       text-align: left; font-weight: 600; }}
  .ranking-table td {{ padding: 0.6rem 0.8rem; border-bottom: 1px solid var(--border); }}
  .threat-badge {{ display: inline-block; padding: 0.2rem 0.6rem; border-radius: 12px;
                   font-size: 0.75rem; font-weight: 700; color: #fff; }}

  .insight {{ border-left: 4px solid var(--primary); padding: 0.75rem 1rem;
              background: var(--primary-light); border-radius: 0 6px 6px 0;
              margin-bottom: 0.75rem; }}
  .insight strong {{ display: block; margin-bottom: 0.25rem; }}
  .insight .rec {{ font-size: 0.85rem; color: var(--muted); margin-top: 0.35rem; }}

  .theme-card {{ border: 1px solid var(--border); border-radius: 6px;
                 padding: 1rem; background: #fff; margin-bottom: 0.75rem; }}
  .theme-card h4 {{ color: var(--primary); margin-bottom: 0.4rem; font-size: 0.9rem; }}
  .theme-card .drivers {{ font-size: 0.8rem; color: var(--muted); margin-bottom: 0.4rem; }}

  footer {{ text-align: center; padding: 2rem; color: var(--muted); font-size: 0.8rem; }}
</style>
</head>
<body>
<header>
  <h1>{company_name} — Competitive Intelligence Report</h1>
  <p>Period: {period_start} → {period_end} &nbsp;|&nbsp; Generated: {generated_at}</p>
</header>

<div class="container">

  <div class="card">
    <h2>Executive Summary</h2>
    {executive_narrative_html}
  </div>

  <div class="card">
    <h2>Competitor Threat &amp; Momentum Rankings</h2>
    <table class="ranking-table">
      <thead>
        <tr><th>#</th><th>Competitor</th><th>Threat Level</th><th>Momentum</th><th>Headline</th></tr>
      </thead>
      <tbody>{rankings_html}</tbody>
    </table>
  </div>

  <div class="grid-2">
    <div class="card">
      <h2>Emerging Market Themes</h2>
      {themes_html}
    </div>
    <div class="card">
      <h2>Strategic Insights &amp; Recommendations</h2>
      {insights_html}
    </div>
  </div>

  <div class="grid-3">
    <div class="card"><h2>Product Moves</h2><p>{product_moves}</p></div>
    <div class="card"><h2>Deal Activity</h2><p>{deal_activity}</p></div>
    <div class="card"><h2>Hiring Signals</h2><p>{hiring_signals}</p></div>
  </div>

</div>

<footer>
  {company_name} Competitive Intelligence &nbsp;|&nbsp;
  Claude Opus 4.6 + Ahrefs Firehose &nbsp;|&nbsp;
  {period_months}-month data window &nbsp;|&nbsp; {generated_at}
</footer>
</body>
</html>"""


def _paras(text: str) -> str:
    if not text:
        return "<p>No data available.</p>"
    return "".join(
        f"<p>{p.strip()}</p>" for p in text.split("\n\n") if p.strip()
    )


def _rankings_html(rankings: list[dict]) -> str:
    rows = []
    for i, r in enumerate(rankings, 1):
        threat = r.get("threat_level", "medium").lower()
        colour = THREAT_COLOUR.get(threat, "#6c757d")
        momentum = r.get("momentum", "stable").lower()
        icon = MOMENTUM_ICON.get(momentum, "→")
        rows.append(
            f"<tr>"
            f"<td>{i}</td>"
            f"<td><strong>{r.get('competitor', '')}</strong></td>"
            f"<td><span class='threat-badge' style='background:{colour}'>{threat.upper()}</span></td>"
            f"<td>{icon} {momentum}</td>"
            f"<td style='font-size:0.85rem'>{r.get('headline', '')}</td>"
            f"</tr>"
        )
    return "\n".join(rows) or "<tr><td colspan=5>No data</td></tr>"


def _themes_html(themes: list[dict]) -> str:
    cards = []
    for t in themes:
        drivers = ", ".join(t.get("competitors_driving", []))
        # The implication key name varies (Claude names it after the company)
        implication = next(
            (v for k, v in t.items() if "implication" in k.lower()), ""
        )
        cards.append(
            f"<div class='theme-card'>"
            f"<h4>{t.get('theme', '')}</h4>"
            f"<p class='drivers'>Driven by: {drivers}</p>"
            f"<p style='font-size:0.85rem'>{t.get('description', '')}</p>"
            + (f"<p style='font-size:0.82rem;color:var(--primary)'><em>{implication}</em></p>" if implication else "")
            + "</div>"
        )
    return "\n".join(cards) or "<p>No themes identified.</p>"


def _insights_html(insights: list[dict]) -> str:
    cards = []
    for ins in insights:
        cards.append(
            f"<div class='insight'>"
            f"<strong>{ins.get('insight', '')}</strong>"
            f"<p style='font-size:0.85rem'>{ins.get('evidence', '')}</p>"
            f"<p class='rec'>→ {ins.get('recommendation', '')}</p>"
            f"</div>"
        )
    return "\n".join(cards) or "<p>No insights generated.</p>"


def generate_html_report(
    comparison_data: dict,
    *,
    report_date: str | None = None,
    period_months: int = 24,
) -> str:
    """Render comparison_data into a self-contained HTML file. Returns file path."""
    target_date = report_date or date.today().isoformat()
    period_start = (
        datetime.strptime(target_date, "%Y-%m-%d") - timedelta(days=period_months * 30)
    ).strftime("%Y-%m-%d")
    generated_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    Path(REPORTS_DIR).mkdir(parents=True, exist_ok=True)
    filepath = os.path.join(REPORTS_DIR, f"competitive_intel_{target_date}.html")

    html = HTML_TEMPLATE.format(
        company_name=COMPANY_NAME,
        report_date=target_date,
        period_start=period_start,
        period_end=target_date,
        period_months=period_months,
        generated_at=generated_at,
        executive_narrative_html=_paras(comparison_data.get("executive_narrative", "")),
        rankings_html=_rankings_html(comparison_data.get("competitor_rankings", [])),
        themes_html=_themes_html(comparison_data.get("market_themes", [])),
        insights_html=_insights_html(comparison_data.get("strategic_insights", [])),
        product_moves=comparison_data.get("product_moves", "No data."),
        deal_activity=comparison_data.get("deal_activity", "No data."),
        hiring_signals=comparison_data.get("hiring_signals", "No data."),
    )

    with open(filepath, "w", encoding="utf-8") as fh:
        fh.write(html)
    return filepath


def generate_daily_digest_markdown(
    snapshots: dict[str, dict],
    *,
    digest_date: str | None = None,
) -> str:
    """Slack/email markdown digest of today's per-competitor snapshots."""
    target_date = digest_date or date.today().isoformat()
    Path(REPORTS_DIR).mkdir(parents=True, exist_ok=True)
    filepath = os.path.join(REPORTS_DIR, f"daily_digest_{target_date}.md")

    lines = [
        f"# {COMPANY_NAME} — Daily Competitive Digest — {target_date}",
        "",
        f"_Generated {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')} · Claude Opus 4.6 · Ahrefs Firehose_",
        "",
    ]

    for cid, data in snapshots.items():
        if not data:
            continue
        cfg = COMPETITORS.get(cid, {})
        sentiment = data.get("sentiment_score") or 0.0
        bar = "🔴" if sentiment < -0.3 else "🟡" if sentiment < 0.3 else "🟢"
        lines += [
            f"## {cfg.get('name', cid)}  {bar}",
            "",
            data.get("summary", "No summary."),
            "",
            "**Key Signals:**",
        ]
        for signal in data.get("key_signals", []):
            lines.append(f"- {signal}")
        if data.get("watch_items"):
            lines += ["", "**Watch:**"]
            for w in data["watch_items"]:
                lines.append(f"- ⚠️ {w}")
        lines.append("")

    with open(filepath, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    return filepath
