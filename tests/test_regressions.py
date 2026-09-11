"""Regression tests for the fixes shipped in 1.2.0."""
import contextlib
import io
import math

import pytest

import partialjson
from partialjson import JSONParser, create_json5_parser, create_json_parser, json5_parser


@pytest.fixture(params=["json", "json5", "json5-no-lib"])
def parser(request, monkeypatch):
    """The JSON parser, and the JSON5 parser both with and without the
    optional ``json5`` package, all of which must accept plain JSON."""
    if request.param == "json":
        return JSONParser()
    if request.param == "json5-no-lib":
        monkeypatch.setattr(json5_parser, "json5", None)
    return JSONParser(json5_enabled=True)


# --- numbers with exponents used to raise inside a container -----------------

@pytest.mark.parametrize(
    "text, expected",
    [
        ("[1e5", [100000.0]),
        ('{"a": 1e-7', {"a": 1e-7}),
        ("[1.5e10, 2", [1.5e10, 2]),
        ("[-1.5E+3]", [-1500.0]),
        ("[1e", [1]),
        ("[1e-", [1]),
        ("[1.5E+", [1.5]),
        ("[2.5e3, 1e", [2500.0, 1]),
        ("1e", 1),
    ],
)
def test_exponent_numbers(parser, text, expected):
    assert parser.parse(text) == expected


def test_incomplete_number_keeps_legacy_shape():
    parser = JSONParser()
    assert parser.parse("-") == "-"
    assert parser.parse("[1, -") == [1, "-"]
    assert parser.parse("[1.") == [1]
    with pytest.raises(ValueError):
        parser.parse("[1.5.")  # invalid, and 1.1.0 raised here as well


# --- incomplete escapes no longer throw away the rest of the string ----------

@pytest.mark.parametrize(
    "text, expected",
    [
        ('{"a":"foo\\', {"a": "foo"}),
        ('{"a":"foo\\u', {"a": "foo"}),
        ('{"a":"foo\\u00', {"a": "foo"}),
        ('{"a":"foo\\u00e', {"a": "foo"}),
        ('{"a":"foo\\u00e9', {"a": "fooé"}),
        ('{"a":"foo\\u00e9\\', {"a": "fooé"}),
        ('"foo\\', "foo"),
        ('{"a":"\\', {"a": ""}),
        ('{"a":"\\u', {"a": ""}),
        ('{"a":"\\u123', {"a": ""}),
        ('{"a":"\\u1234', {"a": "ሴ"}),
        ('{"a":"foo\\"', {"a": 'foo"'}),
        ('{"a":"esc\\\\', {"a": "esc\\"}),  # complete escaped backslash is kept
        ('{"a":"esc\\\\\\', {"a": "esc\\"}),  # ...but a trailing lone one is not
    ],
)
def test_incomplete_escape_keeps_prefix(parser, text, expected):
    assert parser.parse(text) == expected


@pytest.mark.parametrize(
    "text, expected",
    [
        ('{"a":"hi \\ud83d', {"a": "hi "}),
        ('{"a":"hi \\ud83d\\', {"a": "hi "}),
        ('{"a":"hi \\ud83d\\ude0', {"a": "hi "}),
        ('{"a":"hi \\ud83d\\ude00', {"a": "hi 😀"}),
        ('{"a":"hi \\ud83d\\ude00 x', {"a": "hi 😀 x"}),
        ('{"a":"\\ud83c\\udf89\\ud83d', {"a": "🎉"}),
    ],
)
def test_surrogate_pairs_are_held_back_until_complete(parser, text, expected):
    result = parser.parse(text)
    assert result == expected
    result["a"].encode("utf-8")  # never hands out a lone surrogate


def test_non_strict_incomplete_string_is_still_raw():
    parser = JSONParser(strict=False)
    assert parser.parse('{"a":"foo\\u00') == {"a": "foo\\u00"}
    assert parser.parse('{"a":"foo\\') == {"a": "foo\\"}
    assert parser.parse('"A\\nB') == "A\\nB"


# --- literals ---------------------------------------------------------------

@pytest.mark.parametrize(
    "text, expected",
    [
        ("[t", [True]),
        ("[tru", [True]),
        ("[fals", [False]),
        ('{"a": nul', {"a": None}),
        ("[1,t", [1, True]),
    ],
)
def test_partial_literals(parser, text, expected):
    assert parser.parse(text) == expected


def test_literal_prefix_no_longer_swallows_following_tokens():
    parser = JSONParser()
    with pytest.raises(ValueError):
        parser.parse("[trap]")
    with pytest.raises(ValueError):
        parser.parse("[t,1]")


def test_json5_case_insensitive_partial_literals():
    parser = create_json5_parser()
    assert parser.parse("[T") == [True]
    assert parser.parse("[Fal") == [False]
    assert parser.parse("[NU") == [None]
    assert parser.parse("[Na") == [math.nan] or math.isnan(parser.parse("[Na")[0])
    assert parser.parse("[Inf") == [math.inf]
    assert parser.parse("[-Inf") == [-math.inf]
    assert parser.parse("{a: 0x") == {"a": "0x"}
    assert parser.parse("{a: 0x1F") == {"a": 31}
    assert parser.parse("{a: +") == {"a": "+"}


