from partialjson.json_parser import JSONParser
import time, sys

parser = JSONParser()

incomplete_json = '{"name": "John", "age": 18, "family":'

json = ""

for char in incomplete_json:
    json += char
    print(f'\nIncomplete or streaming json:\n{json}')
    print(f'Final and usable JSON without crashing:\n{parser.parse(json)}')
    sys.stdout.flush()
    time.sleep(0.3)