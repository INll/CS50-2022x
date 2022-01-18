import os
import requests
import json

response = requests.get("https://zenquotes.io/api/random")
json_data = json.loads(response.text)
print(json_data[0]['q'])