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
date: 05 October 2025
bibliography: paper.bib
---

# Summary

`partialjson` is a Python library for extracting useful data from partial or incomplete JSON [@rfc8259] inputs, such as streaming responses from Large Language Models (LLMs) and truncated payloads. It is commonly used to parse the output of models from providers like OpenAI and other streaming APIs. The library recovers as much structure as possible while remaining faithful to JSON semantics, helping researchers and practitioners work with unreliable or progressive data sources.

# Statement of need

JavaScript Object Notation (JSON) has become the de facto standard for data exchange in web APIs, scientific computing pipelines, and machine learning workflows [@rfc8259]. However, many modern applications consume JSON incrementally rather than as complete documents. A prominent use case is parsing streaming responses from Large Language Models (LLMs) such as GPT [@brown2020language], which often output JSON token by token but may be interrupted, rate-limited, or malformed. Similarly, real-time data pipelines, log processing systems, and chunked HTTP transfers frequently encounter partial JSON documents.

Standard JSON parsers, including Python's built-in `json` module [@python-json], reject incomplete buffers with parse errors, forcing researchers to build ad-hoc workarounds such as manual buffering, regular expressions, or fragile state machines to repair invalid JSON. Existing streaming JSON parsers like `ijson` [@ijson] focus on memory-efficient iteration over complete documents rather than recovery from incomplete inputs.

`partialjson` addresses this gap by providing a lightweight, focused solution: it parses arrays, objects, strings, numbers, booleans, and nulls from incomplete inputs and returns the maximal valid prefix together with any remaining unparsed tail. This enables early inspection of partial results, progress reporting for long-running streams, and robust ingestion pipelines for LLM outputs without bespoke parser code. The library has been designed for use in research workflows involving streaming data analysis, interactive LLM applications, and real-time data processing.

# Implementation

`partialjson` implements a recursive-descent parser that attempts standard JSON parsing first and falls back to incremental parsing when encountering incomplete input. The parser tracks the state of nested structures (objects and arrays) and applies recovery strategies based on a configurable strictness mode. In strict mode, the parser maintains JSON specification compliance [@rfc8259] while recovering from missing closing delimiters. In relaxed mode, it additionally handles incomplete escape sequences and embedded newlines that may appear in streaming contexts.

The implementation is pure Python with no runtime dependencies, ensuring easy integration into existing scientific Python environments. The library provides a simple API through a `JSONParser` class with configurable behavior and exposes the remaining unparsed tail for resumption in streaming scenarios.

# Acknowledgements

We thank the open-source JSON parsing community and prior libraries such as `ijson` [@ijson] that inspired streaming-oriented parsing approaches.

# References
