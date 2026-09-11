"""Pure JSON parser - no JSON5 extensions.

The scanner works on string indexes instead of slicing the input on every
token, so a parse is linear in the size of the input. Behaviour is kept
identical to the 1.1.0 release except for the fixes listed in CHANGELOG.md.
"""
import json
from typing import Any, Callable, ClassVar, Dict, FrozenSet, Optional, Tuple, Union

OnExtraToken = Callable[[str, Any, str], None]
ScanResult = Tuple[Any, int]

_HEX = "0123456789abcdefABCDEF"
_NUMBER_CHARS = "0123456789.-+eE"
_NO_KEY = object()  # returned by _scan_key when no key could be read


def create_json_parser(
    strict: bool = True, on_extra_token: Optional[OnExtraToken] = None
) -> "_JSONParser":
    """Create a JSON parser (no JSON5 extensions)."""
    return _JSONParser(strict=strict, on_extra_token=on_extra_token)


def _default_on_extra_token(text: str, data: Any, reminding: str) -> None:
    print("Parsed JSON with extra tokens:", {"text": text, "data": data, "reminding": reminding})


def _is_high_surrogate(hex4: str) -> bool:
    code = int(hex4, 16)
    return 0xD800 <= code <= 0xDBFF


def _is_low_surrogate(hex4: str) -> bool:
    code = int(hex4, 16)
    return 0xDC00 <= code <= 0xDFFF


