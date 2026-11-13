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

from api.models import Category, Colour, SearchFilters

PROJECT = "nordhjemstore"
TEXT_LOCATION = "global"
TEXT_MODEL = "gemini-3-flash-preview"


class ParsedQuery(BaseModel):
    """What the text model reads out of the customer's words.

    This class is the form Gemini must fill in: it is passed as the
    response_schema, so the reply always has exactly these fields.
    """
    search_text: str
    category: Category | None
    colour: Colour | None
    max_price: float | None


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
    category = (clicked.category if clicked.category is not None
                else parsed.category)
    colour = clicked.colour if clicked.colour is not None else parsed.colour
    max_price = (clicked.max_price if clicked.max_price is not None
                 else parsed.max_price)
    return SearchFilters(category=category, colour=colour,
                         max_price=max_price)


INSTRUCTION = """You read what a customer typed in the search box of
Nordhjem, a furniture shop. Split it into four parts.

search_text: what the customer wants, in their own words, without the
price. Keep everything else, including sizes and counts.
category: one of sofa, mattress, rug, dining_table, office_chair,
garden, pillow, duvet. Set it only when the customer names the kind of
product. Other words and languages count: a bed or madras is a
mattress, a couch is a sofa, a dyne is a duvet, a Bürostuhl is an
office_chair. If the customer does not name a kind of product, use
null. Do not guess from the room, the use or the feeling: "something
soft for the bedroom" has no category.

colour: one of blue, rust, dark green, beige, grey, black, white. Set it
only when the customer names a colour. Map close words to these: green
or olive is dark green, cream or sand is beige, navy is blue, orange or
terracotta is rust. Other languages count too: grøn and grün are dark
green. If no colour is named, use null.

max_price: the highest price in Danish kroner the customer accepts, as
a number. The currency may be written as kr, kroner, dkk, or not at
all. Only a price counts: a size such as 180x200 or a count such as
"for 8 people" is never a price. With a range, use the upper end. If
no price is given, use null."""


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
    response = get_text_client().models.generate_content(
        model=TEXT_MODEL,
        contents=text,
        config=types.GenerateContentConfig(
            system_instruction=INSTRUCTION,
            response_mime_type="application/json",
            response_schema=ParsedQuery

        ) 
    )
    return response.parsed
