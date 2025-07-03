import os
import time

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.responses import JSONResponse

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

# Check for environment variables
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# Initialize scraper only if environment variables are available
scraper = None
if supabase_url and supabase_key:
    try:
        scraper = JobScraper(
            supabase_url=supabase_url,
            supabase_key=supabase_key,
            browser_use_api_key=os.getenv("BROWSER_USE_API_KEY", "")
        )
    except Exception as e:
        print(f"Warning: Could not initialize scraper: {e}")
        scraper = None
else:
    print("Warning: Supabase environment variables not configured. Scraper functionality disabled.")


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
        if not scraper:
            raise HTTPException(
                status_code=503, 
                detail="Scraper not available. Please configure SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY environment variables."
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
    try:
        result = await handle_github_webhook(request)
        return JSONResponse(content=result, status_code=200)
    except HTTPException as e:
        return JSONResponse(content={"error": e.detail}, status_code=e.status_code)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.post("/webhooks/vercel")
async def vercel_webhook_endpoint(request: Request):
    """Vercel webhook endpoint"""
    try:
        result = await handle_vercel_webhook(request)
        return JSONResponse(content=result, status_code=200)
    except HTTPException as e:
        return JSONResponse(content={"error": e.detail}, status_code=e.status_code)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.get("/")
async def root():
    """Root endpoint"""
    env_status = {
        "supabase_configured": bool(supabase_url and supabase_key),
        "scraper_available": scraper is not None,
        "github_webhook_secret": bool(os.getenv("GITHUB_WEBHOOK_SECRET")),
        "vercel_webhook_secret": bool(os.getenv("VERCEL_WEBHOOK_SECRET"))
    }
    
    return {
        "message": "Job Portal Connector API",
        "status": "running",
        "environment": env_status
    }

# Handle all other routes for SPA compatibility
@app.get("/{path:path}")
async def catch_all(path: str):
    """Catch-all for undefined routes"""
    return {"message": f"Route /{path} not found", "available_routes": [
        "/", "/api/health", "/webhooks/github", "/webhooks/vercel", "/api/scrape"
    ]}
