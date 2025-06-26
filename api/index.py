from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import time
from typing import Dict, Any
import asyncio

from .scraper import JobScraper

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
            browser_use_api_key=os.getenv("BROWSER_USE_API_KEY")
        )
        
        # Run scraping process
        result = await scraper.scrape_candidates(
            portal_url=request.portal_url,
            username=request.username,
            password=request.password,
            position_name=request.position_name,
            company_name=request.company_name
        )
        
        duration_ms = int((time.time() - start_time) * 1000)
        
        return ScrapeResponse(
            inserted=result["inserted"],
            skipped=result["skipped"],
            duration_ms=duration_ms,
            message=f"Successfully processed {result['inserted'] + result['skipped']} candidates"
        )
        
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        raise HTTPException(
            status_code=500,
            detail=f"Scraping failed: {str(e)}"
        )

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "job-portal-connector"}

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Job Portal Connector API",
        "version": "1.0.0",
        "endpoints": {
            "scrape": "/api/scrape",
            "health": "/api/health"
        }
    } 