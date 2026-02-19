"""Pure JSON parser - no JSON5 extensions."""
import json
import re


def create_json_parser(strict=True, on_extra_token=None):
    """Create a JSON parser (no JSON5 extensions)."""
    return _JSONParser(strict=strict, on_extra_token=on_extra_token)


def _default_on_extra_token(text, data, reminding):
    print("Parsed JSON with extra tokens:", {"text": text, "data": data, "reminding": reminding})


_INCOMPLETE_ESCAPE_REGEX = re.compile(r"^\\(?:u[0-9a-fA-F]{0,3}|x[0-9a-fA-F]{0,1})?$")


class _JSONParser:
    """Internal JSON-only parser implementation."""

    def __init__(self, strict=True, on_extra_token=None):
        self.strict = strict
        self.on_extra_token = on_extra_token or _default_on_extra_token
        self.last_parse_reminding = None
        self._parsers = self._build_parsers()

    def _build_parsers(self):
        parsers = {
            " ": self._parse_space,
            "\r": self._parse_space,
            "\n": self._parse_space,
            "\t": self._parse_space,
            "[": self._parse_array,
            "{": self._parse_object,
            '"': self._parse_string,
            "t": self._parse_true,
            "f": self._parse_false,
            "n": self._parse_null,
        }
        for c in "0123456789.-":
            parsers[c] = self._parse_number
        return parsers

    def parse(self, s):
        if len(s) >= 1:
            try:
                return json.loads(s)
            except (json.JSONDecodeError, ValueError) as e:
                data, reminding = self.parse_any(s, e)
                self.last_parse_reminding = reminding
                if self.on_extra_token and reminding:
                    self.on_extra_token(s, data, reminding)
                return data
        return json.loads("{}")

    def parse_any(self, s, e):
        if not s:
            raise e
        while s and s[0].isspace():
            s = self._parse_space(s, e)
        if not s:
            return None, ""
        parser = self._parsers.get(s[0])
        if not parser:
            raise e
        return parser(s, e)

    def _parse_space(self, s, e):
        i = 0
        while i < len(s) and s[i].isspace():
            i += 1
        return s[i:]

    def _parse_array(self, s, e):
        s = s[1:]
        acc = []
        while True:
            while s and s[0].isspace():
                s = self._parse_space(s, e)
            if not s:
                break
            if s[0] == "]":
                s = s[1:]
                break
            res, s = self.parse_any(s, e)
            acc.append(res)
            while s and s[0].isspace():
                s = self._parse_space(s, e)
            if s and s.startswith(","):
                s = s[1:]
        return acc, s

    def _parse_object(self, s, e):
        s = s[1:]
        acc = {}
        while True:
            while s and s[0].isspace():
                s = self._parse_space(s, e)
            if not s:
                break
            if s[0] == "}":
                s = s[1:]
                break
            key, s = self.parse_any(s, e)
            while s and s[0].isspace():
                s = self._parse_space(s, e)
            if not s or s[0] == "}":
                if key is not None:
                    acc[key] = None
                if s and s[0] == "}":
                    s = s[1:]
                break
            if s[0] != ":":
                if key is not None:
                    acc[key] = None
                break
            s = s[1:]
            while s and s[0].isspace():
                s = self._parse_space(s, e)
            if not s or s[0] in ",}":
                acc[key] = None
                if s and s.startswith(","):
                    s = s[1:]
                elif s and s.startswith("}"):
                    s = s[1:]
                break
            if s and s[0] in self._parsers:
                value, s = self.parse_any(s, e)
                acc[key] = value
            else:
                if key is not None:
                    acc[key] = None
                break
            while s and s[0].isspace():
                s = self._parse_space(s, e)
            if s and s.startswith(","):
                s = s[1:]
        return acc, s

    def _parse_string(self, s, e):
        quote = s[0]
        end = 1
        while end < len(s):
            if s[end] == "\\":
                end += 2
                continue
            if s[end] == quote:
                break
            end += 1

        if end >= len(s):
            content = s[1:]
            if not self.strict:
                return content, ""
            if _INCOMPLETE_ESCAPE_REGEX.match(content):
                return "", ""
            try:
                return json.loads(f'"{content}"'), ""
            except json.JSONDecodeError:
                return "", ""

        str_val = s[: end + 1]
        remainder = s[end + 1 :]
        if not self.strict:
            return str_val[1:-1], remainder
        return json.loads(str_val), remainder

    def _parse_number(self, s, e):
        i = 0
        while i < len(s) and s[i] in "0123456789.-":
            i += 1
        num_str = s[:i]
        s = s[i:]
        if not num_str or num_str == "-" or num_str == ".":
            return num_str, ""
        try:
            if num_str.endswith("."):
                num = int(num_str[:-1])
            else:
                num = (
                    float(num_str)
                    if "." in num_str or "e" in num_str or "E" in num_str
                    else int(num_str)
                )
        except ValueError:
            raise e
        return num, s

    def _parse_true(self, s, e):
        if s.startswith("t") or s.startswith("T"):
            return True, s[4:]
        raise e

    def _parse_false(self, s, e):
        if s.startswith("f") or s.startswith("F"):
            return False, s[5:]
        raise e

    def _parse_null(self, s, e):
        if s.startswith("n"):
            return None, s[4:]
        raise e


# Backward compatibility
class JSONParser:
    """JSON parser. Use create_json_parser() or create_json5_parser() for new code."""

    def __init__(self, strict=True, json5_enabled=False, on_extra_token=None):
        if json5_enabled:
            from .json5_parser import create_json5_parser

            self._impl = create_json5_parser(strict=strict, on_extra_token=on_extra_token)
        else:
            self._impl = create_json_parser(strict=strict, on_extra_token=on_extra_token)

    def parse(self, s):
        return self._impl.parse(s)

    def parse_any(self, s, e):
        return self._impl.parse_any(s, e)

    @property
    def last_parse_reminding(self):
        return getattr(self._impl, "last_parse_reminding", None)

    @property
    def on_extra_token(self):
        return getattr(self._impl, "on_extra_token", None)

    @on_extra_token.setter
    def on_extra_token(self, value):
        self._impl.on_extra_token = value
