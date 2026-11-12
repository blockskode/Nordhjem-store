"""The shapes of the data that goes in and out of the API.

These mirror web/src/types.ts; change both together.
"""

from typing import Literal

from pydantic import BaseModel, Field

Category = Literal[
    "sofa", "mattress", "rug", "dining_table",
    "office_chair", "garden", "pillow", "duvet",
]


class SearchFilters(BaseModel):
    """Optional limits on which products a search may return."""

    category: Category | None = None
    max_price: float | None = Field(default=None, gt=0)


class Hit(BaseModel):
    """One search result before it is shown: a product ID and its score."""

    product_id: str
    score: float


class SearchRequest(SearchFilters):
    """The body of POST /api/search."""

    query: str = Field(min_length=1, max_length=300)
    k: int = Field(default=24, ge=1, le=96)


class ProductHit(BaseModel):
    """One result as the page shows it."""

    product_id: str
    name: str
    category: Category
    colour: str
    price_dkk: float
    image_url: str
    score: float | None = None


class BrowseResponse(BaseModel):
    """The reply of GET /api/products: one page of the catalogue."""

    results: list[ProductHit]
    total: int


class SearchResponse(BaseModel):
    """The reply of POST /api/search."""

    results: list[ProductHit]
    engine: str
    took_ms: int
