"""JSON5 parser - extends JSON with comments, unquoted keys, single quotes, etc.

Built on top of the JSON scanner in ``json_parser``; only the JSON5-specific
pieces (whitespace and comments, identifiers, extra string escapes, hex and
signed numbers, ``Infinity``/``NaN``, case-insensitive literals) are overridden.
"""
import json
from types import ModuleType
from typing import Any, ClassVar, FrozenSet, Optional, Tuple

from .json_parser import (
    _HEX,
    _NO_KEY,
    OnExtraToken,
    ScanResult,
    _default_on_extra_token,
    _is_high_surrogate,
    _is_low_surrogate,
    _JSONParser,
)

json5: Optional[ModuleType]
try:
    import json5
except ImportError:  # pragma: no cover - exercised via monkeypatching in tests
    json5 = None

__all__ = ["_default_on_extra_token", "create_json5_parser"]

_JSON5_WHITESPACE = "\v\f\u00A0\u2028\u2029\uFEFF"
_LINE_TERMINATORS = "\n\r\u2028\u2029"
_SIMPLE_ESCAPES = {
    "b": "\b",
    "f": "\f",
    "n": "\n",
    "r": "\r",
    "t": "\t",
    "v": "\v",
    "0": "\0",
}


def create_json5_parser(
    strict: bool = True, on_extra_token: Optional[OnExtraToken] = None
) -> "_JSON5Parser":
    """Create a JSON5 parser."""
    return _JSON5Parser(strict=strict, on_extra_token=on_extra_token)


def _decode_json5_string(content: str) -> str:
    """Decode the body of a JSON5 string literal (quotes already removed)."""
    out = []
    i = 0
    n = len(content)
    while i < n:
        c = content[i]
        if c != "\\":
            out.append(c)
            i += 1
            continue
        if i + 1 >= n:
            raise ValueError("incomplete escape")
        esc = content[i + 1]
        if esc == "u":
            hex4 = content[i + 2 : i + 6]
            if len(hex4) < 4 or any(h not in _HEX for h in hex4):
                raise ValueError("bad \\u escape")
            code = int(hex4, 16)
            i += 6
            if _is_high_surrogate(hex4) and content[i : i + 2] == "\\u":
                low = content[i + 2 : i + 6]
                if len(low) == 4 and all(h in _HEX for h in low) and _is_low_surrogate(low):
                    code = 0x10000 + ((code - 0xD800) << 10) + (int(low, 16) - 0xDC00)
                    i += 6
            out.append(chr(code))
        elif esc == "x":
            hex2 = content[i + 2 : i + 4]
            if len(hex2) < 2 or any(h not in _HEX for h in hex2):
                raise ValueError("bad \\x escape")
            out.append(chr(int(hex2, 16)))
            i += 4
        elif esc == "\r":
            i += 3 if content[i + 2 : i + 3] == "\n" else 2
        elif esc in _LINE_TERMINATORS:
            i += 2  # line continuation
        elif esc in _SIMPLE_ESCAPES:
            out.append(_SIMPLE_ESCAPES[esc])
            i += 2
        else:
            out.append(esc)  # \' \" \\ \/ and any other escaped character
            i += 2
    return "".join(out)


