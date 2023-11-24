# PartialJson

## Parse Partial and incomplete JSON in python

## Example
```python
import json
from partialjson.json_parser import JSONParser
parser = JSONParser()

incomplete_json = '{"name": "John", "age": 30, "is_student": false, "courses": ["Math", "Science"'
print("Testing with incomplete JSON string:", parser.parse(incomplete_json))
```