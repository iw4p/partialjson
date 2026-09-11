# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2026-09-12

No API changes. Every input that 1.1.0 parsed successfully parses to the same
value in 1.2.0, verified by `tests/test_compat_1_1_0.py`, which runs the frozen
1.1.0 parser next to the current one over every prefix of a corpus of documents.

### Fixed

- Numbers with an exponent (`1e5`, `2.5E-3`) inside an incomplete array or
  object raised `JSONDecodeError`. They now parse; an exponent that has not
  received its digits yet (`1e`, `1e-`) is dropped until it is complete.
- In strict mode an unterminated string whose tail was an incomplete escape
  (`"foo\`, `"foo\u00`) returned `""`, discarding text that had already
  streamed. It now returns `"foo"`; only the unfinished escape is held back
  (issue #8).
- In strict mode a string cut between the two halves of a surrogate pair
  (`"\ud83d`, half of an emoji) returned a lone surrogate, which raises
  `UnicodeEncodeError` as soon as it is encoded. The high half is now held
  back until its partner arrives.
- The JSON5 parser raised on partial literals (`{"a": tr`, `[fals`, `[Inf`)
  and on exponent numbers, and treated a comment that had only streamed its
  first `/` as an unknown token. It now behaves like the JSON parser.
- JSON5 string decoding no longer depends on whether the optional `json5`
  package is installed; the same escapes (`\x41`, `\'`, line continuations,
  surrogate pairs) decode the same way either way.
- `bytes` and `bytearray` input, which `json.loads` accepts, no longer crash
  the fallback parser with `AttributeError`. A chunk that ends in the middle
  of a multi-byte UTF-8 character drops the incomplete bytes.
- A leading UTF-8 byte-order mark no longer causes a `JSONDecodeError`.
- `JSONParser.strict`, `.on_extra_token` and `.last_parse_reminding` are
  readable and assignable again (assigning `strict` on a 1.x parser was
  silently ignored), and the 0.x method names `parse_string`, `parse_number`,
  `parse_array`, `parse_object`, `parse_true`, `parse_false`, `parse_null`
  and `parse_space` are callable again.

### Changed

- The scanner works on string indexes instead of re-slicing the input at
  every token, so a parse is linear in the input size. A 900 KB partial
  document went from about 1 s to about 60 ms per `parse()` call.
- A literal that is not a prefix of `true`/`false`/`null` (for example
  `[trap]`, which 1.1.0 returned as `[True]`) now raises, matching
  `json.loads`. Prefixes such as `[t`, `[tru` still parse.
- `_JSON5Parser` is now a subclass of the JSON parser instead of a copy of it.
- Packaging moved to `pyproject.toml` with `requires-python >= 3.8`,
  classifiers and a `py.typed` marker; the package is fully type-annotated.
- CI runs on Python 3.8 through 3.14, with and without the optional `json5`
  dependency.

## [1.1.0] - 2026-02-20

### Added

- JSON5 support: comments, unquoted keys, single-quoted strings, hex numbers,
  `Infinity`/`NaN`, trailing commas. Available through
  `create_json5_parser()` or `JSONParser(json5_enabled=True)`; install
  `partialjson[json5]` for the optional `json5` fast path (issue #9).
- `create_json_parser()` factory.

## [1.0.0] - 2026-02

### Added

- `CITATION.cff`, `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`, JOSS paper draft,
  GitHub Actions test workflow.

### Changed

- `JSONParser` became a thin facade over an internal implementation class.

## [0.1.0] - 2025-01-28

### Fixed

- Incomplete escape sequences (`"\`, `"\u12`) at the end of a streamed
  string no longer raise (issue #8).

## [0.0.8] - 2024-08-03

### Added

- Support `strict` mode based on [this issue](https://github.com/iw4p/partialjson/issues/5)
- Test cases for `parser_strict` and `parser_non_strict` to handle incomplete and complete JSON strings with newline characters.
- Example usage of both strict and non-strict parsers in the unit tests.
- Unit tests for various number, string, boolean, array, and object parsing scenarios.

### Changed

- Updated incomplete number parsing logic to ensure better error handling and test coverage.

### Fixed

- Fixed issue with parsing incomplete floating point numbers where the parser incorrectly returned an error.
- Corrected string parsing logic to properly handle escape characters in strict mode.

## [0.0.2] - 2023-11-24

### Added

### Changed

### Fixed

- json format

## [0.0.1] - 2023-11-24

### Added

- Initial implementation of `JSONParser` with support for only strict mode.