class _JSONParser:
    """Internal JSON-only parser implementation."""

    # Characters that may legally start a value in this dialect. Used by the
    # object parser to decide whether an unexpected character ends the parse.
    _VALUE_START: ClassVar[FrozenSet[str]] = frozenset('[{"tfn0123456789.-')

    def __init__(
        self, strict: bool = True, on_extra_token: Optional[OnExtraToken] = None
    ) -> None:
        self.strict = strict
        self.on_extra_token: Optional[OnExtraToken] = on_extra_token or _default_on_extra_token
        self.last_parse_reminding: Optional[str] = None

    # ------------------------------------------------------------------ public

    def parse(self, s: Union[str, bytes, bytearray]) -> Any:
        """Parse ``s``, returning as much of the document as is available."""
        if isinstance(s, (bytes, bytearray)):
            s = self._decode_bytes(s)
        if s[:1] == "\ufeff":
            s = s[1:]
        if len(s) >= 1:
            try:
                return self._loads(s)
            except (json.JSONDecodeError, ValueError) as e:
                data, reminding = self.parse_any(s, e)
                self.last_parse_reminding = reminding
                if self.on_extra_token and reminding:
                    self.on_extra_token(s, data, reminding)
                return data
        return json.loads("{}")

    def parse_any(self, s: str, e: BaseException) -> Tuple[Any, str]:
        """Parse one value from the start of ``s``.

        Returns ``(value, remaining_text)``. Raises ``e`` when ``s`` is empty
        or does not start with anything that looks like JSON.
        """
        if not s:
            raise e
        i = self._skip_space(s, 0)
        if i >= len(s):
            return None, ""
        value, i = self._scan_value(s, i, e)
        return value, s[i:]

    # 0.x compatible entry points. Each takes the text and the exception to
    # raise on invalid input, and returns ``(value, remaining_text)``.

    def parse_space(self, s: str, e: BaseException) -> str:
        return s[self._skip_space(s, 0) :]

    def parse_array(self, s: str, e: BaseException) -> Tuple[Any, str]:
        value, i = self._scan_array(s, 0, e)
        return value, s[i:]

    def parse_object(self, s: str, e: BaseException) -> Tuple[Any, str]:
        value, i = self._scan_object(s, 0, e)
        return value, s[i:]

    def parse_string(self, s: str, e: BaseException) -> Tuple[Any, str]:
        value, i = self._scan_string(s, 0, e)
        return value, s[i:]

    def parse_number(self, s: str, e: BaseException) -> Tuple[Any, str]:
        value, i = self._scan_number(s, 0, e)
        return value, s[i:]

    def parse_true(self, s: str, e: BaseException) -> Tuple[Any, str]:
        value, i = self._scan_literal(s, 0, "true", True, e)
        return value, s[i:]

    def parse_false(self, s: str, e: BaseException) -> Tuple[Any, str]:
        value, i = self._scan_literal(s, 0, "false", False, e)
        return value, s[i:]

    def parse_null(self, s: str, e: BaseException) -> Tuple[Any, str]:
        value, i = self._scan_literal(s, 0, "null", None, e)
        return value, s[i:]

    # --------------------------------------------------------------- internals

    @staticmethod
    def _decode_bytes(s: Union[bytes, bytearray]) -> str:
        # A streamed chunk may end in the middle of a multi-byte character;
        # drop the incomplete tail, it will be complete in the next chunk.
        return bytes(s).decode("utf-8", errors="ignore")

    def _loads(self, s: str) -> Any:
        """Fast path for complete documents."""
        return json.loads(s)

    def _is_space(self, s: str, i: int) -> bool:
        return s[i].isspace()

    def _skip_space(self, s: str, i: int) -> int:
        n = len(s)
        while i < n and self._is_space(s, i):
            i += 1
        return i

    def _can_start_value(self, s: str, i: int) -> bool:
        return s[i] in self._VALUE_START

    def _scan_value(self, s: str, i: int, e: BaseException) -> ScanResult:
        """Dispatch on the character at ``s[i]``; whitespace must be skipped."""
        c = s[i]
        if c == "[":
            return self._scan_array(s, i, e)
        if c == "{":
            return self._scan_object(s, i, e)
        if c == '"':
            return self._scan_string(s, i, e)
        if c == "t":
            return self._scan_literal(s, i, "true", True, e)
        if c == "f":
            return self._scan_literal(s, i, "false", False, e)
        if c == "n":
            return self._scan_literal(s, i, "null", None, e)
        if c in "0123456789.-":
            return self._scan_number(s, i, e)
        raise e

    def _scan_array(self, s: str, i: int, e: BaseException) -> ScanResult:
        n = len(s)
        i += 1  # '['
        acc = []
        while True:
            i = self._skip_space(s, i)
            if i >= n:
                break
            if s[i] == "]":
                i += 1
                break
            value, i = self._scan_value(s, i, e)
            acc.append(value)
            i = self._skip_space(s, i)
            if i < n and s[i] == ",":
                i += 1
        return acc, i

    def _scan_key(self, s: str, i: int, e: BaseException) -> ScanResult:
        return self._scan_value(s, i, e)

    def _scan_object(self, s: str, i: int, e: BaseException) -> ScanResult:
        n = len(s)
        i += 1  # '{'
        acc: Dict[Any, Any] = {}
        while True:
            i = self._skip_space(s, i)
            if i >= n:
                break
            if s[i] == "}":
                i += 1
                break
            key, i = self._scan_key(s, i, e)
            if key is _NO_KEY:
                i = self._skip_space(s, i)
                if i < n and s[i] == "}":
                    i += 1
                break
            i = self._skip_space(s, i)
            if i >= n or s[i] == "}":
                if key is not None:
                    acc[key] = None
                if i < n:
                    i += 1
                break
            if s[i] != ":":
                if key is not None:
                    acc[key] = None
                break
            i += 1  # ':'
            i = self._skip_space(s, i)
            if i >= n or s[i] in ",}":
                acc[key] = None
                if i < n:
                    i += 1
                break
            if self._can_start_value(s, i):
                value, i = self._scan_value(s, i, e)
                acc[key] = value
            else:
                if key is not None:
                    acc[key] = None
                break
            i = self._skip_space(s, i)
            if i < n and s[i] == ",":
                i += 1
        return acc, i

    def _scan_string(self, s: str, i: int, e: BaseException) -> ScanResult:
        """Scan a string literal starting at the quote ``s[i]``.

        For an unterminated string the trailing incomplete escape sequence
        (``\\``, ``\\u``, ``\\u1``, ...) and a dangling high surrogate escape
        are dropped, since their final value is not known yet; everything
        before them is returned.
        """
        n = len(s)
        quote = s[i]
        start = i + 1
        j = start
        cut = -1  # where an incomplete escape begins, if the string is cut there
        pending_high = -1  # start index of a high-surrogate escape awaiting its pair
        while j < n:
            c = s[j]
            if c == "\\":
                if j + 1 >= n:
                    cut = j
                    break
                esc = s[j + 1]
                if esc == "u":
                    hex4 = s[j + 2 : j + 6]
                    if len(hex4) < 4 or any(h not in _HEX for h in hex4):
                        if all(h in _HEX for h in hex4) and j + 6 > n:
                            cut = j  # incomplete \uXXXX at end of input
                            break
                        # Malformed escape: let the decoder report it.
                        pending_high = -1
                        j += 2
                        continue
                    if pending_high != -1 and _is_low_surrogate(hex4):
                        pending_high = -1
                    elif _is_high_surrogate(hex4):
                        pending_high = j
                    else:
                        pending_high = -1
                    j += 6
                    continue
                incomplete, length = self._scan_extra_escape(s, j, n)
                if incomplete:
                    cut = j
                    break
                pending_high = -1
                j += length
                continue
            if c == quote:
                break
            pending_high = -1
            j += 1

        if j >= n or cut != -1:
            # Unterminated string.
            if not self.strict:
                return s[start:], n
            end = cut if cut != -1 else n
            if pending_high != -1 and pending_high + 6 == end:
                end = pending_high
            return self._decode_incomplete(quote, s[start:end]), n

        return self._decode_complete(s[i : j + 1], quote), j + 1

    def _scan_extra_escape(self, s: str, j: int, n: int) -> Tuple[bool, int]:
        """Hook for dialects with extra escapes. Returns (incomplete, length)."""
        return False, 2

    def _decode_incomplete(self, quote: str, content: str) -> Any:
        try:
            return json.loads('"' + content + '"')
        except json.JSONDecodeError:
            return ""

    def _decode_complete(self, literal: str, quote: str) -> Any:
        if not self.strict:
            return literal[1:-1]
        return json.loads(literal)

    def _scan_number(self, s: str, i: int, e: BaseException) -> ScanResult:
        n = len(s)
        j = i
        while j < n and s[j] in _NUMBER_CHARS:
            j += 1
        num_str = s[i:j]
        if j >= n:
            # An exponent that has not received its digits yet is dropped.
            stripped = num_str.rstrip("+-")
            if stripped.endswith(("e", "E")):
                num_str = stripped[:-1]
        if not num_str or num_str == "-" or num_str == ".":
            return num_str, n
        try:
            if num_str.endswith("."):
                num: Any = int(num_str[:-1])
            elif "." in num_str or "e" in num_str or "E" in num_str:
                num = float(num_str)
            else:
                num = int(num_str)
        except ValueError:
            raise e from None
        return num, j

    def _literal_matches(self, s: str, i: int, word: str) -> int:
        """Length of the prefix of ``word`` present at ``s[i:]``."""
        n = len(s)
        k = 0
        while i + k < n and k < len(word) and s[i + k] == word[k]:
            k += 1
        return k

    def _scan_literal(
        self, s: str, i: int, word: str, value: Any, e: BaseException
    ) -> ScanResult:
        k = self._literal_matches(s, i, word)
        if k == len(word) or i + k >= len(s):
            return value, i + k
        raise e


