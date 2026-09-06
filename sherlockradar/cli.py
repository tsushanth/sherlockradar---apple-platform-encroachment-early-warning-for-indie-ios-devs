#!/usr/bin/env python3
"""SherlockRadar CLI entry point: `python cli.py scan [--min-score N]`."""

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from analyze import DEFAULT_MODEL, analyze_all
from ingest import load_sources
from portfolio import load_apps
from report import rank_alerts, render_console_table, write_reports

OUT_DIR = Path(__file__).parent


def scan(min_score: int, model: str) -> int:
    load_dotenv()
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print(
            "ANTHROPIC_API_KEY is not set. Copy .env.example to .env and add "
            "your key.",
            file=sys.stderr,
        )
        return 1

    from anthropic import Anthropic

    client = Anthropic(api_key=api_key)

    sources = load_sources()
    apps = load_apps()
    print(f"Comparing {len(sources)} source documents against {len(apps)} apps "
          f"({len(sources) * len(apps)} pairs)...")

    alerts = analyze_all(client, sources, apps, model=model)
    ranked = rank_alerts(alerts, min_score=min_score)

    print()
    print(render_console_table(ranked))
    print()

    md_path, json_path = write_reports(ranked, OUT_DIR)
    print(f"Wrote {md_path} and {json_path}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="cli.py", description="SherlockRadar")
    subparsers = parser.add_subparsers(dest="command", required=True)

    scan_parser = subparsers.add_parser(
        "scan", help="Compare sample Apple sources against the sample app portfolio"
    )
    scan_parser.add_argument(
        "--min-score",
        type=int,
        default=50,
        help="Minimum risk score (0-100) to include in the report (default: 50)",
    )
    scan_parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"Anthropic model to use (default: {DEFAULT_MODEL})",
    )

    args = parser.parse_args()
    if args.command == "scan":
        return scan(min_score=args.min_score, model=args.model)
    return 1


if __name__ == "__main__":
    sys.exit(main())
