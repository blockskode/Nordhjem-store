"""Load the 500 products into Firestore, each with its embedding.

For every product this writes one document products/{product_id} with
the product fields, the photo file (image_path), the exact text that
was embedded (embed_text) and its vector (embedding, 768 numbers,
normalised to length 1).

Why normalise: gemini-embedding-001 returns length-1 vectors only at
the full size (3072 numbers). Shortened to 768 numbers, a vector has
length about 0.59, so it is divided by its length here.

Run from the repo root (uses your Application Default Credentials):
    uv run python -m loaders.load_products
"""

import json
import math
from pathlib import Path

from google import genai
from google.cloud import firestore
from google.cloud.firestore_v1.vector import Vector
from google.genai import types

PROJECT = "nordhjemstore"
EMBED_LOCATION = "europe-west1"
EMBED_MODEL = "gemini-embedding-001"
DIMENSIONS = 768
EMBED_BATCH = 250   # most texts one embedding call accepts
WRITE_BATCH = 400   # Firestore allows at most 500 writes per batch

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def read_products() -> list[dict]:
    """Read the products and add the photo file of each.

    Returns:
        The 500 products, each with an extra "image_path" field.
    """
    images = json.loads((DATA_DIR / "product_images.json").read_text())
    products = []
    with open(DATA_DIR / "products.jsonl", encoding="utf-8") as file:
        for line in file:
            product = json.loads(line)
            product["image_path"] = "product-images/" + images[
                product["product_id"]]
            products.append(product)
    return products


def embed_text(product: dict) -> str:
    """Build the text that represents a product for the embedding.

    Args:
        product: one product's fields.

    Returns:
        Name, category, colour and description in one text, for
        example "KILGAARD mattress. Category: mattress. Colour: grey.
        Memory foam mattress ...".
    """
    category = product["category"].replace("_", " ")
    return (f"{product['name']}. Category: {category}. "
            f"Colour: {product['colour']}. {product['description']}")


def normalise(vector: list[float]) -> list[float]:
    """Scale a vector to length 1.

    Args:
        vector: any non-zero vector.

    Returns:
        The same direction with length 1.
    """
    length = math.sqrt(sum(x * x for x in vector))
    return [x / length for x in vector]


def embed_all(client: genai.Client, texts: list[str]) -> list[list[float]]:
    """Embed many texts, EMBED_BATCH at a time, as documents.

    Args:
        client: a Vertex AI client.
        texts: the texts to embed.

    Returns:
        One normalised vector per text, in the same order.
    """
    config = types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT",
                                      output_dimensionality=DIMENSIONS)
    vectors = []
    for start in range(0, len(texts), EMBED_BATCH):
        batch = texts[start:start + EMBED_BATCH]
        reply = client.models.embed_content(model=EMBED_MODEL,
                                            contents=batch, config=config)
        vectors.extend(normalise(e.values) for e in reply.embeddings)
        print(f"embedded {start + len(batch)} of {len(texts)}")
    return vectors


def write_all(db: firestore.Client, products: list[dict],
              texts: list[str], vectors: list[list[float]]) -> None:
    """Write one Firestore document per product, in batches.

    Args:
        db: a Firestore client.
        products: the products.
        texts: the embedded text of each product.
        vectors: the vector of each product.
    """
    collection = db.collection("products")
    for start in range(0, len(products), WRITE_BATCH):
        batch = db.batch()
        end = start + WRITE_BATCH
        for product, text, vector in zip(products[start:end],
                                         texts[start:end],
                                         vectors[start:end]):
            document = dict(product, embed_text=text,
                            embedding=Vector(vector))
            batch.set(collection.document(product["product_id"]), document)
        batch.commit()
        print(f"wrote {min(end, len(products))} of {len(products)}")


def main() -> None:
    """Read, embed and write all products."""
    products = read_products()
    texts = [embed_text(p) for p in products]
    client = genai.Client(vertexai=True, project=PROJECT,
                          location=EMBED_LOCATION)
    vectors = embed_all(client, texts)
    db = firestore.Client(project=PROJECT)
    write_all(db, products, texts, vectors)


if __name__ == "__main__":
    main()
