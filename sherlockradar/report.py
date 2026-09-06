"""Sorts alerts by risk score, filters by threshold, renders a console table,
and writes report.md / report.json."""

import json
from dataclasses import asdict
from pathlib import Path

from analyze import Alert


def rank_alerts(alerts: list[Alert], min_score: int = 0) -> list[Alert]:
    """Filters alerts below min_score and sorts the rest by risk_score desc."""
    kept = [a for a in alerts if a.risk_score >= min_score]
    return sorted(kept, key=lambda a: a.risk_score, reverse=True)


def render_console_table(alerts: list[Alert]) -> str:
    """Renders a fixed-width text table of alerts for terminal output."""
    if not alerts:
        return "No alerts at or above the given risk threshold."

    header = f"{'RISK':>4}  {'APP':<14}  {'SOURCE':<32}  OVERLAP SUMMARY"
    lines = [header, "-" * len(header)]
    for a in alerts:
        summary = a.overlap_summary
        if len(summary) > 60:
            summary = summary[:57] + "..."
        lines.append(f"{a.risk_score:>4}  {a.app_name:<14}  {a.source_filename:<32}  {summary}")
    return "\n".join(lines)


def render_markdown(alerts: list[Alert]) -> str:
    """Renders the full alert list as a markdown report with pivot suggestions."""
    lines = ["# SherlockRadar Report", ""]
    if not alerts:
        lines.append("No alerts at or above the given risk threshold.")
        return "\n".join(lines)

    for a in alerts:
        lines.append(f"## {a.app_name} — risk {a.risk_score}/100")
        lines.append(f"**Source:** `{a.source_filename}`")
        lines.append("")
        lines.append(f"**Overlap:** {a.overlap_summary}")
        lines.append("")
        lines.append(f"**Suggested pivot:** {a.pivot_suggestion}")
        lines.append("")
    return "\n".join(lines)


def write_reports(alerts: list[Alert], out_dir: Path) -> tuple[Path, Path]:
    """Writes report.md and report.json to out_dir; returns their paths."""
    out_dir.mkdir(parents=True, exist_ok=True)
    md_path = out_dir / "report.md"
    json_path = out_dir / "report.json"
    md_path.write_text(render_markdown(alerts))
    json_path.write_text(json.dumps([asdict(a) for a in alerts], indent=2))
    return md_path, json_path
