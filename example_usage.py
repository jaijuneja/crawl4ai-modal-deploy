import requests
import os
from dotenv import load_dotenv

load_dotenv()

CRAWLER_ENDPOINT = os.getenv("CRAWLER_ENDPOINT", "<your_modal_endpoint>")
BEARER_TOKEN = os.getenv("BEARER_TOKEN", "<your_bearer_token>")

payload = {
    "url": "https://example.com/",
    "bypass_cache": False,
    "autoparse_pdf": False
}

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {BEARER_TOKEN}"
}

response = requests.post(CRAWLER_ENDPOINT, json=payload, headers=headers)

if response.ok:
    result = response.json()
    print(result)
else:
    print(f"Error: {response.status_code} - {response.text}")