"""Loads the developer's app portfolio from samples/apps.json."""

import json
from dataclasses import dataclass
from pathlib import Path

APPS_FILE = Path(__file__).parent / "samples" / "apps.json"


@dataclass(frozen=True)
class App:
    name: str
    description: str
    key_features: list[str]


def load_apps(apps_file: Path = APPS_FILE) -> list[App]:
    """Loads the app portfolio subset from a JSON file of app records."""
    raw = json.loads(apps_file.read_text())
    return [
        App(
            name=entry["name"],
            description=entry["description"],
            key_features=entry["key_features"],
        )
        for entry in raw
    ]
