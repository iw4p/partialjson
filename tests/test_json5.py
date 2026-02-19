import pytest
import math
from partialjson.json_parser import JSONParser

def test_json5_comments():
    parser = JSONParser(json5_enabled=True)
    assert parser.parse("{// comment\n\"a\": 1}") == {"a": 1}
    assert parser.parse("{/* multi-line\n comment */\"a\": 1}") == {"a": 1}
    assert parser.parse("{/* incomplete comment") == {}

def test_json5_unquoted_keys():
    parser = JSONParser(json5_enabled=True)
    assert parser.parse("{a: 1, b: 2}") == {"a": 1, "b": 2}
    assert parser.parse("{_foo: \"bar\", $baz: 3}") == {"_foo": "bar", "$baz": 3}
    assert parser.parse("{a: 1, ") == {"a": 1}

def test_json5_single_quotes():
    parser = JSONParser(json5_enabled=True)
    assert parser.parse("'hello'") == "hello"
    assert parser.parse("{'a': 'b'}") == {"a": "b"}
    assert parser.parse("'it\\'s me'") == "it's me"

def test_json5_multi_line_strings():
    parser = JSONParser(json5_enabled=True)
    assert parser.parse("'line1\\\nline2'") == "line1line2"
    assert parser.parse("\"line1\\\r\nline2\"") == "line1line2"

def test_json5_hex_numbers():
    parser = JSONParser(json5_enabled=True)
    assert parser.parse("0x1f") == 31
    assert parser.parse("-0x10") == -16 # Note: JSON5 spec says hex can have optional sign
    # Actually checking spec: "Hexadecimal numbers ... may be prefixed with an optional plus or minus sign"
    assert parser.parse("0XFF") == 255

def test_json5_special_numbers():
    parser = JSONParser(json5_enabled=True)
    assert parser.parse("Infinity") == float("inf")
    assert parser.parse("-Infinity") == float("-inf")
    assert math.isnan(parser.parse("NaN"))
    assert parser.parse(".5") == 0.5
    assert parser.parse("+42") == 42

def test_json5_case_insensitive_literals():
    parser = JSONParser(json5_enabled=True)
    assert parser.parse("True") is True
    assert parser.parse("FALSE") is False
    assert parser.parse("Null") is None

def test_json5_trailing_commas():
    # Already supported but good to verify with JSON5 enabled
    parser = JSONParser(json5_enabled=True)
    assert parser.parse("[1, 2, 3,]") == [1, 2, 3]
    assert parser.parse("{a: 1, b: 2,}") == {"a": 1, "b": 2}

def test_json5_whitespace():
    parser = JSONParser(json5_enabled=True)
    assert parser.parse("{\v\"a\"\f: 1\u00A0}") == {"a": 1}
