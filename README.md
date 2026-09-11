# PartialJson

[![Partialjson](https://github.com/iw4p/partialjson/raw/main/images/partialjson.png)](https://pypi.org/project/partialjson/)

## Parse Partial and incomplete JSON in python

![](https://github.com/iw4p/partialjson/raw/main/images/partialjson.gif)

### Parse Partial and incomplete JSON in python with just 3 lines of python code.

[![PyPI version](https://img.shields.io/pypi/v/partialjson.svg)](https://pypi.org/project/partialjson)
[![Supported Python versions](https://img.shields.io/pypi/pyversions/partialjson.svg)](#Installation)
[![Downloads](https://pepy.tech/badge/partialjson)](https://pepy.tech/project/partialjson)

## Example

```python
from partialjson import JSONParser
parser = JSONParser()

incomplete_json = '{"name": "John Doe", "age": 30, "is_student": false, "courses": ["Math", "Science"'
print(parser.parse(incomplete_json))
# {'name': 'John Doe', 'age': 30, 'is_student': False, 'courses': ['Math', 'Science']}
```

Problem with `\n`? Use `strict=False`:

```python
from partialjson import JSONParser
parser = JSONParser(strict=False)

incomplete_json = '{"name": "John\nDoe", "age": 30, "is_student": false, "courses": ["Math", "Science"'
print(parser.parse(incomplete_json))
# {'name': 'John\nDoe', 'age': 30, 'is_student': False, 'courses': ['Math', 'Science']}
```

### JSON5 support

Use `create_json5_parser` or `JSONParser(json5_enabled=True)` for JSON5 (comments, unquoted keys, single quotes, etc.):

```python
from partialjson import create_json5_parser
parser = create_json5_parser()

incomplete_json5 = '{name: "Demo", version: 1.0, items: [1, 2, 3,]'
print(parser.parse(incomplete_json5))
# {'name': 'Demo', 'version': 1.0, 'items': [1, 2, 3]}
```

The optional `json5` dependency speeds up parsing of complete JSON5 documents: `pip install partialjson[json5]`. Partial documents parse the same way with or without it.

### What you get while a string is still streaming

Text that has already arrived is returned; only what cannot be decided yet is held back. With `strict=True` (the default) escapes are decoded and an unfinished escape or half an emoji is dropped until it is complete:

```python
parser.parse('{"msg": "caf\\u00')        # {'msg': 'caf'}
parser.parse('{"msg": "caf\\u00e9"')      # {'msg': 'café'}
parser.parse('{"msg": "hi \\ud83d"')      # {'msg': 'hi '}
parser.parse('{"msg": "hi \\ud83d\\ude00"')  # {'msg': 'hi 😀'}
```

With `strict=False` the raw text of an unfinished string is returned untouched, backslashes included.

### Extra tokens

If the input contains a complete value followed by more text, the value is returned and the callback passed as `on_extra_token` is called with the input, the value and the leftover text. The default callback prints to stdout; pass `on_extra_token=None` to silence it, or read `parser.last_parse_reminding` afterwards.

```python
parser = JSONParser(on_extra_token=None)
parser.parse('{"a": 1} trailing')   # {'a': 1}
parser.last_parse_reminding         # ' trailing'
```

### Installation

```sh
$ pip install partialjson
```

Also can be found on [pypi](https://pypi.org/project/partialjson/)

### How can I use it?

- Install the package by pip package manager.
- After installing, you can use it and call the library.

## Testing

```bash
pip install -e '.[json5]'
pip install -r requirements-dev.txt
pytest -q
```

`tests/test_compat_1_1_0.py` runs the frozen 1.1.0 parser next to the current one over every prefix of a corpus of documents, so behaviour changes for existing users show up as test failures.

## Citation

If you use this software, please cite it using the metadata in `CITATION.cff`.

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=iw4p/partialjson&type=Date)](https://star-history.com/#iw4p/partialjson&Date)

### Issues

Feel free to submit issues and enhancement requests or contact me via [vida.page/nima](https://vida.page/nima).

### Contributing

Please refer to each project's style and contribution guidelines for submitting patches and additions. In general, we follow the "fork-and-pull" Git workflow.

1.  **Fork** the repo on GitHub
2.  **Clone** the project to your own machine
3.  **Update the Version** inside `partialjson/__init__.py` and add a `CHANGELOG.md` entry (a release is published to PyPI when a `vX.Y.Z` tag is pushed, not on merge)
4.  **Commit** changes to your own branch
5.  **Push** your work back up to your fork
6.  Submit a **Pull request** so that we can review your changes
