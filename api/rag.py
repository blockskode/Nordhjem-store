"""Answer policy questions with RAG. THIS IS YOUR EXERCISE (Step 2).

Read steps/02_rag/learn.pdf first. Fill in the functions marked TODO,
from top to bottom; each one is one step of RAG. Check your work from
the repo root:

    python3 steps/02_rag/check.py

Until answer() works, the chat uses a keyword placeholder and says
"keyword placeholder". When the check passes, restart the API and the
chat says "your RAG".
"""

import sys
from dataclasses import dataclass
from datetime import date
from functools import lru_cache
from pathlib import Path

import numpy as np
from google.cloud import firestore
from google.genai import types  # noqa: F401 - you need it in answer
from pydantic import BaseModel

# Lets you run this file directly: python3 api/rag.py
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from api.models import AskRequest, Source  # noqa: E402
from api.parse_query import TEXT_MODEL, get_text_client  # noqa: E402,F401
from api.search import (  # noqa: E402,F401 - your Step 1 functions
    PROJECT, get_embed_query, get_top_k, normalise,
)

K = 4               # how many chunks the text model gets
TOPIC_BONUS = 0.03  # extra score for chunks in the topic the customer chose
COUNTRY_NAMES = {"DK": "Denmark", "SE": "Sweden", "NO": "Norway",
                 "DE": "Germany"}


@dataclass
class ChunkIndex:
    """The policy chunks as lists and arrays; row i is chunk i."""

    ids: list[str]               # "returns-2026-1"
    vectors: np.ndarray          # shape (n, 768), every row length 1
    doc_ids: list[str]           # "returns-2026"
    titles: list[str]            # "Returns policy"
    headings: list[str]          # "How long you have"
    texts: list[str]             # the paragraphs under the heading
    topics: np.ndarray           # shape (n,), "returns", "delivery"...
    countries: list[list[str]]   # ["all"], or for example ["DK"]
    valid_from: list[str]        # "2026-01-01"
    valid_to: list[str | None]   # last day it applied, None if current


class RagAnswer(BaseModel):
    """The form the text model fills in (given, no TODO)."""

    answer: str
    sources: list[str]   # the doc_ids of the sources it used


@lru_cache(maxsize=1)
def load_chunks() -> ChunkIndex:
    """Read every policy chunk from Firestore once (given, no TODO).

    The same idea as your load_index in Step 1, for the collection
    "policy_chunks" (81 chunks, written by loaders/load_policies.py).

    Returns:
        The chunk index.
    """
    db = firestore.Client(project=PROJECT)
    rows = [(d.id, d.to_dict())
            for d in db.collection("policy_chunks").stream()]
    return ChunkIndex(
        ids=[chunk_id for chunk_id, _ in rows],
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

    A chunk is allowed when both are true:
    - its countries contain "all" or the customer's country;
    - it is in force: valid_from <= today, and valid_to is None or
      valid_to >= today. (Dates written "2026-11-13" compare correctly
      as text.)

    Example, for a customer in "DK" on "2026-11-13":

        countries   [["all"], ["DK"], ["SE"], ["all"]]
        valid_to    [None,    None,   None,   "2025-12-31"]
        allowed     [True,    True,   False,  False]

    Args:
        index: the chunks.
        country: the customer's country, for example "SE".
        today: today's date, for example "2026-11-13".

    Returns:
        One True or False per chunk.
    """
    # TODO 1: countries and dates are plain lists, not NumPy arrays, so
    #   loop over them together with zip(...), build a list of True or
    #   False, and return np.array(that_list, dtype=bool).
    raise NotImplementedError("TODO 1: allowed_chunks")


def retrieve(index: ChunkIndex, question: str, country: str,
             topic: str | None, today: str, k: int) -> list[int]:
    """Find the k allowed chunks closest in meaning to the question.

    Args:
        index: the chunks.
        question: the customer's question.
        country: the customer's country.
        topic: the topic the customer chose, or None for all topics.
        today: today's date.
        k: how many chunks to return.

    Returns:
        Row numbers, best first.
    """
    # TODO 2: this is your Step 1 search again, on chunks:
    #   embed and normalise the question, score with @, add TOPIC_BONUS
    #   to the chunks whose topic is the chosen one (only if topic is
    #   not None), remove the not-allowed chunks with np.where and
    #   -np.inf, cap k, and return the rows from get_top_k as a list of
    #   plain ints.
    raise NotImplementedError("TODO 2: retrieve")


def build_prompt(index: ChunkIndex, rows: list[int], question: str,
                 country: str) -> str:
    """Put the country, the chunks and the question into one text.

    The text should look like this:

        Customer's country: Denmark (DK)

        Sources:
        [delivery-dk] Delivery in Denmark, Price and time
        - Standard delivery: **499 kr**, free on orders over 5,000 kr.
        ...

        Question: How much is delivery?

    Args:
        index: the chunks.
        rows: the retrieved rows, best first.
        question: the customer's question.
        country: the customer's country code.

    Returns:
        The text sent to the model, together with INSTRUCTION.
    """
    # TODO 3: build a list of lines and join them with "\n". Each source
    #   starts with its doc_id in square brackets: the model uses it to
    #   say which sources it took the answer from.
    raise NotImplementedError("TODO 3: build_prompt")


# TODO 4: write the instruction for the text model, as plain English.
#   It decides whether the model is honest. Say:
#   - answer only from the sources; never guess or use outside knowledge;
#   - if the sources do not answer, say "I don't know. Please contact
#     customer service." and give no sources;
#   - in sources, list the [doc_id]s of the sources it used;
#   - when rules differ by country, use the customer's country;
#   - answer in the language of the question, short, with exact numbers.
INSTRUCTION = """"""


def answer(request: AskRequest) -> tuple[str, list[Source]]:
    """Answer one policy question: retrieve, then generate.

    Args:
        request: the question, the customer's country and a topic.

    Returns:
        The answer, and the documents it used.
    """
    # TODO 5: the whole of RAG, in four moves:
    #   1. index = load_chunks(); today = date.today().isoformat()
    #   2. rows = retrieve(...) with K chunks; prompt = build_prompt(...)
    #   3. ask get_text_client().models.generate_content(...) with
    #      model=TEXT_MODEL, contents=prompt and a
    #      types.GenerateContentConfig with system_instruction=INSTRUCTION,
    #      response_mime_type="application/json", response_schema=RagAnswer.
    #      reply.parsed is a RagAnswer.
    #   4. turn its doc_ids into Source(doc_id=..., title=...), keeping
    #      only doc_ids that were in the retrieved rows (the model could
    #      invent one), each once. Return (answer text, sources).
    raise NotImplementedError("TODO 5: answer")


if __name__ == "__main__":
    print(answer(AskRequest(question="Can I return a mattress after 80 "
                            "nights?", country="DK")))