class _JSON5Parser(_JSONParser):
    """JSON5 parser with comments, unquoted keys, single quotes, hex, Infinity, etc."""

    _VALUE_START: ClassVar[FrozenSet[str]] = frozenset("[{\"'tfnTFNI+0123456789.-")

    # ------------------------------------------------------------ fast path

    def _loads(self, s: str) -> Any:
        try:
            return json.loads(s)
        except (json.JSONDecodeError, ValueError):
            if json5 is None:
                raise
            return json5.loads(s)

    # ------------------------------------------------- whitespace & comments

    def _is_space(self, s: str, i: int) -> bool:
        c = s[i]
        return c.isspace() or c in _JSON5_WHITESPACE

    def _skip_space(self, s: str, i: int) -> int:
        n = len(s)
        while i < n:
            c = s[i]
            if c.isspace() or c in _JSON5_WHITESPACE:
                i += 1
            elif c == "/":
                if i + 1 >= n:
                    return n  # a comment that has only streamed its first '/'
                nxt = s[i + 1]
                if nxt == "/":
                    i += 2
                    while i < n and s[i] not in _LINE_TERMINATORS:
                        i += 1
                elif nxt == "*":
                    end = s.find("*/", i + 2)
                    if end == -1:
                        return n  # unterminated block comment swallows the rest
                    i = end + 2
                else:
                    break
            else:
                break
        return i

    # --------------------------------------------------------------- values

    def _scan_value(self, s: str, i: int, e: BaseException) -> ScanResult:
        c = s[i]
        if c == "'":
            return self._scan_string(s, i, e)
        if c in "tT":
            return self._scan_literal(s, i, "true", True, e)
        if c in "fF":
            return self._scan_literal(s, i, "false", False, e)
        if c == "n":
            return self._scan_literal(s, i, "null", None, e)
        if c == "N":
            return self._scan_n_literal(s, i, e)
        if c in "+I":
            return self._scan_number(s, i, e)
        return super()._scan_value(s, i, e)

    def _scan_key(self, s: str, i: int, e: BaseException) -> ScanResult:
        if s[i] in "\"'":
            return self._scan_string(s, i, e)
        n = len(s)
        j = i
        while j < n and (s[j].isalnum() or s[j] in "_$"):
            j += 1
        if j == i:
            return _NO_KEY, i
        return s[i:j], j

    # -------------------------------------------------------------- strings

    def _scan_extra_escape(self, s: str, j: int, n: int) -> Tuple[bool, int]:
        esc = s[j + 1]
        if esc == "x":
            hex2 = s[j + 2 : j + 4]
            if all(h in _HEX for h in hex2):
                if len(hex2) < 2:
                    return True, 0  # \x or \xA at the end of the input
                return False, 4
            return False, 2
        if esc == "\r" and s[j + 2 : j + 3] == "\n":
            return False, 3
        return False, 2

    def _decode_incomplete(self, quote: str, content: str) -> Any:
        try:
            return _decode_json5_string(content)
        except ValueError:
            return ""

    def _decode_complete(self, literal: str, quote: str) -> Any:
        try:
            return _decode_json5_string(literal[1:-1])
        except ValueError:
            return literal[1:-1]

    # -------------------------------------------------------------- numbers

    def _scan_number(self, s: str, i: int, e: BaseException) -> ScanResult:
        n = len(s)
        sign = 1
        j = i
        if s[j] in "+-":
            sign = -1 if s[j] == "-" else 1
            j += 1
        if s[j : j + 2] in ("0x", "0X"):
            k = j + 2
            while k < n and s[k] in _HEX:
                k += 1
            if k == j + 2:
                return s[i:k], n  # "0x" with no digits yet
            return sign * int(s[j + 2 : k], 16), k
        for word, value in (("Infinity", float("inf")), ("NaN", float("nan"))):
            k = self._literal_matches(s, j, word)
            if k and (k == len(word) or j + k >= n):
                return sign * value, j + k
        if s[i] == "+":
            if j >= n:
                return "+", n
            return super()._scan_number(s, j, e)
        return super()._scan_number(s, i, e)

    # ------------------------------------------------------------- literals

    def _literal_matches(self, s: str, i: int, word: str) -> int:
        n = len(s)
        k = 0
        while i + k < n and k < len(word) and s[i + k].lower() == word[k].lower():
            k += 1
        return k

    def _scan_n_literal(self, s: str, i: int, e: BaseException) -> ScanResult:
        if s[i + 1 : i + 2].lower() == "a":
            return self._scan_number(s, i, e)
        return self._scan_literal(s, i, "null", None, e)
