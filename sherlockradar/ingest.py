"""Loads sample Apple-source documents from samples/sources/."""

from dataclasses import dataclass
from pathlib import Path

SOURCES_DIR = Path(__file__).parent / "samples" / "sources"


@dataclass(frozen=True)
class SourceDocument:
    filename: str
    text: str


def load_sources(sources_dir: Path = SOURCES_DIR) -> list[SourceDocument]:
    """Loads every .txt file in sources_dir as a SourceDocument, sorted by filename."""
    paths = sorted(sources_dir.glob("*.txt"))
    return [SourceDocument(filename=p.name, text=p.read_text()) for p in paths]
