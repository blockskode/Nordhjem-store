"""Check Step 1b: reading the filters from the customer's words.

Run from the repo root:

    python3 steps/01b_filters_from_words/check.py             # yours
    python3 steps/01b_filters_from_words/check.py --solution  # reference

Part 1 tests ParsedQuery and merge_filters without calling Gemini.
Part 2 reads the 15 sentences in data/eval/filter_queries.json and
compares the filters with the right answers. Part 3 runs your Step 1
search on the 23 search questions, once without and once with the
filters read from the words, to show what changes.
"""

import importlib
import json
import sys
import time
import warnings
from pathlib import Path
from types import ModuleType
from typing import Callable, TypeVar

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
warnings.filterwarnings("ignore")

from api.models import SearchFilters  # noqa: E402

K = 5
MIN_FIELD = 0.90      # share of sentences with the right category / price
MIN_HIT = 0.95        # the Step 1 marks must still hold
MIN_PRECISION = 0.90

T = TypeVar("T")


def load_module(use_solution: bool) -> ModuleType:
    """Import api/parse_query.py, or the reference solution.

    Args:
        use_solution: load the solution in this folder instead.

    Returns:
        The imported module.
    """
    if use_solution:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        return importlib.import_module("solution")
    return importlib.import_module("api.parse_query")


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


def test_offline(module: ModuleType) -> bool:
    """Test the class and merge_filters on hand-made values.

    Args:
        module: the module under test.

    Returns:
        True if every test passed.
    """
    fields = set(module.ParsedQuery.model_fields)
    results = [check(
        fields == {"search_text", "category", "max_price"},
        "ParsedQuery has search_text, category and max_price",
        f"it has {sorted(fields)}")]
    parsed = module.ParsedQuery(search_text="comfy bed",
                                category="mattress", max_price=4000)
    cases = [
        (SearchFilters(), "mattress", 4000.0,
         "nothing clicked: both come from the words"),
        (SearchFilters(category="sofa"), "sofa", 4000.0,
         "a clicked category wins over the words"),
        (SearchFilters(max_price=2500), "mattress", 2500.0,
         "a clicked price wins over the words"),
    ]
    for clicked, category, price, what in cases:
        got = module.merge_filters(clicked, parsed)
        results.append(check(
            got.category == category and got.max_price == price,
            f"merge_filters: {what}",
            f"got category={got.category!r}, max_price={got.max_price}"))
    nothing = module.ParsedQuery(search_text="x", category=None,
                                 max_price=None)
    got = module.merge_filters(SearchFilters(), nothing)
    results.append(check(
        got.category is None and got.max_price is None,
        "merge_filters: no filters anywhere stays no filters",
        f"got category={got.category!r}, max_price={got.max_price}"))
    return all(results)


def test_sentences(module: ModuleType) -> bool:
    """Read the test sentences and compare with the right filters.

    Args:
        module: the module under test.

    Returns:
        True if category and price are right often enough.
    """
    sentences = json.loads(
        (ROOT / "data" / "eval" / "filter_queries.json").read_text())
    right_category = right_price = 0
    print(f"\n{'cat':>3} {'price':>5}  {'sentence':<42} read as")
    for item in sentences:
        parsed = with_retry(lambda: module.parse_query(item["query"]))
        category_ok = parsed.category == item["category"]
        price_ok = parsed.max_price == item["max_price"]
        right_category += category_ok
        right_price += price_ok
        print(f"{'ok' if category_ok else 'NO':>3} "
              f"{'ok' if price_ok else 'NO':>5}  "
              f"{item['query'][:42]:<42} {parsed.category}, "
              f"{parsed.max_price}, \"{parsed.search_text}\"")
        if not (category_ok and price_ok):
            print(f"{'':>12}want {item['category']}, {item['max_price']}"
                  f" ({item['why']})")
    n = len(sentences)
    print()
    ok_category = check(right_category / n >= MIN_FIELD,
                        f"category right in {right_category} of {n} "
                        f"(pass mark {MIN_FIELD:.0%})")
    ok_price = check(right_price / n >= MIN_FIELD,
                     f"max_price right in {right_price} of {n} "
                     f"(pass mark {MIN_FIELD:.0%})")
    return ok_category and ok_price


