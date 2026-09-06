from pathlib import Path

from analyze import Alert
from report import rank_alerts, render_console_table, render_markdown, write_reports

HIGH = Alert(
    source_filename="wwdc_health.txt",
    app_name="InkJournal",
    risk_score=90,
    overlap_summary="Health's Journal Insights duplicates InkJournal's mood graph.",
    pivot_suggestion="Add community-shared prompts and coach-facing exports.",
)
MEDIUM = Alert(
    source_filename="release_notes_ios20.txt",
    app_name="FocusFlow",
    risk_score=55,
    overlap_summary="Focus Filters add distraction budgets, overlapping partially.",
    pivot_suggestion="Differentiate on cross-device history and reporting.",
)
LOW = Alert(
    source_filename="appstore_connect_changelog.txt",
    app_name="TableTally",
    risk_score=5,
    overlap_summary="No plausible overlap with bill splitting.",
    pivot_suggestion="No pivot needed.",
)


def test_rank_alerts_sorts_by_score_descending():
    ranked = rank_alerts([MEDIUM, LOW, HIGH], min_score=0)
    assert [a.risk_score for a in ranked] == [90, 55, 5]


def test_rank_alerts_filters_below_min_score():
    ranked = rank_alerts([HIGH, MEDIUM, LOW], min_score=50)
    assert ranked == [HIGH, MEDIUM]


def test_rank_alerts_empty_when_all_below_threshold():
    ranked = rank_alerts([LOW], min_score=50)
    assert ranked == []


def test_render_console_table_empty():
    assert "No alerts" in render_console_table([])


def test_render_console_table_includes_app_and_score():
    table = render_console_table([HIGH])
    assert "InkJournal" in table
    assert "90" in table


def test_render_markdown_includes_pivot_suggestion():
    md = render_markdown([HIGH])
    assert "InkJournal" in md
    assert HIGH.pivot_suggestion in md


def test_write_reports_creates_matching_files(tmp_path: Path):
    md_path, json_path = write_reports([HIGH, MEDIUM], tmp_path)
    assert md_path.exists()
    assert json_path.exists()
    assert "InkJournal" in md_path.read_text()
    assert "FocusFlow" in json_path.read_text()
