"""Check Step 2: RAG over the policy documents.

Run from the repo root:

    python3 steps/02_rag/check.py             # yours (api/rag.py)
    python3 steps/02_rag/check.py --solution  # the reference

Part 1 tests allowed_chunks and build_prompt on four made-up chunks,
without calling Google. Part 2 tests retrieval on the 30 questions in
data/eval/policy_questions.json: is a right document among the chunks
found? Part 3 asks the full RAG every question and checks the answer:
the key fact, the source, and "I don't know" when the documents have
no answer.
"""

import importlib
import json
import sys
import time
import warnings
from pathlib import Path
from types import ModuleType
from typing import Callable, TypeVar

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
warnings.filterwarnings("ignore")

from api.models import AskRequest  # noqa: E402

MIN_RECALL = 0.90       # share of questions with a right chunk found
MIN_FACTS = 0.85        # share of answers with the key fact
DONT_KNOW = ("don't know", "do not know")
TODAY = "2026-11-13"    # fixed, so the check gives the same result later

T = TypeVar("T")


def load_module(use_solution: bool) -> ModuleType:
    """Import api/rag.py, or the reference solution.

    Args:
        use_solution: load the solution in this folder instead.

    Returns:
        The imported module.
    """
    if use_solution:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        return importlib.import_module("solution")
    return importlib.import_module("api.rag")


def with_retry(call: Callable[[], T]) -> T:
    """Run a call to Google, waiting and trying again when rate limited.

    Args:
        call: a function with no arguments that calls Google.

    Returns:
        What the call returns.
    """
    for wait in (5, 15, 30, 60):
        try:
            return call()
        except Exception as error:  # noqa: BLE001 - only retry 429s
            if "429" not in str(error):
                raise
            print(f"      (rate limited by Google, waiting {wait} s)")
            time.sleep(wait)
    return call()


def check(passed: bool, what: str, detail: str = "") -> bool:
    """Print one result line.

    Args:
        passed: whether it passed.
        what: what was checked.
        detail: extra text shown when it failed.

    Returns:
        passed, unchanged.
    """
    print(f"{'PASS' if passed else 'FAIL'}  {what}")
    if not passed and detail:
        print(f"      {detail}")
    return passed


def small_index(module: ModuleType):  # noqa: ANN201 - the module's class
    """Build four made-up chunks, as in the learn PDF.

    Args:
        module: the module under test.

    Returns:
        A ChunkIndex with four rows.
    """
    return module.ChunkIndex(
        ids=["a-1", "b-1", "c-1", "d-1"],
        vectors=np.zeros((4, 3)),
        doc_ids=["returns-2026", "delivery-dk", "delivery-se",
                 "returns-2025"],
        titles=["Returns policy", "Delivery in Denmark",
                "Delivery in Sweden", "Returns policy (2025)"],
        headings=["How long you have", "Price and time",
                  "Price and time", "How long you have"],
        texts=["60 days.", "499 kr.", "599 SEK.", "30 days."],
        topics=np.array(["returns", "delivery", "delivery", "returns"]),
        countries=[["all"], ["DK"], ["SE"], ["all"]],
        valid_from=["2026-01-01", "2026-01-01", "2026-01-01",
                    "2025-01-01"],
        valid_to=[None, None, None, "2025-12-31"],
    )


def test_offline(module: ModuleType) -> bool:
    """Test allowed_chunks and build_prompt without calling Google.

    Args:
        module: the module under test.

    Returns:
        True if every test passed.
    """
    index = small_index(module)
    results = []
    got = np.asarray(module.allowed_chunks(index, "DK", TODAY)).tolist()
    results.append(check(
        got == [True, True, False, False],
        "allowed_chunks for DK: all + DK, not SE, not the expired 2025 one",
        f"got {got}"))
    got = np.asarray(module.allowed_chunks(index, "SE", TODAY)).tolist()
    results.append(check(
        got == [True, False, True, False],
        "allowed_chunks for SE: all + SE",
        f"got {got}"))
    got = np.asarray(module.allowed_chunks(index, "DK", "2025-06-01"))
    results.append(check(
        got.tolist() == [False, False, False, True],
        "allowed_chunks on 2025-06-01: only the 2025 policy was in force",
        f"got {got.tolist()}"))
    prompt = module.build_prompt(index, [1, 0], "How much is delivery?",
                                 "DK")
    needed = ["How much is delivery?", "[delivery-dk]", "499 kr.",
              "[returns-2026]", "60 days.", "Denmark"]
    missing = [n for n in needed if n not in str(prompt)]
    results.append(check(
        not missing,
        "build_prompt has the question, each [doc_id], each text, the "
        "country",
        f"missing: {missing}"))
    results.append(check(
        "599 SEK." not in str(prompt),
        "build_prompt only has the rows it was given"))
    return all(results)