def score(search: ModuleType, query: str, filters: SearchFilters,
          relevant: set[str]) -> tuple[float, float]:
    """Run one search and measure hit@K and precision@K.

    Args:
        search: the Step 1 search module.
        query: the text to search for.
        filters: the filters to apply.
        relevant: the right product IDs.

    Returns:
        hit (0 or 1) and precision.
    """
    hits = with_retry(lambda: search.search(query, filters, K))
    correct = sum(hit.product_id in relevant for hit in hits)
    return (1.0 if correct else 0.0), correct / K


def test_search(module: ModuleType) -> bool:
    """Compare the Step 1 search without and with filters from words.

    Args:
        module: the module under test.

    Returns:
        True if the graded Step 1 questions still pass with filters.
    """
    search = importlib.import_module("api.search")
    questions = json.loads(
        (ROOT / "data" / "eval" / "product_queries.json").read_text())
    by_kind: dict[str, list[tuple[float, float, float, float]]] = {}
    print(f"\n{'before':>11} {'after':>11}  kind          question")
    for question in questions:
        relevant = set(question["relevant"])
        before = score(search, question["query"], SearchFilters(), relevant)
        parsed = with_retry(lambda: module.parse_query(question["query"]))
        filters = module.merge_filters(SearchFilters(), parsed)
        after = score(search, parsed.search_text or question["query"],
                      filters, relevant)
        by_kind.setdefault(question["kind"], []).append(before + after)
        print(f"{before[0]:4.0f} {before[1]:5.2f}  {after[0]:4.0f} "
              f"{after[1]:5.2f}  {question['kind']:<13} {question['query']}")
    print(f"\n{'kind':<13} {'prec@5 before':>13} {'prec@5 after':>13}")
    for kind, rows in by_kind.items():
        print(f"{kind:<13} {sum(r[1] for r in rows) / len(rows):>13.2f} "
              f"{sum(r[3] for r in rows) / len(rows):>13.2f}")
    graded = by_kind.get("meaning", []) + by_kind.get("language", [])
    hit = sum(r[2] for r in graded) / len(graded)
    precision = sum(r[3] for r in graded) / len(graded)
    print()
    ok_hit = check(hit >= MIN_HIT, f"with filters, hit@5 on meaning + "
                   f"language is still {hit:.2f} (pass mark {MIN_HIT})")
    ok_precision = check(precision >= MIN_PRECISION,
                         f"with filters, precision@5 on meaning + language "
                         f"is still {precision:.2f} "
                         f"(pass mark {MIN_PRECISION})")
    print("\n'sofa under 4000 kr' should improve. 'not leather' and "
          "'180x200' are not\nfilters yet (no field for material or "
          "size); they only score by meaning.")
    return ok_hit and ok_precision


def main() -> None:
    """Run the three parts in order, stopping at the first failure."""
    module = load_module("--solution" in sys.argv)
    print("Part 1: the class and merge_filters (no Gemini)\n")
    try:
        if not test_offline(module):
            sys.exit("\nFix these first.")
    except NotImplementedError as error:
        sys.exit(f"FAIL  {error} (still a TODO?)")
    print("\nPart 2: filters read from 15 sentences")
    try:
        if not test_sentences(module):
            sys.exit("\nNot there yet; read the 'want' lines above.")
    except NotImplementedError as error:
        sys.exit(f"FAIL  {error} (still a TODO?)")
    print("\nPart 3: your Step 1 search, without and with these filters")
    passed = test_search(module)
    print("\nAll good." if passed else "\nNot there yet; see above.")


if __name__ == "__main__":
    main()
