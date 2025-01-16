import requests
import json

url = "https://qvapay.com/api/p2p"
response = requests.get(url)
base = response.json()
categories = list(base.keys())
print("Categories:", categories)

# Inspect the data structure
#print(json.dumps(data, indent=4))

