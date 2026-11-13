"""Read the filters out of the customer's words. YOUR EXERCISE (Step 1b).

"A very comfortable bed under 4000" should become:
    search_text = "A very comfortable bed"
    category    = "mattress"
    max_price   = 4000
so that your filter_products can drop everything above 4000 kr, even
when the customer never touches the price menu.

Read steps/01b_filters_from_words/learn.pdf first. Fill in the TODOs
from top to bottom, then check your work from the repo root:

    python3 steps/01b_filters_from_words/check.py

Until parse_query works, the API searches exactly as in Step 1.
"""

from functools import lru_cache

from google import genai
from google.genai import types  # noqa: F401 - you need it in parse_query
from pydantic import BaseModel

from api.models import Category, SearchFilters  # noqa: F401

PROJECT = "nordhjemstore"
TEXT_LOCATION = "global"
TEXT_MODEL = "gemini-3-flash-preview"


class ParsedQuery(BaseModel):
    """What the text model reads out of the customer's words.

    This class is the form Gemini must fill in: it is passed as the
    response_schema, so the reply always has exactly these fields.
    """

    search_text: str
    # TODO 1: add the two filter fields, with the same types as in
    #   SearchFilters (api/models.py), but with no default value:
    #   category is one of the 8 categories or None; max_price is a
    #   number or None. No default means Gemini must always fill them.


def merge_filters(clicked: SearchFilters,
                  parsed: ParsedQuery) -> SearchFilters:
    """Combine the clicked filters with the ones read from the words.

    A click wins, because it is the more deliberate choice.

    Example: the customer types "bed under 4000" and clicks the price
    menu at 2500. The words say 4000, the click says 2500: use 2500.

    Args:
        clicked: the filters from the chips and the price menu.
        parsed: the filters read from the words.

    Returns:
        One SearchFilters for the search.
    """
    # TODO 2: for the category, take the clicked one if it is not None,
    #   otherwise the parsed one. The same for max_price. Return a new
    #   SearchFilters(category=..., max_price=...).
    raise NotImplementedError("TODO 2: merge_filters")


# TODO 3: write the instruction for the text model, as plain English.
#   It is the only thing that tells Gemini what you mean. Say:
#   - what the three fields are;
#   - the 8 allowed categories, and that other words count too (a bed,
#     a madras, a couch...);
#   - only set a filter when the customer clearly says it: no guessing
#     (look at "something cosy for the living room floor" in
#     data/eval/filter_queries.json);
#   - max_price is a price in kroner, never a size ("180x200") or a
#     count ("for 8 people"); with a range, use the upper end.
INSTRUCTION = """"""


@lru_cache(maxsize=1)
def get_text_client() -> genai.Client:
    """Create the client for the text model once (given, no TODO).

    Returns:
        A client for Gemini on Vertex AI.
    """
    return genai.Client(vertexai=True, project=PROJECT,
                        location=TEXT_LOCATION)


@lru_cache(maxsize=256)
def parse_query(text: str) -> ParsedQuery:
    """Ask the text model to split the words into meaning and filters.

    @lru_cache remembers the answer per text, so "Show more" on the
    same search does not ask Gemini again.

    Args:
        text: what the customer typed.

    Returns:
        The search text, and the category and max price if given.
    """
    # TODO 4: call get_text_client().models.generate_content with
    #   model=TEXT_MODEL, contents=text and a
    #   types.GenerateContentConfig(...) holding three settings:
    #   system_instruction=INSTRUCTION,
    #   response_mime_type="application/json",
    #   response_schema=ParsedQuery.
    #   The reply has a .parsed attribute: a ready ParsedQuery. Return it.
    raise NotImplementedError("TODO 4: parse_query")
