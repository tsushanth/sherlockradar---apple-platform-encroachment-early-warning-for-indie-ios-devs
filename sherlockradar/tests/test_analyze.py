from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from analyze import (
    ANALYSIS_TOOL,
    Alert,
    analyze_all,
    analyze_pair,
    build_user_message,
    parse_assessment,
)
from ingest import SourceDocument
from portfolio import App

SOURCE = SourceDocument(filename="wwdc_health.txt", text="New journaling feature in Health.")
APP = App(
    name="InkJournal",
    description="A journaling app with mood tracking.",
    key_features=["AI prompts", "Mood graph"],
)


def test_build_user_message_includes_source_and_app_details():
    message = build_user_message(SOURCE, APP)
    assert SOURCE.filename in message
    assert SOURCE.text in message
    assert APP.name in message
    assert APP.description in message
    for feature in APP.key_features:
        assert feature in message


def test_parse_assessment_returns_fields():
    tool_input = {
        "risk_score": 85,
        "overlap_summary": "Both do mood-tracked journaling.",
        "pivot_suggestion": "Lean into community prompts Apple lacks.",
    }
    risk_score, overlap_summary, pivot_suggestion = parse_assessment(tool_input)
    assert risk_score == 85
    assert overlap_summary == "Both do mood-tracked journaling."
    assert pivot_suggestion == "Lean into community prompts Apple lacks."


@pytest.mark.parametrize("bad_score", [-1, 101])
def test_parse_assessment_rejects_out_of_range_score(bad_score):
    with pytest.raises(ValueError):
        parse_assessment(
            {
                "risk_score": bad_score,
                "overlap_summary": "x",
                "pivot_suggestion": "y",
            }
        )


def _mock_client_with_response(tool_input: dict) -> MagicMock:
    tool_use_block = SimpleNamespace(type="tool_use", input=tool_input)
    response = SimpleNamespace(content=[tool_use_block])
    client = MagicMock()
    client.messages.create.return_value = response
    return client


def test_analyze_pair_builds_alert_from_tool_response():
    tool_input = {
        "risk_score": 90,
        "overlap_summary": "Health's Journal Insights duplicates InkJournal's mood graph.",
        "pivot_suggestion": "Add community-shared prompts and coach-facing exports.",
    }
    client = _mock_client_with_response(tool_input)

    alert = analyze_pair(client, SOURCE, APP, model="test-model")

    assert alert == Alert(
        source_filename=SOURCE.filename,
        app_name=APP.name,
        risk_score=90,
        overlap_summary=tool_input["overlap_summary"],
        pivot_suggestion=tool_input["pivot_suggestion"],
    )

    _, kwargs = client.messages.create.call_args
    assert kwargs["model"] == "test-model"
    assert kwargs["tools"] == [ANALYSIS_TOOL]
    assert kwargs["tool_choice"] == {"type": "tool", "name": "record_assessment"}
    assert kwargs["messages"][0]["role"] == "user"


def test_analyze_all_runs_full_cross_product():
    tool_input = {
        "risk_score": 10,
        "overlap_summary": "No overlap.",
        "pivot_suggestion": "No pivot needed.",
    }
    client = _mock_client_with_response(tool_input)

    sources = [SOURCE, SourceDocument(filename="other.txt", text="unrelated")]
    apps = [APP, App(name="TableTally", description="bill splitter", key_features=["split"])]

    alerts = analyze_all(client, sources, apps, model="test-model")

    assert len(alerts) == len(sources) * len(apps)
    assert client.messages.create.call_count == len(sources) * len(apps)
