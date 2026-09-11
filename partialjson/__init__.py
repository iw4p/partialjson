"""
Partial Json.

Parse partial and incomplete JSON, such as a streaming LLM response, without
crashing: ``JSONParser().parse('{"a": [1, 2')`` returns ``{"a": [1, 2]}``.
"""

from .json5_parser import create_json5_parser
from .json_parser import JSONParser, create_json_parser

__version__ = "1.2.0"
__author__ = "Nima Akbarzadeh"
__author_email__ = "iw4p@protonmail.com"
__license__ = "MIT"
__url__ = "https://github.com/iw4p/partialjson"

PYPI_SIMPLE_ENDPOINT: str = "https://pypi.org/project/partialjson"

__all__ = [
    "PYPI_SIMPLE_ENDPOINT",
    "JSONParser",
    "create_json5_parser",
    "create_json_parser",
]
