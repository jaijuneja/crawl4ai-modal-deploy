import requests
import os
from dotenv import load_dotenv

load_dotenv()

ENDPOINT = "<your_modal_endpoint>"
BEARER_TOKEN = os.getenv("BEARER_TOKEN", "<your_bearer_token>")

payload = {
    "url": "https://example.com",
    "bypass_cache": False
}

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {BEARER_TOKEN}"
}

response = requests.post(ENDPOINT, json=payload, headers=headers)

if response.ok:
    result = response.json()
    print(result["markdown"]["raw_markdown"])
else:
    print(f"Error: {response.status_code} - {response.text}")