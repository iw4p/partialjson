# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
