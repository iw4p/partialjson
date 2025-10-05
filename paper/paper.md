---
title: "partialjson: Parsing incomplete JSON streams safely in Python"
tags:
  - Python
  - JSON
  - streaming
  - parsing
  - LLM
  - OpenAI
authors:
  - name: Nima Akbarzadeh
    orcid: 0009-0005-8143-8083
    affiliation: 1
affiliations:
  - name: Independent Researcher
    index: 1
date: 2025-10-05
bibliography: paper.bib
---

# Summary

partialjson is a small Python library for extracting useful data from partial or incomplete JSON inputs, such as streaming responses from Large Language Models (LLMs) and truncated payloads. It is commonly used to parse the output of models from providers like OpenAI. The library recovers as much structure as possible while remaining faithful to JSON semantics, helping researchers and practitioners work with unreliable or progressive sources (e.g., HTTP chunked transfer, LLM token streams, and log tails).

# Statement of need

Many data-centric research workflows increasingly consume JSON incrementally. A prominent use case is parsing streaming responses from LLMs, which often output JSON token by token but may be interrupted or malformed. Standard parsers reject these incomplete buffers, forcing researchers to build ad-hoc workarounds like buffering, regexes, or fragile state machines to repair the invalid JSON. partialjson provides a focused, lightweight solution: it parses arrays, objects, strings, numbers, booleans, and nulls from incomplete inputs and returns the maximal valid prefix. This enables early inspection, progress reporting, and robust ingestion pipelines for LLM outputs without bespoke parser code.

# Functionality

partialjson exposes a simple factory‑style API to parse any incoming buffer and return Python data structures. It supports a strict mode for standards‑compliant behavior and a relaxed mode for pragmatic recovery of incomplete strings or numbers. Typical usage requires only a few lines of code and integrates with stream readers or callback loops. The library is pure‑Python with no runtime dependencies and works across supported CPython versions.

Key features:

- Parse incomplete objects and arrays, recovering maximal valid structure
- Handle strings, numbers, booleans, and nulls with optional relaxed handling
- Report remaining unparsed tail for resumed parsing
- Minimal API and small footprint

See the project README for installation and examples.

# Acknowledgements

We thank open‑source JSON tooling and prior libraries that inspired streaming‑oriented parsing approaches.

# References
