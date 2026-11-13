"""The policy documents, read from data/policies/ and cut into sections.

Each file starts with a header between two "---" lines (doc_id, title,
topic, country, valid_from...). The text below it is split at every
"## " heading, so one section is one heading and its paragraphs.
"""

from dataclasses import dataclass
from functools import lru_cache

from api.catalog import DATA_DIR

POLICY_DIR = DATA_DIR / "policies"


@dataclass
class Section:
    """One heading of one policy document, with its text."""

    doc_id: str
    title: str          # the document's title
    heading: str        # this section's heading
    text: str
    topic: str
    countries: list[str]   # ["all"], or for example ["DK", "SE"]


def read_header(lines: list[str]) -> tuple[dict[str, str], int]:
    """Read the header between the two "---" lines.

    Args:
        lines: all lines of one file.

    Returns:
        The header fields, and the line number where the text starts.
    """
    header = {}
    end = lines.index("---", 1)
    for line in lines[1:end]:
        key, value = line.split(":", 1)
        header[key.strip()] = value.strip()
    return header, end + 1


def split_sections(header: dict[str, str], body: list[str]) -> list[Section]:
    """Cut a document's text into one Section per "## " heading.

    Args:
        header: the document's header fields.
        body: the lines after the header.

    Returns:
        The sections, in the order they appear.
    """
    countries = [c.strip() for c in header["country"].split(",")]
    sections = []
    heading = header["title"]   # text before the first "##"
    lines: list[str] = []
    for line in body + ["## (end)"]:
        if line.startswith("## "):
            text = "\n".join(lines).strip()
            if text:
                sections.append(Section(
                    doc_id=header["doc_id"], title=header["title"],
                    heading=heading, text=text, topic=header["topic"],
                    countries=countries))
            heading = line[3:].strip()
            lines = []
        elif not line.startswith("# "):
            lines.append(line)
    return sections


@lru_cache(maxsize=1)
def load_sections() -> list[Section]:
    """Read every policy document once and cut it into sections.

    Returns:
        All sections of all documents.
    """
    sections = []
    for path in sorted(POLICY_DIR.glob("*.md")):
        lines = path.read_text(encoding="utf-8").splitlines()
        header, start = read_header(lines)
        sections.extend(split_sections(header, lines[start:]))
    return sections
