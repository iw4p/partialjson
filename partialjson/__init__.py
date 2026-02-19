"""
Partial Json.

Parsing ChatGPT JSON stream response — Partial and incomplete JSON parser python library for OpenAI
"""

from .json_parser import JSONParser, create_json_parser
from .json5_parser import create_json5_parser

__version__ = "1.1.0"
__author__ = "Nima Akbarzadeh"
__author_email__ = "iw4p@protonmail.com"
__license__ = "MIT"
__url__ = "https://github.com/iw4p/partialjson"

PYPI_SIMPLE_ENDPOINT: str = "https://pypi.org/project/partialjson"

__all__ = [
    "JSONParser",
    "create_json_parser",
    "create_json5_parser",
    "PYPI_SIMPLE_ENDPOINT",
]
