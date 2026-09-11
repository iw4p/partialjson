"""Randomised version of test_compat_1_1_0: generate documents, parse every
prefix with the frozen 1.1.0 parser and the current one, report differences
that are not one of the documented fixes.

Not collected by pytest. Run it by hand:

    python tests/fuzz_compat_1_1_0.py [seed] [documents]
"""
import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from legacy_1_1_0_parser import LegacyJSONParser
from test_compat_1_1_0 import _ends_in_incomplete_escape, _run

from partialjson import JSONParser

WORDS = [
    "a", "name", "x y", "", "tab\there", 'quote"q', "back\\slash", "nl\nline",
    "é", "😀", " ", "true", "null", "1e5", "/", "\x01", "ሴ", "🎉x",
]
NUMBERS = [0, 1, -1, 42, 3.14, -2.5, 1e5, 2.5e-3, -1.5e10, 1e300, 0.001, 12345678901234567890, 7.0]


def random_string():
    return "".join(random.choice(WORDS) for _ in range(random.randint(0, 3)))


def random_value(depth=0):
    r = random.random()
    if depth > 3 or r < 0.35:
        leaves = [
            random_string,
            lambda: random.choice(NUMBERS),
            lambda: True,
            lambda: False,
            lambda: None,
        ]
        return random.choice(leaves)()
    if r < 0.7:
        return [random_value(depth + 1) for _ in range(random.randint(0, 4))]
    return {random_string(): random_value(depth + 1) for _ in range(random.randint(0, 4))}


def main(seed, count):
    random.seed(seed)
    unexplained = []
    prefixes = 0
    for _ in range(count):
        doc = json.dumps(
            random_value(),
            ensure_ascii=random.random() < 0.5,
            indent=random.choice([None, None, 1]),
        )
        for strict in (True, False):
            legacy, current = LegacyJSONParser(strict=strict), JSONParser(strict=strict)
            for cut in range(1, len(doc) + 1):
                prefix = doc[:cut]
                prefixes += 1
                old, new = _run(legacy, prefix), _run(current, prefix)
                if old == new:
                    continue
                if old[0] == "raised" and new[0] == "ok":
                    continue
                if strict and _ends_in_incomplete_escape(prefix):
                    continue
                unexplained.append((strict, prefix, old, new))
    print(f"documents={count} prefixes={prefixes} unexplained={len(unexplained)}")
    for item in unexplained[:10]:
        print(repr(item))
    return 1 if unexplained else 0


if __name__ == "__main__":
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    count = int(sys.argv[2]) if len(sys.argv) > 2 else 500
    sys.exit(main(seed, count))
