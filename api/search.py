"""Product search with embeddings. THIS IS YOUR EXERCISE (Step 1).

Read steps/01_embeddings/learn.pdf first. Fill in the functions marked
TODO, from top to bottom; each one is one step of the search. Check
your work from the repo root:

    uv run python steps/01_embeddings/check.py

Until search() works, the API uses a keyword search instead and the
page says "keyword placeholder". When check.py passes, restart the API
and the page says "your search".
"""

from dataclasses import dataclass
from functools import lru_cache

import numpy as np
from google import genai
from google.cloud import firestore
from google.genai import types  # noqa: F401 - you need it in embed_query

from api.models import Hit, SearchFilters

PROJECT = "nordhjemstore"
EMBED_LOCATION = "europe-west1"
EMBED_MODEL = "gemini-embedding-001"
DIMENSIONS = 768


@dataclass
class Index:
    """The products as NumPy arrays; row i of every array is product i."""

    ids: list[str]
    vectors: np.ndarray      # shape (n, 768), every row length 1
    categories: np.ndarray   # shape (n,), text
    prices: np.ndarray       # shape (n,), DKK


@lru_cache(maxsize=1)
def get_client() -> genai.Client:
    """Create the Vertex AI client once (given, no TODO).

    Returns:
        A client for the embedding model.
    """
    return genai.Client(vertexai=True, project=PROJECT,
                        location=EMBED_LOCATION)


@lru_cache(maxsize=1)
def load_index() -> Index:
    """Read every product from Firestore once and build the arrays.

    @lru_cache keeps the result, so Firestore is read only on the first
    search, not on every search.

    Returns:
        The index. The vectors are already length 1 (the loader
        normalised them).
    """
    # TODO 1: read the "products" collection and fill four lists.
    #   db = firestore.Client(project=PROJECT)
    #   for document in db.collection("products").stream():
    #       product = document.to_dict()
    #       document.id is the product ID; product["embedding"] is a
    #       Firestore Vector: list(product["embedding"]) gives the 768
    #       numbers. Also keep product["category"] and
    #       product["price_dkk"].
    #   Return Index(...) with np.array(...) around the vectors,
    #   categories and prices.
    _ = firestore  # remove this line when you use firestore above
    raise NotImplementedError("TODO 1: load_index")


def embed_query(text: str) -> np.ndarray:
    """Embed the customer's question.

    Args:
        text: the question.

    Returns:
        Its vector, 768 numbers (not yet normalised).
    """
    # TODO 2: call get_client().models.embed_content with model
    #   EMBED_MODEL, contents=[text] and a types.EmbedContentConfig with
    #   task_type="RETRIEVAL_QUERY" and output_dimensionality=DIMENSIONS.
    #   Return np.array(...) of the values of the first embedding.
    raise NotImplementedError("TODO 2: embed_query")


def normalise(vectors: np.ndarray) -> np.ndarray:
    """Scale vectors to length 1 (L2 norm).

    Args:
        vectors: one vector (1 dimension) or one vector per row
            (2 dimensions).

    Returns:
        The same shape, every vector with length 1.
    """
    # TODO 3: divide by the length. np.linalg.norm with axis=-1 and
    #   keepdims=True works for both one vector and a matrix.
    raise NotImplementedError("TODO 3: normalise")


def allowed(index: Index, filters: SearchFilters) -> np.ndarray:
    """Mark which products pass the filters.

    Args:
        index: the products.
        filters: optional category and max price (None means "any").

    Returns:
        One True or False per product.
    """
    # TODO 4: start with all True (np.ones(..., dtype=bool)); if a
    #   category is given, keep only that category; if a max price is
    #   given, keep only prices <= max price. Combine with &.
    raise NotImplementedError("TODO 4: allowed")


def top_k(scores: np.ndarray, k: int) -> list[int]:
    """Find the positions of the k highest scores, highest first.

    Args:
        scores: one score per product.
        k: how many to return.

    Returns:
        Row numbers, best first.
    """
    # TODO 5: np.argsort sorts from low to high; reverse it, take k.
    raise NotImplementedError("TODO 5: top_k")


def search(query: str, filters: SearchFilters, k: int) -> list[Hit]:
    """Find the k products closest in meaning to the query.

    Args:
        query: what the customer typed, for example "soft grey sofa".
        filters: optional category and max price; only return products
            that pass them.
        k: how many results to return at most.

    Returns:
        Up to k hits, best first. Each has a product ID and a score
        (cosine similarity: higher is closer).
    """
    # TODO 6: put the pieces together (learn.pdf, section 7):
    #   index, the normalised question vector, all scores with one
    #   matrix product, -np.inf where not allowed, top_k, then Hit(...)
    #   for each row. Never return more hits than allowed products.
    raise NotImplementedError("TODO 6: search")
