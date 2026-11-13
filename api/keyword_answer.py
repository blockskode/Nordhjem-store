"""A keyword placeholder for the policy chat, used until api/rag.py works.

It does not write an answer. It finds the one section whose words
overlap most with the question and shows that section as it is. It
does not understand meaning, does not know which policy is the newest,
and never says "I don't know" when it should. Step 2 fixes all three.
"""

import re

from api.models import AskRequest, Source
from api.policies import Section, load_sections

WORD = re.compile(r"\w+")
# Small words that match everything and carry no meaning.
STOP_WORDS = {
    "a", "an", "the", "i", "my", "me", "you", "your", "we", "is", "are",
    "can", "do", "does", "to", "of", "in", "on", "for", "and", "or", "it",
    "how", "what", "much", "if", "with", "be", "will", "at", "from",
}
TOPIC_BONUS = 1   # the chosen topic counts as one extra shared word


def words(text: str) -> set[str]:
    """Split text into lower-case words, without the small ones.

    Args:
        text: any text.

    Returns:
        The distinct meaningful words.
    """
    return set(WORD.findall(text.lower())) - STOP_WORDS


def allowed(section: Section, request: AskRequest) -> bool:
    """Check that a section applies to the customer's country.

    Args:
        section: one policy section.
        request: the question, with the customer's country.

    Returns:
        True if the section is for all countries or for this one.
    """
    return "all" in section.countries or request.country in section.countries


def score(section: Section, request: AskRequest) -> int:
    """Count the question's words found in the section.

    Args:
        section: one policy section.
        request: the question, with the chosen topic.

    Returns:
        The number of shared words, plus a bonus for the chosen topic.
    """
    text = f"{section.title} {section.heading} {section.text}"
    shared = len(words(request.question) & words(text))
    if request.topic and section.topic == request.topic:
        shared += TOPIC_BONUS
    return shared


def plain_text(text: str) -> str:
    """Turn a section's Markdown into plain text for the chat.

    Removes the ** bold markers and joins lines that the file wrapped,
    keeping one line per list item.

    Args:
        text: the section text, as in the file.

    Returns:
        The same text, ready to show.
    """
    lines: list[str] = []
    for line in text.replace("**", "").splitlines():
        line = line.strip()
        if not line:
            lines.append("")
        elif lines and lines[-1] and not line.startswith("- "):
            lines[-1] += " " + line
        else:
            lines.append(line)
    return "\n".join(lines)


def answer(request: AskRequest) -> tuple[str, list[Source]]:
    """Return the best matching section as the answer.

    Args:
        request: the question, country and optional topic.

    Returns:
        The answer text and its source (none if nothing matched).
    """
    best, best_score = None, 0
    for section in load_sections():
        if not allowed(section, request):
            continue
        section_score = score(section, request)
        if section_score > best_score:
            best, best_score = section, section_score
    if best is None:
        return "I could not find anything about that.", []
    text = f"{best.heading}:\n{plain_text(best.text)}"
    return text, [Source(doc_id=best.doc_id, title=best.title)]
