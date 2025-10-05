import pytest
from partialjson.json_parser import JSONParser


def test_numbers_and_floats():
    parser = JSONParser(strict=True)
    assert parser.parse("42") == 42
    assert parser.parse("-42") == -42
    assert parser.parse("12.34") == 12.34
    assert parser.parse("-12.34") == -12.34
    assert parser.parse("12.") == 12
    assert parser.parse("-12.") == -12


def test_invalid_number_raises_error():
    parser = JSONParser(strict=True)
    with pytest.raises(Exception):
        parser.parse("1.2.3.4")


def test_booleans_and_null():
    parser = JSONParser(strict=True)
    assert parser.parse("true") is True
    assert parser.parse("false") is False
    assert parser.parse("null") is None


def test_array_complete_and_incomplete():
    parser = JSONParser(strict=True)
    assert parser.parse("[]") == []
    assert parser.parse("[1,2,3]") == [1, 2, 3]
    assert parser.parse("[1,2,3") == [1, 2, 3]
    assert parser.parse("[1,2,") == [1, 2]
    assert parser.parse("[1,") == [1]
    assert parser.parse("[") == []


def test_object_complete():
    parser = JSONParser(strict=True)
    expected = {"a": "apple", "b": "banana"}
    assert parser.parse('{"a":"apple","b":"banana"}') == expected
    assert parser.parse('{"a": "apple","b": "banana"}') == expected


def test_string_strict_complete_and_incomplete_in_object():
    parser = JSONParser(strict=True)
    assert parser.parse('{"x": "1st line\\n2nd line"}') == {"x": "1st line\n2nd line"}
    assert parser.parse('{"x": "1st line\\n2nd line') == {"x": "1st line\n2nd line"}


def test_top_level_string():
    parser = JSONParser(strict=True)
    assert parser.parse('"I am text"') == "I am text"
    assert parser.parse('"I\\"m text"') == 'I"m text'


def test_top_level_incomplete_string_strict():
    parser = JSONParser(strict=True)
    assert parser.parse('"I am text') == "I am text"


def test_string_relaxed_returns_raw_content_when_incomplete():
    parser = JSONParser(strict=False)
    result = parser.parse('"A\\nB')
    assert result == "A\\nB"


def test_spaces_and_extra_tokens():
    parser = JSONParser(strict=True)
    assert parser.parse(" [1] ") == [1]
    assert parser.parse(" [1 ") == [1]


def test_invalid_input_raises_error():
    parser = JSONParser(strict=True)
    with pytest.raises(Exception):
        parser.parse(":atom")


def test_unicode_escape_complete():
    parser = JSONParser(strict=True)
    assert parser.parse('{"a":"\\u0041"}') == {"a": "A"}
    assert parser.parse('{"a":"\\u00E9"}') == {"a": "é"}
    assert parser.parse('{"a":"\\u20AC"}') == {"a": "€"}


def test_unicode_escape_incomplete_strict():
    parser = JSONParser(strict=True)
    assert parser.parse('{"a":"\\u123"') == {"a": "\u1234"}
    assert parser.parse('{"a":"\\u"') == {"a": ""}
    assert parser.parse('{"a":"\\""') == {"a": ""}
