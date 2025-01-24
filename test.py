import unittest
from partialjson.json_parser import JSONParser


class TestJSONParser(unittest.TestCase):
    def setUp(self):
        self.parser_strict = JSONParser(strict=True)
        self.parser_non_strict = JSONParser(strict=False)

    # Test for parser_strict
    def test_parser_strict_incomplete_object(self):
        with self.assertRaises(Exception):
            self.parser_strict.parse(
                '{"x": "1st line\\n2nd line', '{"x": "1st line\\n2nd line"}'
            )

    def test_parser_strict_incomplete_string(self):
        with self.assertRaises(Exception):
            self.parser_strict.parse(
                '{"x": "1st line\\n2nd line"', '{"x": "1st line\\n2nd line"}'
            )

    def test_parser_strict_complete_string(self):
        self.assertEqual(
            self.parser_strict.parse('{"x": "1st line\\n2nd line"}').get("x"),
            "1st line\n2nd line",
        )

    def test_parser_strict_incomplete_object(self):
        self.assertEqual(
            self.parser_strict.parse('{"x": "1st line\\n2nd line').get("x"),
            "1st line\n2nd line",
        )

    def test_parser_strict_incomplete_string(self):
        self.assertEqual(
            self.parser_strict.parse('{"x": "1st line\\n2nd line"').get("x"),
            "1st line\n2nd line",
        )

    # Test for parser_non_strict
    def test_parser_non_strict_complete_string(self):
        self.assertEqual(
            self.parser_non_strict.parse('{"x": "1st line\\n2nd line"}').get("x"),
            "1st line\n2nd line",
        )

    # Existing tests can remain unchanged...
    # Number Tests
    def test_positive_integer(self):
        self.assertEqual(self.parser_strict.parse("42"), 42)

    def test_negative_integer(self):
        self.assertEqual(self.parser_strict.parse("-42"), -42)

    def test_positive_float(self):
        self.assertEqual(self.parser_strict.parse("12.34"), 12.34)

    def test_negative_float(self):
        self.assertEqual(self.parser_strict.parse("-12.34"), -12.34)

    def test_incomplete_positive_float(self):
        self.assertEqual(self.parser_strict.parse("12."), 12)

    def test_incomplete_negative_float(self):
        self.assertEqual(self.parser_strict.parse("-12."), -12)

    def test_invalid_number(self):
        with self.assertRaises(Exception):
            self.parser_strict.parse("1.2.3.4")

    # String Tests
    def test_string(self):
        self.assertEqual(self.parser_strict.parse('"I am text"'), "I am text")
        self.assertEqual(self.parser_strict.parse('"I\'m text"'), "I'm text")
        self.assertEqual(self.parser_strict.parse('"I\\"m text"'), 'I"m text')

    def test_incomplete_string(self):
        with self.assertRaises(Exception):
            self.parser_strict.parse('"I am text', "I am text")
            self.parser_strict.parse("\"I'm text", "I'm text")
            self.parser_strict.parse('"I\\"m text', "I\\m text")

    # Boolean Tests
    def test_boolean(self):
        self.assertEqual(self.parser_strict.parse("true"), True)
        self.assertEqual(self.parser_strict.parse("false"), False)

    # Array Tests
    def test_empty_array(self):
        self.assertEqual(self.parser_strict.parse("[]"), [])

    def test_number_array(self):
        self.assertEqual(self.parser_strict.parse("[1,2,3]"), [1, 2, 3])

    def test_incomplete_array(self):
        self.assertEqual(self.parser_strict.parse("[1,2,3"), [1, 2, 3])
        self.assertEqual(self.parser_strict.parse("[1,2,"), [1, 2])
        self.assertEqual(self.parser_strict.parse("[1,2"), [1, 2])
        self.assertEqual(self.parser_strict.parse("[1,"), [1])
        self.assertEqual(self.parser_strict.parse("[1"), [1])
        self.assertEqual(self.parser_strict.parse("["), [])

    # Object Tests
    def test_simple_object(self):
        o = {"a": "apple", "b": "banana"}
        self.assertEqual(self.parser_strict.parse('{"a":"apple","b":"banana"}'), o)
        self.assertEqual(self.parser_strict.parse('{"a": "apple","b": "banana"}'), o)
        self.assertEqual(self.parser_strict.parse('{"a" : "apple", "b" : "banana"}'), o)

    # Invalid Inputs
    def test_invalid_input(self):
        with self.assertRaises(Exception):
            self.parser_strict.parse(":atom")

    # Extra Space
    def test_extra_space(self):
        self.assertEqual(self.parser_strict.parse(" [1] "), [1])
        self.assertEqual(self.parser_strict.parse(" [1 "), [1])

    # Unicode Tests
    def test_incomplete_unicode_escape(self):
        with self.assertRaises(Exception):
            self.parser_strict.parse('{"a":"\\', '{"a":"\\"')
            self.parser_strict.parse('{"a":"\\u', '{"a":"\\u"')
            self.parser_strict.parse('{"a":"\\u1', '{"a":"\\u1"')
            self.parser_strict.parse('{"a":"\\u123', '{"a":"\\u123"')

    def test_complete_unicode_escape(self):
        self.assertEqual(self.parser_strict.parse('{"a":"\\u0041"}').get("a"), "A")
        self.assertEqual(self.parser_strict.parse('{"a":"\\u00E9"}').get("a"), "é")
        self.assertEqual(self.parser_strict.parse('{"a":"\\u20AC"}').get("a"), "€")


if __name__ == "__main__":
    unittest.main()
