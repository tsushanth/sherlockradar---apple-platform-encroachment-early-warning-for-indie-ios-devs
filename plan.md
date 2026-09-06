# SherlockRadar — Local MVP Scaffold Plan

## Goal of this MVP

Prove the core value in one local run: given a handful of Apple-source documents
(WWDC transcript excerpts, release notes, App Store Connect changelog entries,
beta OS diff notes) and a small portfolio of a developer's own apps, produce a
ranked list of "sherlocking risk" alerts — each with a risk score, an overlap
summary, and an AI-drafted pivot/differentiation suggestion.

No live ingestion, no accounts, no payment, no server. Just: static sample
documents in → LLM-scored, ranked alerts out, printed to the console and saved
as a markdown report.

## 1. Stack

**Python 3 CLI script, single package, no framework.**

- Python 3.11+, stdlib `argparse` for the CLI.
- `anthropic` SDK for the actual comparison/scoring/pivot-suggestion calls
  (this is the one piece of "AI" the product's value depends on — it cannot be
  faked without misrepresenting the demo).
- No embeddings, no vector DB, no scikit-learn: source documents and app
  descriptions are small enough for this demo that we hand raw text straight
  to the model and ask it to reason about overlap directly, returned as
  structured JSON (via a tool-call / forced JSON schema).
- No database: outputs are files (`report.md`, `report.json`) written to the
  local filesystem.
- `python-dotenv` to load `ANTHROPIC_API_KEY` from a local `.env` (not
  committed).

Rejected alternatives: Node/TS CLI (equally valid, but Python needs less
scaffolding for quick text-file wrangling); a small web UI (adds a server,
routing, and build step for zero additional proof of the core value — a CLI
table/report is sufficient to demonstrate the alerting logic).

## 2. Explicitly out of scope for this local MVP

- **Auth / accounts** — single implicit user (Sushanth), no login.
- **Billing / subscriptions** — not needed to prove the alerting logic works.
- **Hosting / deployment** — runs on a laptop via `python cli.py scan`.
- **Live ingestion** (scraping Apple's site, WWDC video/transcript APIs, App
  Store Connect API, TestFlight/beta OS diffing tools) — replaced with a
  handful of hand-written/pasted sample source documents that stand in for
  "already ingested" content. Wiring up real ingestion is a distinct,
  later problem (and mostly a scraping/API-integration problem, not the part
  that needs validating first).
- **Scheduling / continuous monitoring / cron** — one-shot `scan` run.
- **Notifications** (email, Slack, push) — alerts are printed/written to a
  file, not delivered anywhere.
- **Multi-tenant portfolio support** — one `apps.json` file, a 3–5 app subset
  of the 15-app portfolio is enough to demonstrate ranking/discrimination.
- **Persistence/history across runs** (diffing "new alerts since last scan")
  — each run is stateless and evaluates the full sample set fresh.
- **Vector search / embeddings pipeline** — sample corpus is small enough that
  direct LLM reasoning over raw text is simpler and just as demonstrative.

## 3. File / directory layout

```
sherlockradar/
  cli.py                 # entry point: `python cli.py scan [--min-score N]`
  ingest.py              # loads sample source docs from samples/sources/
  portfolio.py           # loads samples/apps.json
  analyze.py             # builds the comparison prompt per (source, app)
                          # pair, calls the Anthropic API, parses the
                          # structured JSON response (risk_score,
                          # overlap_summary, pivot_suggestion)
  report.py              # sorts results by risk_score desc, renders
                          # console table + writes report.md / report.json
  samples/
    sources/
      wwdc2026_session_health.txt
      release_notes_ios20.txt
      appstore_connect_changelog.txt
      beta_os_diff_notes.txt
    apps.json             # 3-5 apps from the portfolio: name, description,
                           # key features (hand-written, representative)
  tests/
    test_analyze.py       # mocks the Anthropic call; asserts prompt
                           # construction and response-JSON parsing
    test_report.py        # asserts sorting/filtering by min-score works
  requirements.txt         # anthropic, python-dotenv
  .env.example              # ANTHROPIC_API_KEY=
  README.md                 # how to set up + run the demo
```

## 4. Verification

**Automated:**
- `pytest tests/` — `test_analyze.py` mocks the Anthropic client so prompt
  building and JSON-response parsing are covered without live API calls;
  `test_report.py` checks ranking/threshold-filtering logic with fixed
  in-memory alert data.

**Manual run-through (the real proof):**
1. `pip install -r requirements.txt`, copy `.env.example` to `.env`, add a
   real `ANTHROPIC_API_KEY`.
2. Curate `samples/sources/` so at least one document contains an obvious,
   unambiguous overlap with one app in `samples/apps.json` (e.g., a WWDC
   excerpt describing a new system-level feature that duplicates a demo
   app's core feature) — this is the "should fire loudly" case.
3. Include at least one source/app pair with no plausible overlap — this is
   the "should stay quiet" case, proving the tool discriminates rather than
   flagging everything.
4. Run `python cli.py scan`.
5. Confirm: the high-overlap pair surfaces near the top with a high risk
   score, a coherent overlap summary, and a non-generic pivot suggestion; the
   unrelated pair is scored low / omitted under the default `--min-score`
   threshold; `report.md` and `report.json` are written and match the
   console output.
