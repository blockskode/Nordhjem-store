"""Reference solution for Step 2: RAG over the policy documents.

Open this only after trying api/rag.py yourself, or when stuck on one
function. Run the checks on it from the repo root:

    python3 steps/02_rag/check.py --solution
"""

from dataclasses import dataclass
from datetime import date
from functools import lru_cache

import numpy as np
from google.cloud import firestore
from google.genai import types
from pydantic import BaseModel

from api.models import AskRequest, Source
from api.parse_query import TEXT_MODEL, get_text_client
from api.search import PROJECT, get_embed_query, get_top_k, normalise

K = 4               # chunks given to the text model
TOPIC_BONUS = 0.03  # extra score for chunks in the chosen topic
COUNTRY_NAMES = {"DK": "Denmark", "SE": "Sweden", "NO": "Norway",
                 "DE": "Germany"}

INSTRUCTION = """You answer customer questions for Nordhjem, a furniture
shop. Answer only from the sources given with the question.

- Use only facts that are in the sources. Never guess and never use
  outside knowledge.
- If the sources do not answer the question, say: "I don't know. Please
  contact customer service." and give no sources.
- Each source starts with its id in square brackets, such as
  [returns-2026]. In sources, list the ids of the sources you used.
- The customer's country is given. When the rules differ by country,
  use the rules for that country.
- Answer in the language of the question, in one to three short
  sentences, with the exact numbers from the sources."""


@dataclass
class ChunkIndex:
    """The policy chunks as lists and arrays; row i is chunk i."""

    ids: list[str]
    vectors: np.ndarray          # shape (n, 768), every row length 1
    doc_ids: list[str]
    titles: list[str]
    headings: list[str]
    texts: list[str]
    topics: np.ndarray           # shape (n,), text
    countries: list[list[str]]   # ["all"] or for example ["DK", "SE"]
    valid_from: list[str]        # "2026-01-01"
    valid_to: list[str | None]   # last day it applied, None if current


class RagAnswer(BaseModel):
    """The form the text model fills in."""

    answer: str
    sources: list[str]


@lru_cache(maxsize=1)
def load_chunks() -> ChunkIndex:
    """Read every policy chunk from Firestore once.

    Returns:
        The chunk index.
    """
    db = firestore.Client(project=PROJECT)
    rows = [(d.id, d.to_dict())
            for d in db.collection("policy_chunks").stream()]
    return ChunkIndex(
        ids=[i for i, _ in rows],
        vectors=np.array([list(c["embedding"]) for _, c in rows]),
        doc_ids=[c["doc_id"] for _, c in rows],
        titles=[c["title"] for _, c in rows],
        headings=[c["heading"] for _, c in rows],
        texts=[c["text"] for _, c in rows],
        topics=np.array([c["topic"] for _, c in rows]),
        countries=[c["countries"] for _, c in rows],
        valid_from=[c["valid_from"] for _, c in rows],
        valid_to=[c["valid_to"] for _, c in rows],
    )


def allowed_chunks(index: ChunkIndex, country: str, today: str) -> np.ndarray:
    """Mark the chunks that apply to this customer today.

    Args:
        index: the chunks.
        country: the customer's country, for example "SE".
        today: today's date, for example "2026-11-13".

    Returns:
        One True or False per chunk.
    """
    allowed = []
    for countries, start, end in zip(index.countries, index.valid_from,
                                     index.valid_to):
        right_country = "all" in countries or country in countries
        in_force = start <= today and (end is None or end >= today)
        allowed.append(right_country and in_force)
    return np.array(allowed, dtype=bool)


def retrieve(index: ChunkIndex, question: str, country: str,
             topic: str | None, today: str, k: int) -> list[int]:
    """Find the k chunks closest to the question that are allowed.

    Args:
        index: the chunks.
        question: the customer's question.
        country: the customer's country.
        topic: the chosen topic, or None for all topics.
        today: today's date.
        k: how many chunks to return.

    Returns:
        Row numbers, best first.
    """
    vector = normalise(get_embed_query(question))
    scores = index.vectors @ vector
    if topic is not None:
        scores = scores + TOPIC_BONUS * (index.topics == topic)
    mask = allowed_chunks(index, country, today)
    scores = np.where(mask, scores, -np.inf)
    k = min(k, int(mask.sum()))
    return [int(row) for row in get_top_k(scores, k)]


def build_prompt(index: ChunkIndex, rows: list[int], question: str,
                 country: str) -> str:
    """Put the country, the chunks and the question into one text.

    Args:
        index: the chunks.
        rows: the retrieved rows, best first.
        question: the customer's question.
        country: the customer's country.

    Returns:
        The text sent to the model with the instruction.
    """
    parts = [f"Customer's country: {COUNTRY_NAMES[country]} ({country})",
             "", "Sources:"]
    for row in rows:
        parts.append(f"[{index.doc_ids[row]}] {index.titles[row]}, "
                     f"{index.headings[row]}")
        parts.append(index.texts[row])
        parts.append("")
    parts.append(f"Question: {question}")
    return "\n".join(parts)


def answer(request: AskRequest) -> tuple[str, list[Source]]:
    """Answer one policy question: retrieve, then generate.

    Args:
        request: the question, the customer's country and a topic.

    Returns:
        The answer, and the documents it used.
    """
    index = load_chunks()
    today = date.today().isoformat()
    rows = retrieve(index, request.question, request.country,
                    request.topic, today, K)
    prompt = build_prompt(index, rows, request.question, request.country)
    config = types.GenerateContentConfig(
        system_instruction=INSTRUCTION,
        response_mime_type="application/json",
        response_schema=RagAnswer,
    )
    reply = get_text_client().models.generate_content(
        model=TEXT_MODEL, contents=prompt, config=config)
    titles = {index.doc_ids[row]: index.titles[row] for row in rows}
    sources = []
    for doc_id in reply.parsed.sources:
        already = any(s.doc_id == doc_id for s in sources)
        if doc_id in titles and not already:
            sources.append(Source(doc_id=doc_id, title=titles[doc_id]))
    return reply.parsed.answer, sources
