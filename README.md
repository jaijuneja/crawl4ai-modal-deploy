# Crawl4AI Modal App

This is a simple repo to deploy the [Crawl4AI](https://github.com/unclecode/crawl4ai) web scraper as a Modal app, served via a FastAPI endpoint. This enables you to crawl any URL from a 3rd party app by sending a POST request to the endpoint.

Modal is a serverless cloud solution that only charges for compute time. This makes it ideal for running web scrapers that are called intermittently.

Modal takes care of infrastructure and scaling, and ensures that the crawler runs fast, auto-scales to handle higher workloads, and scales down when the crawler is idle to avoid unnecessary costs.

This implementation deploys the crawl endpoint and uses a Bearer token in the header for authentication. Instructions for setting up authentication are below.

## Instructions for Deploying in Modal

1. Sign up for a Modal account if you haven't already at https://modal.com/
2. Clone this repo
3. Inside the repo run:
    ```
    pip install modal
    python3 -m modal setup
    ```
    This will authorize your account on your local machine.
4. Set up a secret key for the app and create an auth token to be included in the request header:
    ```
    python3 generate_token.py
    ```
    This will generate a secret key and a token. Save the secret key in a secure location and include the token in the header when making requests to the app.
5. Push the secret key to the Modal app:
    ```
    modal secret create crawler-auth-secret SECRET_KEY="your_generated_secret_key"
    ```

    Or alternatively you can set up the secret via the Modal UI at:
    ```
    https://modal.com/secrets/<your_username>/main/create?secret_name=crawler-auth-secret   
    ```
6. Run the following command to deploy the app:
    ```
    modal deploy start.py
    ```

In your Modal app you will now be able to see the crawler endpoint, which typically looks something like this:

```
https://<your-modal-username>--crawler-crawl.modal.run
```

## Example Usage

```
import requests

ENDPOINT = "<your_modal_endpoint>"
BEARER_TOKEN = "<your_bearer_token>"

payload = {
    "url": "https://example.com",
    "bypass_cache": False,
    "autoparse_pdf": False
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
```

## PDF Parsing

As of Crawl4AI v0.5.0, the crawler supports parsing of PDF content by invoking the `PDFCrawlerStrategy`.

We have added an optional field to the request payload called `autoparse_pdf`. When set to `True` the endpoint will check if the URL is a PDF (based on the URL pattern and Content-Type header) and, if so, will apply the `PDFCrawlerStrategy`. `autoparse_pdf` defaults to `False`.

## Author

This repo was created by [Jai Juneja](https://github.com/jaijuneja) at [QX Labs](https://www.qxlabs.com).