"""The API routes. No search logic here: each route checks its input,
calls one function and shapes the reply.

Run locally from the repo root:
    uv run uvicorn api.app:app --reload --port 8000
"""

import os
import time
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles

from api import keyword_search, search
from api.catalog import DATA_DIR, load_products
from api.keyword_search import passes
from api.models import (
    BrowseResponse, Category, Hit, ProductHit, SearchFilters,
    SearchRequest, SearchResponse,
)

# Where the page loads photos from; {file} is replaced by the file name.
# Locally the API serves data/images at /images. In production this is
# set to the Cloud Storage address, for example
# https://firebasestorage.googleapis.com/v0/b/BUCKET/o/product-images%2F{file}?alt=media
IMAGE_URL_TEMPLATE = os.environ.get("IMAGE_URL_TEMPLATE", "/images/{file}")

app = FastAPI(title="Nordhjem API")


@app.get("/api/health")
def health() -> dict[str, str]:
    """Say that the service is up.

    Returns:
        {"status": "ok"}.
    """
    return {"status": "ok"}


def run_search(request: SearchRequest) -> tuple[list[Hit], str]:
    """Use the owner's search if it works, else the keyword placeholder.

    Args:
        request: the validated search request.

    Returns:
        The hits, and the name of the engine that produced them.
    """
    filters = SearchFilters(category=request.category,
                            max_price=request.max_price)
    try:
        return search.search(request.query, filters, request.k), "your search"
    except NotImplementedError:
        hits = keyword_search.search(request.query, filters, request.k)
        return hits, "keyword placeholder"


def to_product_hit(product_id: str, score: float | None = None) -> ProductHit:
    """Build the fields the page shows for one product.

    Args:
        product_id: for example "P1001".
        score: the search score, or None when browsing.

    Returns:
        The full result for the page, including the photo address.
    """
    product = load_products()[product_id]
    return ProductHit(
        product_id=product_id,
        name=product["name"],
        category=product["category"],
        colour=product["colour"],
        price_dkk=product["price_dkk"],
        image_url=IMAGE_URL_TEMPLATE.format(file=product["image_file"]),
        score=None if score is None else round(score, 4),
    )


@app.post("/api/search")
def search_products(request: SearchRequest) -> SearchResponse:
    """Search the products and return them ready to show.

    Args:
        request: query, optional filters and k.

    Returns:
        The results, which engine answered, and the time taken.
    """
    start = time.perf_counter()
    hits, engine = run_search(request)
    took_ms = round((time.perf_counter() - start) * 1000)
    results = [to_product_hit(h.product_id, h.score) for h in hits]
    return SearchResponse(results=results,
                          engine=engine, took_ms=took_ms)


@app.get("/api/products")
def browse_products(
    category: Category | None = None,
    max_price: float | None = Query(default=None, gt=0),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=24, ge=1, le=96),
) -> BrowseResponse:
    """Return one page of the catalogue, without a search.

    Args:
        category: only this category, if given.
        max_price: only products at or below this price, if given.
        offset: how many matching products to skip.
        limit: how many to return.

    Returns:
        The products on this page, and how many match in total.
    """
    filters = SearchFilters(category=category, max_price=max_price)
    ids = [pid for pid, product in load_products().items()
           if passes(product, filters)]
    page = ids[offset:offset + limit]
    return BrowseResponse(results=[to_product_hit(pid) for pid in page],
                          total=len(ids))


@app.get("/api/products/{product_id}")
def get_product(product_id: str) -> dict:
    """Return all fields of one product.

    Args:
        product_id: for example "P1001".

    Returns:
        The product's fields.

    Raises:
        HTTPException: 404 if there is no such product.
    """
    product = load_products().get(product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="No such product")
    return product


images_dir = Path(DATA_DIR / "images")
if images_dir.is_dir():
    app.mount("/images", StaticFiles(directory=images_dir), name="images")
