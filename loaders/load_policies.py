"""Load the policy documents into Firestore as chunks with embeddings.

A chunk is one section of one document: a "## " heading and its
paragraphs (see api/policies.py). For every chunk this writes one
document policy_chunks/{doc_id}-{n} with its fields, the exact text
that was embedded (embed_text) and its vector (embedding, 768 numbers,
normalised to length 1).

Old chunks are deleted first, so the collection always matches
data/policies/.

Run from the repo root (uses your Application Default Credentials):
    uv run python -m loaders.load_policies
"""

from dataclasses import asdict

from google import genai
from google.cloud import firestore
from google.cloud.firestore_v1.vector import Vector

from api.policies import Section, load_sections
from loaders.load_products import (
    EMBED_LOCATION, PROJECT, WRITE_BATCH, embed_all,
)

COLLECTION = "policy_chunks"


def embed_text(section: Section) -> str:
    """Build the text that is embedded for one chunk.

    The document title and the heading are included, because a heading
    such as "Price and time" means little without "Delivery in Sweden".

    Args:
        section: one policy section.

    Returns:
        Title, heading and text in one string.
    """
    return f"{section.title}. {section.heading}.\n{section.text}"


def delete_old(db: firestore.Client) -> None:
    """Delete every document in the chunk collection.

    Args:
        db: a Firestore client.
    """
    old = list(db.collection(COLLECTION).list_documents())
    for start in range(0, len(old), WRITE_BATCH):
        batch = db.batch()
        for document in old[start:start + WRITE_BATCH]:
            batch.delete(document)
        batch.commit()
    print(f"deleted {len(old)} old chunks")


def write_all(db: firestore.Client, sections: list[Section],
              texts: list[str], vectors: list[list[float]]) -> None:
    """Write one Firestore document per chunk.

    Args:
        db: a Firestore client.
        sections: the chunks.
        texts: the embedded text of each chunk.
        vectors: the vector of each chunk.
    """
    collection = db.collection(COLLECTION)
    count: dict[str, int] = {}
    batch = db.batch()
    for section, text, vector in zip(sections, texts, vectors):
        count[section.doc_id] = count.get(section.doc_id, 0) + 1
        chunk_id = f"{section.doc_id}-{count[section.doc_id]}"
        document = dict(asdict(section), embed_text=text,
                        embedding=Vector(vector))
        batch.set(collection.document(chunk_id), document)
    batch.commit()
    print(f"wrote {len(sections)} chunks")


def main() -> None:
    """Read, embed and write all policy chunks."""
    sections = load_sections()
    texts = [embed_text(s) for s in sections]
    client = genai.Client(vertexai=True, project=PROJECT,
                          location=EMBED_LOCATION)
    vectors = embed_all(client, texts)
    db = firestore.Client(project=PROJECT)
    delete_old(db)
    write_all(db, sections, texts, vectors)


if __name__ == "__main__":
    main()
