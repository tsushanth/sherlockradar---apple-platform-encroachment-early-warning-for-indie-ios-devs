# SherlockRadar

A local MVP that proves out the core value of SherlockRadar: given a handful
of Apple-source documents (WWDC session excerpts, developer release notes,
App Store Connect changelog entries, beta OS diff notes) and a developer's
own app portfolio, it produces a ranked list of "sherlocking risk" alerts —
each with a risk score (0-100), a summary of the overlapping functionality,
and an AI-drafted pivot/differentiation suggestion.

This is a **local, one-shot CLI demo** — see [`plan.md`](plan.md) for the
full scope and what's deliberately left out (auth, billing, hosting, live
ingestion, scheduling, notifications, multi-tenant support, and
history-across-runs are all out of scope for this MVP; see plan.md section 2
for the reasoning behind each).

## How it works

1. `ingest.py` loads sample Apple-source documents from
   `sherlockradar/samples/sources/`.
2. `portfolio.py` loads a 5-app subset of the developer's portfolio from
   `sherlockradar/samples/apps.json`.
3. `analyze.py` builds one comparison prompt per (source document, app) pair
   and calls the Anthropic API, forcing a structured tool-call response with
   `risk_score`, `overlap_summary`, and `pivot_suggestion`.
4. `report.py` ranks all alerts by risk score, filters by a minimum
   threshold, and renders both a console table and `report.md` /
   `report.json`.

The sample data is deliberately curated to include both an obvious,
loud-firing overlap (a new Health app journaling/mood feature vs. the sample
`InkJournal` app, and a new Measure app room-scanning feature vs. the sample
`SnapMeasure` app) and clearly unrelated pairs (e.g. an App Store Connect
Game Center changelog vs. a bill-splitting app), to demonstrate that the
tool discriminates rather than flagging everything.

## Setup

```bash
cd sherlockradar
pip install -r requirements.txt
cp .env.example .env
# edit .env and set ANTHROPIC_API_KEY=sk-ant-...
```

## Run the demo

```bash
python cli.py scan
```

Optional flags:

```bash
python cli.py scan --min-score 30   # lower the alert threshold (default: 50)
python cli.py scan --model claude-sonnet-5  # override the model
```

This prints a ranked console table and writes `report.md` and `report.json`
into the `sherlockradar/` directory.

## Tests

```bash
cd sherlockradar
pytest tests/
```

Tests mock the Anthropic client, so `pytest` runs without an API key and
without any network calls. They cover prompt construction, response
parsing, and the ranking/filtering logic in isolation.