# Backward compatibility
class JSONParser:
    """JSON parser. Use create_json_parser() or create_json5_parser() for new code."""

    _impl: _JSONParser
    json5_enabled: bool

    def __init__(
        self,
        strict: bool = True,
        json5_enabled: bool = False,
        on_extra_token: Optional[OnExtraToken] = None,
    ) -> None:
        if json5_enabled:
            from .json5_parser import create_json5_parser

            impl: _JSONParser = create_json5_parser(strict=strict, on_extra_token=on_extra_token)
        else:
            impl = create_json_parser(strict=strict, on_extra_token=on_extra_token)
        object.__setattr__(self, "_impl", impl)
        object.__setattr__(self, "json5_enabled", json5_enabled)

    def parse(self, s: Union[str, bytes, bytearray]) -> Any:
        return self._impl.parse(s)

    def parse_any(self, s: str, e: BaseException) -> Tuple[Any, str]:
        return self._impl.parse_any(s, e)

    @property
    def strict(self) -> bool:
        return self._impl.strict

    @strict.setter
    def strict(self, value: bool) -> None:
        self._impl.strict = value

    @property
    def last_parse_reminding(self) -> Optional[str]:
        return self._impl.last_parse_reminding

    @last_parse_reminding.setter
    def last_parse_reminding(self, value: Optional[str]) -> None:
        self._impl.last_parse_reminding = value

    @property
    def on_extra_token(self) -> Optional[OnExtraToken]:
        return self._impl.on_extra_token

    @on_extra_token.setter
    def on_extra_token(self, value: Optional[OnExtraToken]) -> None:
        self._impl.on_extra_token = value

    def __getattr__(self, name: str) -> Any:
        # Everything else (parse_string, parse_number, ...) lives on the impl.
        return getattr(self._impl, name)
