"""Product search with embeddings. THIS IS YOUR EXERCISE (Step 1).

Read steps/01_embeddings/learn.pdf first. Fill in the functions marked
TODO, from top to bottom; each one is one step of the search. Check
your work from the repo root:

    uv run python steps/01_embeddings/check.py

Until search() works, the API uses a keyword search instead and the
page says "keyword placeholder". When check.py passes, restart the API
and the page says "your search".
"""

import sys
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import numpy as np
from google import genai
from google.cloud import firestore
from google.genai import types  # noqa: F401 - you need it in embed_query

# Lets you run this file directly: python3 api/search.py
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from api.models import Hit, SearchFilters  # noqa: E402

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
    """Create the Vertex AI client.

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
    db = firestore.Client(project=PROJECT) 
    idd, vector, category, price, colour = [], [], [], [], []
    for document in db.collection("products").stream():
        product = document.to_dict()
        idd.append(document.id)
        vector.append(list(product["embedding"]))
        category.append(product["category"])
        price.append(product["price_dkk"])
        colour.append(product["colour"])
    store_index = Index(ids=idd, vectors=np.array(vector), categories=np.array(category), 
                        prices=np.array(price), colours=np.array(colour))
    return store_index


def get_embed_query(text: str) -> np.ndarray:
    """Embed the customer's question.

    Args:
        text: the question.

    Returns:
        Its vector, 768 numbers (not yet normalised).
    """
    result = get_client().models.embed_content(
        model=EMBED_MODEL,
        contents=[text],
        
        config=types.EmbedContentConfig(
            task_type="RETRIEVAL_QUERY",
            output_dimensionality = DIMENSIONS
        )
       
    )
    return np.array(result.embeddings[0].values)


def normalise(vectors: np.ndarray) -> np.ndarray:
    """Scale vectors to length 1 (L2 norm).

    Args:
        vectors: one vector (1 dimension) or one vector per row
            (2 dimensions).

    Returns:
        The same shape, every vector with length 1.
    """
    vector_norm = np.linalg.norm(vectors, axis=-1, keepdims=True)
    normalised_vector = vectors/vector_norm
    return normalised_vector


def filter_products(index: Index, filters: SearchFilters) -> np.ndarray:
    """
    Mark which products pass the filters.

    Returns an array with one entry per product: True if the product
    meets every filter that is set, False if it does not.

    Example, with 4 products and the filters "sofa, at most 4000 kr":

        categories:  ["sofa", "sofa", "rug", "sofa"]
        prices:      [3000,   6500,   1200,  2500]

        sofa?        [True,   True,   False, True]
        <= 4000?     [True,   False,  True,  True]
        both (&):    [True,   False,  False, True]   <- returned

    With no filters set, every product passes: [True, True, True, True].

    Args:
        index: the products.
        filters: optional category and max price (None means "any").

    Returns:
        One True or False per product.
    """
    index_length = len(index.categories)
    filtered_array = np.ones(index_length, dtype=bool)
    if filters.category is not None:
        filtered_array =  filtered_array & (index.categories == filters.category)
    if filters.max_price is not None:
        filtered_array = filtered_array & (index.prices <= filters.max_price)
    if filters.colour is not None:
        filtered_array = filtered_array & (index.colours == filters.colour)
    return filtered_array


def get_top_k(scores: np.ndarray, k: int) -> list[int]:
    """Find the indices of the k highest scores, highest first.

    Args:
        scores: one score per product.
        k: how many to return.

    Returns:
        Row numbers, best first.
    """
    return np.argsort(scores)[::-1][:k]



def search(query: str, filters: SearchFilters, k: int) -> list[Hit]:
    """Find the k products closest in meaning to the query.

    Args:
        query: what the customer typed, for example "soft grey sofa".
        filters: optional category and max price; only return products
            that pass them.
        k: how many results to return at most.

        1 - load the indexes
        2 - get embedded query
        3 - normalise the embedded vector
        4 - compute the socore

    Returns:
        Up to k hits, best first. Each has a product ID and a score
        (cosine similarity: higher is closer).

    """
    index = load_index()
    embedding_query = get_embed_query(query)
    normalised_embedding_query = normalise(embedding_query)
    similarity_scores = index.vectors@normalised_embedding_query
    mask = filter_products(index, filters)
    scores = np.where(mask, similarity_scores, -np.inf)
    k = min(k, int(mask.sum()))  # never more hits than allowed products
    top_k = get_top_k(scores, k)
    return [Hit(product_id=index.ids[row], score=float(scores[row]))
            for row in top_k]


if __name__ == "__main__":

    for hit in search("a couch my guests can sleep on", SearchFilters(), 5):
        print(hit)



