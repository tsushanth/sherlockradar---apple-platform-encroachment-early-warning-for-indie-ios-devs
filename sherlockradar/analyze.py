"""Builds the comparison prompt per (source, app) pair, calls the Anthropic
API, and parses the structured JSON response into an Alert."""

from dataclasses import dataclass

from ingest import SourceDocument
from portfolio import App

DEFAULT_MODEL = "claude-sonnet-5"

SYSTEM_PROMPT = """You are SherlockRadar, an analyst that helps indie iOS \
developers spot when Apple is about to ship a first-party feature that \
competes with ("sherlocks") their app.

You will be given one Apple-source document (a WWDC session transcript \
excerpt, developer release notes, an App Store Connect changelog entry, or \
beta OS diff notes) and one description of a developer's existing app.

Judge how much the functionality described in the source document overlaps \
with, replicates, or subsumes the app's core value proposition. Be a strict, \
skeptical judge: most Apple announcements do NOT meaningfully compete with \
any given third-party app, and you must give those pairs a low score rather \
than inventing a tenuous connection. Only score highly when the overlap is \
concrete and specific, not a vague thematic resemblance.

Respond by calling the record_assessment tool exactly once."""

ANALYSIS_TOOL = {
    "name": "record_assessment",
    "description": (
        "Records the sherlocking-risk assessment for one (source document, "
        "app) pair."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "risk_score": {
                "type": "integer",
                "minimum": 0,
                "maximum": 100,
                "description": (
                    "0-100 risk that this Apple source document describes a "
                    "feature that sherlocks the app. 0 = no plausible "
                    "overlap, 100 = Apple is shipping a near-exact "
                    "replacement of the app's core value proposition."
                ),
            },
            "overlap_summary": {
                "type": "string",
                "description": (
                    "1-3 sentences describing the specific overlapping "
                    "functionality, or the lack thereof."
                ),
            },
            "pivot_suggestion": {
                "type": "string",
                "description": (
                    "A concrete, non-generic pivot or differentiation "
                    "suggestion for the app in light of this source "
                    "document. If risk is low, state briefly why no pivot "
                    "is needed."
                ),
            },
        },
        "required": ["risk_score", "overlap_summary", "pivot_suggestion"],
    },
}


@dataclass(frozen=True)
class Alert:
    source_filename: str
    app_name: str
    risk_score: int
    overlap_summary: str
    pivot_suggestion: str


def build_user_message(source: SourceDocument, app: App) -> str:
    """Builds the user-turn text presenting one source/app pair for comparison."""
    features = "\n".join(f"- {f}" for f in app.key_features)
    return f"""## Apple source document ({source.filename})

{source.text}

## Developer's app: {app.name}

{app.description}

Key features:
{features}

Assess the sherlocking risk this source document poses to this app."""


def parse_assessment(tool_input: dict) -> tuple[int, str, str]:
    """Extracts and validates the three assessment fields from a tool_use input."""
    risk_score = int(tool_input["risk_score"])
    if not 0 <= risk_score <= 100:
        raise ValueError(f"risk_score out of range: {risk_score}")
    return risk_score, tool_input["overlap_summary"], tool_input["pivot_suggestion"]


def analyze_pair(client, source: SourceDocument, app: App, model: str = DEFAULT_MODEL) -> Alert:
    """Calls the Anthropic API for one (source, app) pair and returns an Alert."""
    response = client.messages.create(
        model=model,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        tools=[ANALYSIS_TOOL],
        tool_choice={"type": "tool", "name": "record_assessment"},
        messages=[{"role": "user", "content": build_user_message(source, app)}],
    )
    tool_use = next(block for block in response.content if block.type == "tool_use")
    risk_score, overlap_summary, pivot_suggestion = parse_assessment(tool_use.input)
    return Alert(
        source_filename=source.filename,
        app_name=app.name,
        risk_score=risk_score,
        overlap_summary=overlap_summary,
        pivot_suggestion=pivot_suggestion,
    )


def analyze_all(
    client,
    sources: list[SourceDocument],
    apps: list[App],
    model: str = DEFAULT_MODEL,
) -> list[Alert]:
    """Runs analyze_pair for the full cross-product of sources x apps."""
    return [
        analyze_pair(client, source, app, model=model)
        for source in sources
        for app in apps
    ]
