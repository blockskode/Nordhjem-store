"""Answer policy questions with RAG. YOUR EXERCISE (Step 2), not yet set up.

The exercise (chunks, retrieval, the prompt, the answer with sources)
is designed next. Until answer() works, the chat uses the keyword
placeholder in api/keyword_answer.py and says "keyword placeholder".
"""

from api.models import AskRequest, Source


def answer(request: AskRequest) -> tuple[str, list[Source]]:
    """Answer one policy question from the policy documents.

    Args:
        request: the question, the customer's country and an optional
            topic.

    Returns:
        The answer text, and the documents it was taken from.
    """
    raise NotImplementedError("Step 2: RAG")
