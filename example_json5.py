"""Demo: JSON5 support in partialjson — streaming like example.py."""
from partialjson.json_parser import JSONParser
import time
import sys

parser = JSONParser(json5_enabled=True)

# Streaming JSON5: simulate receiving characters one by one
incomplete_json5 = """
{
  // app config
  name: 'Demo',
  version: 1.0,
  hex: 0xff,
  items: [1, 2, 3,],
  nested: { a: .5, b: +42 }
}
"""

json_str = ""
for char in incomplete_json5.strip():
    json_str += char
    print(f"\nIncomplete or streaming JSON5:\n{json_str}")
    print(f"Parsed so far (usable without crashing):\n{parser.parse(json_str)}")
    sys.stdout.flush()
    time.sleep(0.1)
