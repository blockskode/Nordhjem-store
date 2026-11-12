"""A simple keyword search, used only until api/search.py works.

It counts how many of the query's words appear in a product's text.
It does not understand meaning: "couch" will not find a "sofa". That
gap is what the semantic search in Step 1 fixes.
"""

import re

from api.catalog import load_products
from api.models import Hit, SearchFilters

WORD = re.compile(r"\w+")


def words(text: str) -> set[str]:
    """Split text into a set of lower-case words.

    Args:
        text: any text.

    Returns:
        The distinct words, in lower case.
    """
    return set(WORD.findall(text.lower()))


def passes(product: dict, filters: SearchFilters) -> bool:
    """Check a product against the category and max-price filters.

    Args:
        product: one product's fields.
        filters: the filters to apply.

    Returns:
        True if the product is allowed.
    """
    if filters.category and product["category"] != filters.category:
        return False
    if filters.max_price and product["price_dkk"] > filters.max_price:
        return False
    return True


def product_text(product: dict) -> str:
    """Join the fields a customer might search for into one text.

    Args:
        product: one product's fields.

    Returns:
        Name, category, colour and description in one string.
    """
    parts = [product["name"], product["category"].replace("_", " "),
             product["colour"], product["description"]]
    return " ".join(parts)


def search(query: str, filters: SearchFilters, k: int) -> list[Hit]:
    """Rank products by the share of query words found in their text.

    Args:
        query: what the customer typed.
        filters: optional category and max price.
        k: how many results to return at most.

    Returns:
        Up to k hits, best first; products with no matching word are
        left out.
    """
    query_words = words(query)
    hits = []
    for product in load_products().values():
        if not passes(product, filters):
            continue
        found = query_words & words(product_text(product))
        if found:
            score = len(found) / len(query_words)
            hits.append(Hit(product_id=product["product_id"], score=score))
    hits.sort(key=lambda hit: hit.score, reverse=True)
    return hits[:k]