# --- JSON5 comments and strings ---------------------------------------------

def test_json5_incomplete_comment_at_end_of_stream():
    parser = create_json5_parser()
    assert parser.parse('{"a": 1, /') == {"a": 1}
    assert parser.parse('{"a": 1, //') == {"a": 1}
    assert parser.parse('{"a": 1, // comment') == {"a": 1}
    assert parser.parse('{"a": 1, /* comment') == {"a": 1}
    assert parser.parse('{"a": 1, /* c */ "b": 2') == {"a": 1, "b": 2}


@pytest.mark.parametrize("has_lib", [True, False])
def test_json5_string_decoding_is_independent_of_optional_dependency(monkeypatch, has_lib):
    if not has_lib:
        monkeypatch.setattr(json5_parser, "json5", None)
    parser = create_json5_parser()
    assert parser.parse("{a: 'it\\'s \\x41\\u0042', b: 'x\\\ny'") == {"a": "it's AB", "b": "xy"}
    assert parser.parse("{a: 'it\\'s \\x4") == {"a": "it's "}
    assert parser.parse("{a: 'it\\'s \\x41") == {"a": "it's A"}
    assert parser.parse("{a: '\\ud83d\\ude00'") == {"a": "😀"}
    assert parser.parse("{a: 1, b: 'x\\u2028y'}") == {"a": 1, "b": "x" + chr(0x2028) + "y"}
    assert parser.parse('{"a": "\\/"}') == {"a": "/"}


def test_json5_plain_json_fast_path_without_lib(monkeypatch):
    monkeypatch.setattr(json5_parser, "json5", None)
    parser = create_json5_parser()
    assert parser.parse('{"a": [1, 2, {"b": null}]}') == {"a": [1, 2, {"b": None}]}
    assert parser.last_parse_reminding is None


# --- input types -------------------------------------------------------------

def test_bytes_input(parser):
    assert parser.parse(b'{"a": 1}') == {"a": 1}
    assert parser.parse(b'{"a": "caf\xc3\xa9", "b": [1') == {"a": "café", "b": [1]}
    assert parser.parse(b'{"a": "caf\xc3') == {"a": "caf"}  # split multi-byte char
    assert parser.parse(bytearray(b"[1, 2")) == [1, 2]
    assert parser.parse(b"") == {}


def test_bom_is_ignored(parser):
    assert parser.parse('\ufeff{"a": 1}') == {"a": 1}
    assert parser.parse('\ufeff{"a": 1') == {"a": 1}
    assert parser.parse(b'\xef\xbb\xbf{"a": 1') == {"a": 1}


# --- facade / 0.x API surface ----------------------------------------------

def test_facade_exposes_and_forwards_settings():
    parser = JSONParser()
    assert parser.strict is True
    assert parser.json5_enabled is False
    parser.strict = False
    assert parser.parse('{"a":"x\\u00') == {"a": "x\\u00"}
    calls = []
    parser.on_extra_token = lambda text, data, reminding: calls.append(reminding)
    assert parser.parse("[1] x") == [1]
    assert calls == [" x"]
    assert parser.last_parse_reminding == " x"
    parser.on_extra_token = None
    assert parser.parse("[1] y") == [1]
    assert JSONParser(json5_enabled=True).json5_enabled is True


def test_0x_method_names_still_callable():
    parser = JSONParser()
    e = ValueError("x")
    assert parser.parse_string('"abc" rest', e) == ("abc", " rest")
    assert parser.parse_string('"abc', e) == ("abc", "")
    assert parser.parse_number("12.5, 3", e) == (12.5, ", 3")
    assert parser.parse_array("[1, 2] z", e) == ([1, 2], " z")
    assert parser.parse_object('{"a": 1} z', e) == ({"a": 1}, " z")
    assert parser.parse_true("true,", e) == (True, ",")
    assert parser.parse_false("fa", e) == (False, "")
    assert parser.parse_null("null]", e) == (None, "]")
    assert parser.parse_space("  x", e) == "x"
    assert parser.parse_any("  [1]  ", e) == ([1], "  ")
    with pytest.raises(AttributeError):
        _ = parser.does_not_exist


def test_default_on_extra_token_still_prints():
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        JSONParser().parse("[1] x")
    assert "Parsed JSON with extra tokens" in buf.getvalue()


def test_public_names():
    assert set(partialjson.__all__) >= {"JSONParser", "create_json_parser", "create_json5_parser"}
    assert isinstance(create_json_parser(), partialjson.json_parser._JSONParser)


# --- performance guard -------------------------------------------------------

def test_large_partial_document_is_linear():
    import json
    import time

    def build(n):
        items = [{"id": i, "name": f"item {i}", "tags": ["a", "b"]} for i in range(n)]
        return json.dumps(items)[:-5]

    def timed(text):
        t = time.perf_counter()
        parser.parse(text)
        return time.perf_counter() - t

    parser = JSONParser()
    t_small = timed(build(2000))
    t_large = timed(build(16000))
    # 8x the input should cost roughly 8x, not 64x. Allow generous slack.
    assert t_large < t_small * 30, (t_small, t_large)
