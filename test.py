import unittest
from partialjson.json_parser import JSONParser

class TestJSONParser(unittest.TestCase):
    def setUp(self):
        self.parser = JSONParser()

    # Number Tests
    def test_positive_integer(self):
        self.assertEqual(self.parser.parse("42"), 42)

    def test_negative_integer(self):
        self.assertEqual(self.parser.parse("-42"), -42)

    def test_positive_float(self):
        self.assertEqual(self.parser.parse("12.34"), 12.34)

    def test_negative_float(self):
        self.assertEqual(self.parser.parse("-12.34"), -12.34)

    def test_incomplete_positive_float(self):
        self.assertEqual(self.parser.parse("12."), 12)

    def test_incomplete_negative_float(self):
        self.assertEqual(self.parser.parse("-12."), -12)

    # def test_incomplete_negative_integer(self):
    #     self.assertEqual(self.parser.parse("-"), -0)

    def test_invalid_number(self):
        with self.assertRaises(Exception):
            self.parser.parse("1.2.3.4")

    # String Tests
    def test_string(self):
        self.assertEqual(self.parser.parse('"I am text"'), 'I am text')
        self.assertEqual(self.parser.parse('"I\'m text"'), "I'm text")
        self.assertEqual(self.parser.parse('"I\\"m text"'), 'I"m text')

    def test_incomplete_string(self):
        with self.assertRaises(Exception):
            self.parser.parse('"I am text')
            self.parser.parse('"I\'m text')
            self.parser.parse('"I\\"m text')

    # Boolean Tests
    def test_boolean(self):
        self.assertEqual(self.parser.parse("true"), True)
        self.assertEqual(self.parser.parse("false"), False)

    # Array Tests
    def test_empty_array(self):
        self.assertEqual(self.parser.parse("[]"), [])

    def test_number_array(self):
        self.assertEqual(self.parser.parse("[1,2,3]"), [1, 2, 3])

    def test_incomplete_array(self):
        self.assertEqual(self.parser.parse("[1,2,3"), [1, 2, 3])
        self.assertEqual(self.parser.parse("[1,2,"), [1, 2])
        self.assertEqual(self.parser.parse("[1,2"), [1, 2])
        self.assertEqual(self.parser.parse("[1,"), [1])
        self.assertEqual(self.parser.parse("[1"), [1])
        self.assertEqual(self.parser.parse("["), [])

    # Object Tests
    def test_simple_object(self):
        o = {"a": "apple", "b": "banana"}
        self.assertEqual(self.parser.parse('{"a":"apple","b":"banana"}'), o)
        self.assertEqual(self.parser.parse('{"a": "apple","b": "banana"}'), o)
        self.assertEqual(self.parser.parse('{"a" : "apple", "b" : "banana"}'), o)

    # Invalid Inputs
    def test_invalid_input(self):
        with self.assertRaises(Exception):
            self.parser.parse(":atom")

    # Extra Space
    def test_extra_space(self):
        self.assertEqual(self.parser.parse(" [1] "), [1])
        self.assertEqual(self.parser.parse(" [1 "), [1])

if __name__ == '__main__':
    unittest.main()
