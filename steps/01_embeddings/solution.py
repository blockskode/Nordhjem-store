"""Reference solution for Step 1: semantic product search with NumPy.

Open this only after trying api/search.py yourself, or when stuck on
one function. Run the checks on it from the repo root:

    uv run python steps/01_embeddings/check.py --solution
"""

from dataclasses import dataclass
from functools import lru_cache

import numpy as np
from google import genai
from google.cloud import firestore
from google.genai import types

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
    colours: np.ndarray      # shape (n,), text
    prices: np.ndarray       # shape (n,), DKK


@lru_cache(maxsize=1)
def get_client() -> genai.Client:
    """Create the Vertex AI client once.

    Returns:
        A client for the embedding model.
    """
    return genai.Client(vertexai=True, project=PROJECT,
                        location=EMBED_LOCATION)


@lru_cache(maxsize=1)
def load_index() -> Index:
    """Read every product from Firestore once and build the arrays.

    Returns:
        The index. The vectors were normalised by the loader.
    """
    db = firestore.Client(project=PROJECT)
    ids, vectors, categories, colours, prices = [], [], [], [], []
    for document in db.collection("products").stream():
        product = document.to_dict()
        ids.append(document.id)
        vectors.append(list(product["embedding"]))
        categories.append(product["category"])
        colours.append(product["colour"])
        prices.append(product["price_dkk"])
    return Index(ids=ids, vectors=np.array(vectors),
                 categories=np.array(categories),
                 colours=np.array(colours), prices=np.array(prices))


def get_embed_query(text: str) -> np.ndarray:
    """Embed the customer's question.

    Args:
        text: the question.

    Returns:
        Its vector, 768 numbers (not yet normalised).
    """
    config = types.EmbedContentConfig(task_type="RETRIEVAL_QUERY",
                                      output_dimensionality=DIMENSIONS)
    reply = get_client().models.embed_content(model=EMBED_MODEL,
                                              contents=[text], config=config)
    return np.array(reply.embeddings[0].values)


def normalise(vectors: np.ndarray) -> np.ndarray:
    """Scale vectors to length 1 (L2 norm).

    Args:
        vectors: one vector (1 dimension) or one vector per row
            (2 dimensions).

    Returns:
        The same shape, every vector with length 1.
    """
    lengths = np.linalg.norm(vectors, axis=-1, keepdims=True)
    return vectors / lengths


def filter_products(index: Index, filters: SearchFilters) -> np.ndarray:
    """Mark which products pass the filters.

    Args:
        index: the products.
        filters: optional category and max price.

    Returns:
        One True or False per product.
    """
    mask = np.ones(len(index.ids), dtype=bool)
    if filters.category is not None:
        mask &= index.categories == filters.category
    if filters.max_price is not None:
        mask &= index.prices <= filters.max_price
    if filters.colour is not None:
        mask &= index.colours == filters.colour
    return mask


def get_top_k(scores: np.ndarray, k: int) -> list[int]:
    """Find the positions of the k highest scores, highest first.

    Args:
        scores: one score per product.
        k: how many to return.

    Returns:
        Row numbers, best first.
    """
    order = np.argsort(scores)[::-1]
    return [int(i) for i in order[:k]]


def search(query: str, filters: SearchFilters, k: int) -> list[Hit]:
    """Find the k products closest in meaning to the query.

    Args:
        query: what the customer typed.
        filters: optional category and max price.
        k: how many results to return at most.

    Returns:
        Up to k hits, best first, each with its cosine similarity.
    """
    index = load_index()
    question = normalise(get_embed_query(query))
    scores = index.vectors @ question
    mask = filter_products(index, filters)
    scores = np.where(mask, scores, -np.inf)
    k = min(k, int(mask.sum()))
    return [Hit(product_id=index.ids[i], score=float(scores[i]))
            for i in get_top_k(scores, k)]
