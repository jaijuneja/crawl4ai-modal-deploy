import modal
import logging
import aiohttp
from urllib.parse import urlparse
    
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

from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.processors.pdf import PDFCrawlerStrategy, PDFContentScrapingStrategy
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
    autoparse_pdf: bool = Field(default=False)

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

async def is_pdf_url(url: str) -> bool:
    """
    Determine if a URL points to a PDF by checking both the URL pattern
    and making a HEAD request to check the content type.
    """
    # First check URL pattern (fast check before making request)
    parsed_url = urlparse(url)
    print(parsed_url.path.lower())
    if parsed_url.path.lower().endswith('.pdf'):
        print("It's a PDF")
        return True
        
    try:
        # Make HEAD request to check content type
        async with aiohttp.ClientSession() as session:
            async with session.head(url, allow_redirects=True) as response:
                content_type = response.headers.get('Content-Type', '').lower()
                return 'application/pdf' in content_type
    except Exception as e:
        logger.warning(f"Failed to check content type for URL: {url}", extra={
            "error": str(e),
            "error_type": type(e).__name__
        })
        # Fall back to URL pattern check only
        return False

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

    is_pdf = False
    if request.autoparse_pdf:
        is_pdf = await is_pdf_url(request.url)

    async with AsyncWebCrawler(verbose=True, crawler_strategy=PDFCrawlerStrategy() if is_pdf else None) as crawler:
        crawl_kwargs = request.model_dump(exclude_unset=True)
        try:
            result = await crawler.arun(
                **crawl_kwargs,
                config=CrawlerRunConfig(
                    scraping_strategy=PDFContentScrapingStrategy()
                ) if is_pdf else None
            )
            logger.info("Crawl completed successfully", extra={
                "url": request.url,
                "client_id": payload["client_id"],
                "autoparse_pdf": request.autoparse_pdf,
                "is_pdf": is_pdf
            })
            return result

        except Exception as e:
            logger.error("Crawl failed", extra={
                "url": request.url,
                "client_id": payload["client_id"],
                "autoparse_pdf": request.autoparse_pdf,
                "is_pdf": is_pdf,
                "error": str(e),
                "error_type": type(e).__name__,
            })
            return {"error": f"Error during crawling: {str(e)}"}
        