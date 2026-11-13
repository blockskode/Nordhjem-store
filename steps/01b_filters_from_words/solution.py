"""Reference solution for Step 1b: read the filters from the words.

Open this only after trying api/parse_query.py yourself, or when stuck
on one function. Run the checks on it from the repo root:

    python3 steps/01b_filters_from_words/check.py --solution
"""

from functools import lru_cache

from google import genai
from google.genai import types
from pydantic import BaseModel

from api.models import Category, SearchFilters

PROJECT = "nordhjemstore"
TEXT_LOCATION = "global"
TEXT_MODEL = "gemini-3-flash-preview"

INSTRUCTION = """You read what a customer typed in the search box of
Nordhjem, a furniture shop. Split it into three parts.

search_text: what the customer wants, in their own words, without the
price.

category: one of sofa, mattress, rug, dining_table, office_chair,
garden, pillow, duvet. Set it only when the customer names the kind of
product, in any language (a bed or madras is a mattress, a couch is a
sofa). If they do not name it, use null. Do not guess.

max_price: the highest price in Danish kroner the customer accepts, as
a number. Only set it for a price, never for a size or a count. With a
range, use the upper end. If no price is given, use null."""


class ParsedQuery(BaseModel):
    """What the text model reads out of the customer's words."""

    search_text: str
    category: Category | None
    max_price: float | None


@lru_cache(maxsize=1)
def get_text_client() -> genai.Client:
    """Create the client for the text model once.

    Returns:
        A client for Gemini on Vertex AI.
    """
    return genai.Client(vertexai=True, project=PROJECT,
                        location=TEXT_LOCATION)


@lru_cache(maxsize=256)
def parse_query(text: str) -> ParsedQuery:
    """Ask the text model to split the words into meaning and filters.

    Args:
        text: what the customer typed.

    Returns:
        The search text, and the category and max price if given.
    """
    config = types.GenerateContentConfig(
        system_instruction=INSTRUCTION,
        response_mime_type="application/json",
        response_schema=ParsedQuery,
    )
    reply = get_text_client().models.generate_content(
        model=TEXT_MODEL, contents=text, config=config)
    return reply.parsed


def merge_filters(clicked: SearchFilters,
                  parsed: ParsedQuery) -> SearchFilters:
    """Combine the clicked filters with the ones read from the words.

    A click wins, because it is the more deliberate choice.

    Args:
        clicked: the filters from the chips and the price menu.
        parsed: the filters read from the words.

    Returns:
        One SearchFilters for the search.
    """
    category = clicked.category
    if category is None:
        category = parsed.category
    max_price = clicked.max_price
    if max_price is None:
        max_price = parsed.max_price
    return SearchFilters(category=category, max_price=max_price)