def test_retrieval(module: ModuleType, questions: list[dict]) -> bool:
    """Is a right document among the retrieved chunks?

    Args:
        module: the module under test.
        questions: the test questions.

    Returns:
        True if recall is high enough and the old policy never appears.
    """
    index = module.load_chunks()
    found = total = 0
    old_seen = False
    print(f"\n{'found':>5}  {'question':<58} documents")
    for q in questions:
        rows = with_retry(lambda: module.retrieve(
            index, q["question"], q["country"] or "DK", None, TODAY,
            module.K))
        docs = [index.doc_ids[r] for r in rows]
        old_seen = old_seen or "returns-2025" in docs
        if not q["sources"]:
            continue
        ok = any(d in docs for d in q["sources"])
        found += ok
        total += 1
        print(f"{'ok' if ok else 'NO':>5}  {q['question'][:58]:<58} "
              f"{', '.join(dict.fromkeys(docs))}")
    print()
    passed = check(found / total >= MIN_RECALL,
                   f"a right document found for {found} of {total} "
                   f"(pass mark {MIN_RECALL:.0%})")
    return check(not old_seen, "the expired 2025 returns policy is never "
                 "retrieved") and passed


def says_dont_know(text: str) -> bool:
    """Check whether an answer admits it does not know.

    Args:
        text: the answer.

    Returns:
        True if it says "I don't know" or similar.
    """
    low = text.lower().replace("’", "'")
    return any(phrase in low for phrase in DONT_KNOW)


def test_answers(module: ModuleType, questions: list[dict]) -> bool:
    """Ask the full RAG every question and grade the answers.

    Args:
        module: the module under test.
        questions: the test questions.

    Returns:
        True if enough answers are right and every "no answer"
        question gets "I don't know".
    """
    facts_ok = answerable = honest = no_answer = 0
    print()
    for q in questions:
        request = AskRequest(question=q["question"],
                             country=q["country"] or "DK")
        text, sources = with_retry(lambda: module.answer(request))
        got = [s.doc_id for s in sources]
        if not q["sources"]:
            no_answer += 1
            ok = says_dont_know(text)
            honest += ok
        else:
            answerable += 1
            ok = all(f.lower() in text.lower() for f in q["must_include"])
            ok = ok and any(d in got for d in q["sources"])
            facts_ok += ok
        print(f"{'ok' if ok else 'NO':>4}  {q['kind']:<15} {q['question']}")
        print(f"{'':>6}{text.strip()[:150]}  [{', '.join(got)}]")
        if not ok:
            want = q["must_include"] or ["I don't know"]
            print(f"{'':>6}want: {', '.join(want)} from "
                  f"{q['sources'] or 'no source'} ({q['why'] or q['kind']})")
    print()
    ok_facts = check(facts_ok / answerable >= MIN_FACTS,
                     f"right fact and source in {facts_ok} of "
                     f"{answerable} answers (pass mark {MIN_FACTS:.0%})")
    ok_honest = check(honest == no_answer,
                      f"\"I don't know\" in {honest} of {no_answer} "
                      "questions with no answer in the documents")
    return ok_facts and ok_honest


def main() -> None:
    """Run the three parts in order, stopping at the first failure."""
    module = load_module("--solution" in sys.argv)
    questions = json.loads(
        (ROOT / "data" / "eval" / "policy_questions.json").read_text())
    print("Part 1: allowed_chunks and build_prompt (no Google)\n")
    try:
        if not test_offline(module):
            sys.exit("\nFix these first.")
        print("\nPart 2: retrieval on 30 questions")
        if not test_retrieval(module, questions):
            sys.exit("\nNot there yet; see the NO lines above.")
        print("\nPart 3: the answers")
        passed = test_answers(module, questions)
    except NotImplementedError as error:
        sys.exit(f"FAIL  {error} (still a TODO?)")
    print("\nAll good." if passed else "\nNot there yet; see above.")


if __name__ == "__main__":
    main()
