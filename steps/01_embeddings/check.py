"""Check Step 1: test your functions, then measure the search.

Run from the repo root:

    uv run python steps/01_embeddings/check.py             # api/search.py
    uv run python steps/01_embeddings/check.py --solution  # reference

Part 1 tests normalise, allowed and top_k on small numbers you can
compute by hand (no API calls). Part 2 asks the 23 test questions in
data/eval/product_queries.json and measures hit@5 and precision@5.
"""

import importlib
import json
import sys
import warnings
from pathlib import Path
from types import ModuleType

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
warnings.filterwarnings("ignore")

from api.models import SearchFilters  # noqa: E402

K = 5
# Pass marks for the questions an embedding search can answer.
MIN_HIT = 0.95
MIN_PRECISION = 0.90


def load_module(use_solution: bool) -> ModuleType:
    """Import api/search.py, or the reference solution.

    Args:
        use_solution: load steps/01_embeddings/solution.py instead.

    Returns:
        The imported module.
    """
    if use_solution:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        return importlib.import_module("solution")
    return importlib.import_module("api.search")


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


def test_normalise(module: ModuleType) -> list[bool]:
    """Test normalise on the vectors from the learn PDF.

    Args:
        module: the module under test.

    Returns:
        One result per test.
    """
    got = np.asarray(module.normalise(np.array([0.9, 0.1, 0.4])))
    first = check(
        got.shape == (3,) and np.allclose(got, [0.909, 0.101, 0.404],
                                          atol=1e-3),
        "normalise([0.9, 0.1, 0.4]) is about [0.909, 0.101, 0.404]",
        f"got {np.round(got, 3)}")
    got = np.asarray(module.normalise(np.array([[3.0, 4.0], [0.0, 2.0]])))
    second = check(
        got.shape == (2, 2) and np.allclose(got, [[0.6, 0.8], [0, 1]]),
        "normalise works row by row on a matrix",
        f"got {np.round(got, 3).tolist()}, want [[0.6, 0.8], [0, 1]]")
    return [first, second]


def test_allowed_and_top_k(module: ModuleType) -> list[bool]:
    """Test allowed and top_k on the 4-product example from the PDF.

    Args:
        module: the module under test.

    Returns:
        One result per test.
    """
    index = module.Index(
        ids=["P1", "P2", "P3", "P4"],
        vectors=np.zeros((4, 3)),
        categories=np.array(["sofa", "sofa", "rug", "sofa"]),
        prices=np.array([3000.0, 6500.0, 1200.0, 2500.0]),
    )
    results = []
    got = np.asarray(module.allowed(index, SearchFilters(max_price=4000)))
    results.append(check(
        got.tolist() == [True, False, True, True],
        "allowed: max price 4000 keeps P1, P3, P4",
        f"got {got.tolist()}"))
    filters = SearchFilters(category="sofa", max_price=4000)
    got = np.asarray(module.allowed(index, filters))
    results.append(check(
        got.tolist() == [True, False, False, True],
        "allowed: sofa and max price 4000 keeps P1 and P4",
        f"got {got.tolist()}"))
    got = np.asarray(module.allowed(index, SearchFilters()))
    results.append(check(
        got.tolist() == [True, True, True, True],
        "allowed: no filters keeps all four",
        f"got {got.tolist()}"))
    scores = np.array([0.2, 0.9, 0.1, 0.7, 0.5])
    got = module.top_k(scores, 3)
    results.append(check(
        got is not None and list(got) == [1, 3, 4],
        "top_k([0.2, 0.9, 0.1, 0.7, 0.5], 3) is [1, 3, 4]",
        f"got {got}"))
    return results


def test_functions(module: ModuleType) -> bool:
    """Run the hand-computed tests, catching any error.

    Args:
        module: the module under test.

    Returns:
        True if every test passed.
    """
    try:
        results = test_normalise(module) + test_allowed_and_top_k(module)
    except Exception as error:  # noqa: BLE001 - show any mistake
        return check(False, "functions run",
                     f"{type(error).__name__}: {error} (still a TODO?)")
    return all(results)


def evaluate(module: ModuleType) -> dict[str, list[tuple[float, float]]]:
    """Ask every test question and score the top K results.

    Args:
        module: the module under test.

    Returns:
        For each question kind, a list of (hit, precision) pairs.
    """
    questions = json.loads(
        (ROOT / "data" / "eval" / "product_queries.json").read_text())
    by_kind: dict[str, list[tuple[float, float]]] = {}
    print(f"\n{'hit':>4} {'prec':>5}  kind          question")
    for question in questions:
        hits = module.search(question["query"], SearchFilters(), K)
        relevant = set(question["relevant"])
        correct = sum(hit.product_id in relevant for hit in hits)
        hit = 1.0 if correct else 0.0
        precision = correct / K
        by_kind.setdefault(question["kind"], []).append((hit, precision))
        print(f"{hit:4.0f} {precision:5.2f}  {question['kind']:<13} "
              f"{question['query']}")
    return by_kind


def average(pairs: list[tuple[float, float]]) -> tuple[float, float]:
    """Average a list of (hit, precision) pairs.

    Args:
        pairs: the pairs.

    Returns:
        The mean hit and the mean precision.
    """
    hit = sum(h for h, _ in pairs) / len(pairs)
    precision = sum(p for _, p in pairs) / len(pairs)
    return hit, precision


def summarise(by_kind: dict[str, list[tuple[float, float]]]) -> bool:
    """Print averages per kind and compare with the pass marks.

    Args:
        by_kind: output of evaluate.

    Returns:
        True if the meaning and language questions pass.
    """
    print(f"\n{'kind':<13} {'questions':>9} {'hit@5':>6} {'prec@5':>7}")
    for kind, pairs in by_kind.items():
        hit, precision = average(pairs)
        print(f"{kind:<13} {len(pairs):>9} {hit:>6.2f} {precision:>7.2f}")
    answerable = by_kind.get("meaning", []) + by_kind.get("language", [])
    hit, precision = average(answerable)
    print()
    ok_hit = check(hit >= MIN_HIT,
                   f"hit@5 on meaning + language: {hit:.2f} "
                   f"(pass mark {MIN_HIT})")
    ok_precision = check(precision >= MIN_PRECISION,
                         f"precision@5 on meaning + language: "
                         f"{precision:.2f} (pass mark {MIN_PRECISION})")
    print("\nThe needs_filter questions are not graded: embeddings alone "
          "cannot do 'under 4000 kr',\n'not leather' or exact sizes. "
          "Look at what they return; Step 3 fixes them.")
    return ok_hit and ok_precision


def main() -> None:
    """Run the function tests, then the evaluation."""
    module = load_module("--solution" in sys.argv)
    print("Part 1: functions\n")
    if not test_functions(module):
        sys.exit("\nFix the functions first; the search depends on them.")
    print("\nPart 2: search quality on the test questions")
    passed = summarise(evaluate(module))
    print("\nAll good." if passed else "\nNot there yet; see above.")


if __name__ == "__main__":
    main()
