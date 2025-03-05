import modal
import logging

# Install the necessary dependencies as custom container image which we will pass to our functions
crawler = modal.Image.debian_slim(python_version="3.10").pip_install_from_requirements("requirements.txt").run_commands(
    "apt-get update",
    "apt-get install -y software-properties-common libgtk-3-0 libnotify-dev "
    "libgdk-pixbuf2.0-0 libx11-xcb1 libxcomposite1 libxcursor1 libxdamage1 "
    "libxfixes3 libxi6 libxtst6 libnss3 libxrandr2 libatk1.0-0 "
    "libatk-bridge2.0-0 libdrm2 libgbm1 libpango-1.0-0 libcairo2 "
    "libpangocairo-1.0-0 libxss1",
    "apt-add-repository non-free",
    "apt-add-repository contrib",
    "playwright install-deps chromium",
    "playwright install chromium",
    "playwright install",
)

from crawl4ai import AsyncWebCrawler
from pydantic import BaseModel, Field
from fastapi import Header, HTTPException
from jwt import decode, PyJWTError
import os

# Initialize Modal app and logger
app = modal.App("crawler")
secret = modal.Secret.from_name("crawler-auth-secret")
logger = logging.getLogger(__name__)

class CrawlRequest(BaseModel):
    url: str
    bypass_cache: bool = Field(default=False)

def validate_token(authorization: str) -> dict:
    """Validate JWT token and return payload if valid"""
    try:
        token = authorization.replace('Bearer ', '')
        payload = decode(token, os.environ["SECRET_KEY"], algorithms=["HS256"])
        
        # Optional: Add additional validation
        if "permissions" not in payload or "crawl" not in payload["permissions"]:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
            
        return payload
    except PyJWTError as e:
        raise HTTPException(status_code=401, detail="Invalid authentication token")

@app.function(image=crawler, secrets=[secret])
@modal.web_endpoint(method="POST", docs=True)
async def crawl(request: CrawlRequest, authorization: str = Header(...)):
    """Main crawl function to be executed in Modal container"""
    # Validate token before processing request
    payload = validate_token(authorization)
    
    logger.info("Crawl request received", extra={
        "client_id": payload["client_id"],
        "url": request.url,
        "bypass_cache": request.bypass_cache
    })

    # Create an instance of AsyncWebCrawler
    async with AsyncWebCrawler(verbose=True) as crawler:
        # Run the crawler on the given URL
        crawl_kwargs = request.model_dump(exclude_unset=True)
        try:
            result = await crawler.arun(**crawl_kwargs)
            logger.info("Crawl completed successfully", extra={
                "url": request.url,
                "client_id": payload["client_id"]
            })
            return result
        except Exception as e:
            logger.error("Crawl failed", extra={
                "url": request.url,
                "client_id": payload["client_id"],
                "error": str(e),
                "error_type": type(e).__name__
            })
            return {"error": f"Error during crawling: {str(e)}"}
