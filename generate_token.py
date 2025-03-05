import secrets
import os
from jwt import encode
from dotenv import load_dotenv

load_dotenv()
secret_key = os.getenv("SECRET_KEY")

# Generate a secure random secret key if one doesn't exist in the .env file
if not secret_key:
    secret_key = secrets.token_hex(32)
    print(f"Generated SECRET_KEY (save this somewhere secure): {secret_key}")
else:
    print(f"Using existing SECRET_KEY: {secret_key}")

# Create a sample token to include in the request header and encode this into a Bearer token
payload = {
    "client_id": "crawler_client",
    "permissions": ["crawl"],
}

token = encode(payload, secret_key, algorithm="HS256")
print(f"Generated Bearer token: {token}")