"""Product search with embeddings. THIS IS YOUR EXERCISE (Step 1).

Until you write it, the API uses a simple keyword search instead
(api/keyword_search.py) and the page says "keyword placeholder".
"""

from api.models import Hit, SearchFilters


def search(query: str, filters: SearchFilters, k: int) -> list[Hit]:
    """Find the k products whose meaning is closest to the query.

    Args:
        query: what the customer typed, for example "soft grey sofa".
        filters: optional category and max price; only return products
            that pass them.
        k: how many results to return at most.

    Returns:
        Up to k hits, best first. Each has a product ID and a score
        (cosine similarity: higher is closer).

    Raises:
        NotImplementedError: until you write it.
    """
    raise NotImplementedError("Step 1: write the semantic search here")
