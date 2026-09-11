"""Behavioural compatibility with the 1.1.0 release.

Every prefix of every document in the corpus is parsed with the frozen 1.1.0
parser (tests/legacy_1_1_0_parser.py) and with the current one. The results
must be identical, except where 1.1.0 was demonstrably wrong:

* 1.1.0 raised on a prefix of a valid document (numbers with exponents).
* strict mode: the prefix ends inside an incomplete escape sequence or on a
  lone high surrogate, where 1.1.0 discarded the whole string.
"""
import contextlib
import io
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))
from legacy_1_1_0_parser import LegacyJSONParser

from partialjson import JSONParser

HERE = os.path.dirname(__file__)
_HEX = set("0123456789abcdefABCDEF")

CORPUS = [
    '{"name": "John Doe", "age": 30, "is_student": false, "courses": ["Math", "Science"]}',
    '{"a": {"b": [1, {"c": "d", "e": [true, false, null]}], "f": -12.5, "g": 0}}',
    '{"text": "line1\\nline2\\ttab \\"quoted\\" back\\\\slash \\/ slash", "n": 1}',
    '{"emoji": "\\ud83d\\ude00 smile \\u00e9\\u20ac", "raw": "😀 é €", "k": "\\u0041"}',
    '{"nums": [1e5, -2.5E-3, 0.5, 1.0e+2, 10, -0, 3.14159], "big": 12345678901234567890}',
    '[[], {}, [[]], [{}], "", " ", "\\\\", "\\"", 0, -1, 1.5, true, false, null]',
    '{"": "", "a": "", "b": " ", "c": "\\u0000", "d": "\\b\\f\\r"}',
    '  {\n  "spaced" :  [ 1 , 2 , 3 ] ,\n  "obj" : { "x" : "y" }\n}  \n',
    '"a top level string with \\u00fcml\\u00e4ut and \\ud83c\\udf89"',
    '[1, [2, [3, [4, [5, [6, [7, [8, [9, [10]]]]]]]]]]',
    '{"a": 1, "a": 2, "b": {"a": 3}}',
    "12345",
    "-0.001e-10",
    "true",
    "null",
    '{"servlet": [{"servlet-name": "cofaxCDS", "init-param": {"configGlossary:installationAt": '
    '"Philadelphia, PA", "useJSP": false, "cachePackageTagsTrack": 200}}], '
    '"taglib": {"taglib-uri": "cofax.tld"}}',
]


def _run(parser, text):
    with contextlib.redirect_stdout(io.StringIO()):
        try:
            return ("ok", parser.parse(text))
        except Exception as ex:
            return ("raised", type(ex).__name__)


def _ends_in_incomplete_escape(prefix):
    """True if ``prefix`` ends inside an unterminated string whose tail is an
    incomplete escape (``\\``, ``\\u``, ``\\uAB``...) or a lone high surrogate."""
    i = 0
    n = len(prefix)
    in_string = False
    last_escape = None  # (start, kind)
    while i < n:
        c = prefix[i]
        if not in_string:
            if c == '"':
                in_string = True
                last_escape = None
            i += 1
            continue
        if c == "\\":
            if i + 1 >= n:
                return True
            if prefix[i + 1] == "u":
                hex4 = prefix[i + 2 : i + 6]
                if len(hex4) < 4 and all(h in _HEX for h in hex4):
                    return True
                code = int(hex4, 16)
                if 0xD800 <= code <= 0xDBFF:
                    last_escape = (i, "high")
                elif last_escape and last_escape[1] == "high" and 0xDC00 <= code <= 0xDFFF:
                    last_escape = None
                else:
                    last_escape = None
                i += 6
                continue
            last_escape = None
            i += 2
            continue
        if c == '"':
            in_string = False
            last_escape = None
        else:
            last_escape = None
        i += 1
    return in_string and last_escape is not None and last_escape[0] + 6 == n


def _sameness(a, b):
    # NaN never compares equal to itself; the corpus has none, so plain == works.
    return a == b


@pytest.mark.parametrize("strict", [True, False], ids=["strict", "non_strict"])
@pytest.mark.parametrize("doc", CORPUS, ids=range(len(CORPUS)))
def test_every_prefix_matches_1_1_0(doc, strict):
    legacy = LegacyJSONParser(strict=strict)
    current = JSONParser(strict=strict)
    unexplained = []
    for cut in range(1, len(doc) + 1):
        prefix = doc[:cut]
        old = _run(legacy, prefix)
        new = _run(current, prefix)
        if _sameness(old, new):
            continue
        if old[0] == "raised" and new[0] == "ok":
            continue  # 1.1.0 crashed on a prefix of valid JSON; fixed
        if strict and _ends_in_incomplete_escape(prefix):
            continue  # 1.1.0 threw the whole string away; fixed
        unexplained.append((prefix, old, new))
    assert not unexplained, json.dumps(unexplained[:5], indent=2, ensure_ascii=False)


def test_corpus_is_valid_json():
    for doc in CORPUS:
        json.loads(doc)
