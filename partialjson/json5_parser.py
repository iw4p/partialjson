"""JSON5 parser - extends JSON with comments, unquoted keys, single quotes, etc."""
import json
import re

try:
    import json5
except ImportError:
    json5 = None


def create_json5_parser(strict=True, on_extra_token=None):
    """Create a JSON5 parser."""
    return _JSON5Parser(strict=strict, on_extra_token=on_extra_token)


def _default_on_extra_token(text, data, reminding):
    print("Parsed JSON with extra tokens:", {"text": text, "data": data, "reminding": reminding})


_INCOMPLETE_ESCAPE_REGEX = re.compile(r"^\\(?:u[0-9a-fA-F]{0,3}|x[0-9a-fA-F]{0,1})?$")
_JSON5_WHITESPACE = "\v\f\u00A0\u2028\u2029\uFEFF"


class _JSON5Parser:
    """JSON5 parser with comments, unquoted keys, single quotes, hex, Infinity, etc."""

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
            "'": self._parse_string,
            "t": self._parse_true,
            "f": self._parse_false,
            "n": self._parse_null,
            "/": self._parse_space,
            "+": self._parse_number,
            "I": self._parse_number,
            "N": self._parse_n_literal,
            "T": self._parse_true,
            "F": self._parse_false,
        }
        for c in _JSON5_WHITESPACE:
            parsers[c] = self._parse_space
        for c in "0123456789.-":
            parsers[c] = self._parse_number
        return parsers

    def parse(self, s):
        if len(s) >= 1:
            if json5:
                try:
                    return json5.loads(s)
                except (json.JSONDecodeError, ValueError) as e:
                    data, reminding = self.parse_any(s, e)
                    self.last_parse_reminding = reminding
                    if self.on_extra_token and reminding:
                        self.on_extra_token(s, data, reminding)
                    return data
            data, reminding = self.parse_any(s, json.JSONDecodeError("", "", 0))
            self.last_parse_reminding = reminding
            if self.on_extra_token and reminding:
                self.on_extra_token(s, data, reminding)
            return data
        return json.loads("{}")

    def parse_any(self, s, e):
        if not s:
            raise e
        while s and self._is_space_or_comment_start(s):
            s = self._parse_space(s, e)
        if not s:
            return None, ""
        parser = self._parsers.get(s[0])
        if not parser:
            raise e
        return parser(s, e)

    def _is_space_or_comment_start(self, s):
        if not s:
            return False
        c = s[0]
        if c.isspace() or c in _JSON5_WHITESPACE:
            return True
        if s.startswith("//") or s.startswith("/*"):
            return True
        return False

    def _parse_space(self, s, e):
        i = 0
        while i < len(s):
            if s[i].isspace() or s[i] in _JSON5_WHITESPACE:
                i += 1
            elif s[i : i + 2] == "//":
                i += 2
                while i < len(s) and s[i] not in "\n\r\u2028\u2029":
                    i += 1
            elif s[i : i + 2] == "/*":
                i += 2
                end = s.find("*/", i)
                if end == -1:
                    return ""
                i = end + 2
            else:
                break
        return s[i:]

    def _parse_array(self, s, e):
        s = s[1:]
        acc = []
        while True:
            while s and self._is_space_or_comment_start(s):
                s = self._parse_space(s, e)
            if not s:
                break
            if s[0] == "]":
                s = s[1:]
                break
            res, s = self.parse_any(s, e)
            acc.append(res)
            while s and self._is_space_or_comment_start(s):
                s = self._parse_space(s, e)
            if s and s.startswith(","):
                s = s[1:]
        return acc, s

    def _parse_object(self, s, e):
        s = s[1:]
        acc = {}
        while True:
            while s and self._is_space_or_comment_start(s):
                s = self._parse_space(s, e)
            if not s:
                break
            if s[0] == "}":
                s = s[1:]
                break
            if s[0] not in '"\'':
                key, s = self._parse_identifier(s, e)
                if not key:
                    while s and self._is_space_or_comment_start(s):
                        s = self._parse_space(s, e)
                    if s and s[0] == "}":
                        s = s[1:]
                    break
            else:
                key, s = self.parse_any(s, e)
            while s and self._is_space_or_comment_start(s):
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
            while s and self._is_space_or_comment_start(s):
                s = self._parse_space(s, e)
            if not s or s[0] in ",}":
                acc[key] = None
                if s and s.startswith(","):
                    s = s[1:]
                elif s and s.startswith("}"):
                    s = s[1:]
                break
            while s and self._is_space_or_comment_start(s):
                s = self._parse_space(s, e)
            if s and (
                s[0] in self._parsers
                or s[0] in "/+IN"
                or s[0] in _JSON5_WHITESPACE
            ):
                value, s = self.parse_any(s, e)
                acc[key] = value
            else:
                if key is not None:
                    acc[key] = None
                break
            while s and self._is_space_or_comment_start(s):
                s = self._parse_space(s, e)
            if s and s.startswith(","):
                s = s[1:]
        return acc, s

    def _parse_identifier(self, s, e):
        i = 0
        while i < len(s) and (s[i].isalnum() or s[i] in "_$"):
            i += 1
        return s[:i], s[i:]

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
                if quote == "'":
                    return content, ""
                return json.loads(f'"{content}"'), ""
            except json.JSONDecodeError:
                return "", ""

        str_val = s[: end + 1]
        remainder = s[end + 1 :]

        if json5:
            try:
                return json5.loads(str_val), remainder
            except Exception:
                pass

        decoded = str_val[1:-1]
        decoded = re.sub(r"\\\n", "", decoded)
        decoded = re.sub(r"\\\r\n", "", decoded)

        def replace_hex(match):
            return chr(int(match.group(1), 16))

        decoded = re.sub(r"\\x([0-9a-fA-F]{2})", replace_hex, decoded)

        if quote == "'":
            decoded = decoded.replace('"', '\\"').replace("\\'", "'")
            try:
                return json.loads(f'"{decoded}"'), remainder
            except Exception:
                return decoded, remainder
        if "\\x" in decoded or "\\\n" in str_val or "\\\r" in str_val:
            return decoded, remainder
        try:
            return json.loads(str_val), remainder
        except Exception:
            return decoded, remainder

    def _parse_number(self, s, e):
        if s.startswith(("-0x", "-0X")):
            i = 3
            while i < len(s) and s[i] in "0123456789abcdefABCDEF":
                i += 1
            num_str = s[1:i]
            remainder = s[i:]
            if len(num_str) <= 2:
                return s[:3], ""
            return -int(num_str, 16), remainder
        if s.startswith(("+0x", "+0X")):
            i = 3
            while i < len(s) and s[i] in "0123456789abcdefABCDEF":
                i += 1
            num_str = s[1:i]
            remainder = s[i:]
            if len(num_str) <= 2:
                return s[:3], ""
            return int(num_str, 16), remainder
        if s.startswith(("0x", "0X")):
            i = 2
            while i < len(s) and s[i] in "0123456789abcdefABCDEF":
                i += 1
            num_str = s[:i]
            remainder = s[i:]
            if len(num_str) <= 2:
                return num_str, ""
            return int(num_str, 16), remainder

        for literal, val in [("Infinity", float("inf")), ("NaN", float("nan"))]:
            if s.startswith(literal):
                return val, s[len(literal) :]
            if s.startswith("+" + literal):
                return val, s[len(literal) + 1 :]
            if s.startswith("-" + literal):
                return -val if literal == "Infinity" else val, s[len(literal) + 1 :]

        if s.startswith(".") and len(s) > 1 and s[1].isdigit():
            i = 1
            while i < len(s) and s[i].isdigit():
                i += 1
            num_str = s[:i]
            return float(num_str), s[i:]

        if s.startswith("+"):
            res, remainder = self._parse_number(s[1:], e)
            return res, remainder

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

    def _parse_n_literal(self, s, e):
        if s.lower().startswith("nan"):
            return self._parse_number(s, e)
        return self._parse_null(s, e)

    def _parse_true(self, s, e):
        if s.lower().startswith("true"):
            return True, s[4:]
        raise e

    def _parse_false(self, s, e):
        if s.lower().startswith("false"):
            return False, s[5:]
        raise e

    def _parse_null(self, s, e):
        if s.lower().startswith("null"):
            return None, s[4:]
        raise e
