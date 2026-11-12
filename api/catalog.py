"""The product catalogue, read from the files in data/.

For now the products come from data/products.jsonl. Later they come
from Firestore (see docs/diagrams/fig-data-model-v1.png).
"""

import json
from functools import lru_cache
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


@lru_cache(maxsize=1)
def load_products() -> dict[str, dict]:
    """Read all products once and keep them in memory.

    Returns:
        A dict from product ID (for example "P1001") to its fields,
        with an extra "image_file" field taken from
        data/product_images.json.
    """
    images = json.loads((DATA_DIR / "product_images.json").read_text())
    products = {}
    with open(DATA_DIR / "products.jsonl", encoding="utf-8") as file:
        for line in file:
            product = json.loads(line)
            product["image_file"] = images[product["product_id"]]
            products[product["product_id"]] = product
    return products
