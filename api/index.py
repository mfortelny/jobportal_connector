import os
import time

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .scraper import JobScraper
from .webhooks.handlers import handle_github_webhook, handle_vercel_webhook

app = FastAPI(title="Job Portal Connector", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ScrapeRequest(BaseModel):
    portal_url: str
    username: str
    password: str
    position_name: str
    company_name: str


class ScrapeResponse(BaseModel):
    inserted: int
    skipped: int
    duration_ms: int
    message: str


@app.post("/api/scrape", response_model=ScrapeResponse)
async def scrape_job_portal(request: ScrapeRequest):
    """
    Scrape job portal for candidates and store them in Supabase.
    Prevents duplicates using phone number SHA-256 hashing.
    """
    start_time = time.time()

    try:
        # Initialize scraper
        scraper = JobScraper(
            supabase_url=os.getenv("SUPABASE_URL"),
            supabase_key=os.getenv("SUPABASE_SERVICE_ROLE_KEY"),
            browser_use_api_key=os.getenv("BROWSER_USE_API_KEY"),
        )

        # Run scraping process
        result = await scraper.scrape_candidates(
            portal_url=request.portal_url,
            username=request.username,
            password=request.password,
            position_name=request.position_name,
            company_name=request.company_name,
        )

        duration_ms = int((time.time() - start_time) * 1000)

        return ScrapeResponse(
            inserted=result["inserted"],
            skipped=result["skipped"],
            duration_ms=duration_ms,
            message=f"Successfully processed {result['inserted'] + result['skipped']} candidates",
        )

    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        raise HTTPException(status_code=500, detail=f"Scraping failed: {str(e)}")


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "job-portal-connector"}


@app.post("/webhooks/github")
async def github_webhook_endpoint(request: Request):
    """GitHub webhook endpoint"""
    return await handle_github_webhook(request)


@app.post("/webhooks/vercel")
async def vercel_webhook_endpoint(request: Request):
    """Vercel webhook endpoint"""
    return await handle_vercel_webhook(request)


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Job Portal Connector API",
        "version": "1.0.0",
        "endpoints": {
            "scrape": "/api/scrape", 
            "health": "/api/health",
            "github_webhook": "/webhooks/github",
            "vercel_webhook": "/webhooks/vercel"
        },
    }
