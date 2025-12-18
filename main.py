"""
🎯 eBay Automation Tool - Main Application
Blazing Fast FastAPI Backend mit allem was das Herz begehrt!
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import asyncio
from typing import List, Optional
import uvicorn
import redis
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from contextlib import asynccontextmanager
import json
from datetime import datetime

from architecture import (
    EbayAutomationEngine, 
    ProductAnalysis, 
    MarketData, 
    ListingContent,
    ListingStatus
)

# 🚀 GLOBAL INSTANCES (Singleton Pattern für Performance)
automation_engine = EbayAutomationEngine()
redis_client = redis.asyncio.Redis(host='localhost', port=6379, db=0)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """App Startup/Shutdown Logic"""
    # Startup
    print("🚀 eBay Automation Engine starting up...")
    # TODO: Database connection, Redis connection tests
    yield
    # Shutdown  
    print("🔄 Graceful shutdown...")
    await redis_client.close()

# 🔥 FASTAPI APP SETUP
app = FastAPI(
    title="eBay Automation API",
    description="KI-powered eBay listing creation tool",
    version="1.0.0",
    lifespan=lifespan
)

# CORS für Frontend Development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ProcessingJob:
    """Job Status Tracking für Async Processing"""
    def __init__(self, job_id: str):
        self.job_id = job_id
        self.status = ListingStatus.ANALYZING
        self.progress = 0
        self.result = None
        self.error = None
        self.created_at = datetime.now()

# 📦 IN-MEMORY JOB STORE (Für MVP, später Redis/Database)
jobs: dict[str, ProcessingJob] = {}

@app.get("/")
async def root():
    """Health Check"""
    return {
        "message": "🎯 eBay Automation API is running!",
        "status": "healthy",
        "version": "1.0.0"
    }

@app.post("/analyze-product")
async def analyze_product_image(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """
    🔍 Produktbild hochladen und Analyse starten
    Returns: Job-ID für Status-Polling
    """
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Job-ID generieren
    import uuid
    job_id = str(uuid.uuid4())
    jobs[job_id] = ProcessingJob(job_id)
    
    # Async Background Processing starten
    background_tasks.add_task(process_product_pipeline, job_id, file)
    
    return {
        "job_id": job_id,
        "message": "Analysis started",
        "status_url": f"/status/{job_id}"
    }

async def process_product_pipeline(job_id: str, file: UploadFile):
    """
    🔄 Komplette Processing Pipeline (Async Background Task)
    1. Bildanalyse → 2. Marktforschung → 3. Content-Generierung → 4. Listing-Vorbereitung
    """
    job = jobs[job_id]
    
    try:
        # STEP 1: Bildanalyse
        job.status = ListingStatus.ANALYZING
        job.progress = 20
        
        # TODO: Save uploaded file temporarily
        # image_url = await save_temp_image(file)
        # product_analysis = await automation_engine.process_product_image(image_url)
        
        # MOCK für Development
        product_analysis = ProductAnalysis(
            brand="Beyerdynamic",
            model="TG V50d", 
            category="instruments",
            condition="Sehr gut",
            key_features=["Dynamic Microphone", "Cardioid", "XLR"],
            confidence_score=0.95
        )
        
        # STEP 2: Marktforschung  
        job.status = ListingStatus.RESEARCHING
        job.progress = 50
        
        market_data = await automation_engine.research_market(product_analysis)
        
        # STEP 3: Content-Generierung
        job.status = ListingStatus.GENERATING
        job.progress = 80
        
        listing_content = await automation_engine.generate_listing(product_analysis, market_data)
        
        # STEP 4: Fertig!
        job.status = ListingStatus.READY
        job.progress = 100
        job.result = {
            "product": product_analysis.__dict__,
            "market": market_data.__dict__,
            "listing": listing_content.__dict__
        }
        
    except Exception as e:
        job.status = ListingStatus.ERROR
        job.error = str(e)
        print(f"❌ Error in job {job_id}: {e}")

@app.get("/status/{job_id}")
async def get_job_status(job_id: str):
    """📊 Job Status abrufen (für Frontend Polling)"""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    return {
        "job_id": job_id,
        "status": job.status.value,
        "progress": job.progress,
        "result": job.result,
        "error": job.error,
        "created_at": job.created_at.isoformat()
    }

@app.post("/publish-listing/{job_id}")
async def publish_listing(job_id: str):
    """🚀 Fertiges Listing auf eBay veröffentlichen"""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    if job.status != ListingStatus.READY:
        raise HTTPException(status_code=400, detail="Listing not ready for publishing")
    
    try:
        # TODO: Actual eBay API call
        listing_content = ListingContent(**job.result["listing"])
        ebay_item_id = await automation_engine.publish_to_ebay(listing_content, [])
        
        job.status = ListingStatus.PUBLISHED
        job.result["ebay_item_id"] = ebay_item_id
        
        return {
            "success": True,
            "ebay_item_id": ebay_item_id,
            "ebay_url": f"https://www.ebay.de/itm/{ebay_item_id}"
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/preview/{job_id}")
async def preview_listing(job_id: str):
    """👀 HTML Preview der generierten Auktion"""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    if not job.result:
        raise HTTPException(status_code=400, detail="No result available")
    
    listing = job.result["listing"]
    
    # Simple HTML Preview
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{listing['title']}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .price {{ color: #e53e3e; font-size: 24px; font-weight: bold; }}
        </style>
    </head>
    <body>
        <h1>{listing['title']}</h1>
        <div class="price">Startpreis: {listing['starting_price']}€</div>
        <div>{listing['description']}</div>
        <p>Keywords: {', '.join(listing['keywords'])}</p>
    </body>
    </html>
    """
    
    return StreamingResponse(
        iter([html_content]), 
        media_type="text/html"
    )

# 🚀 DEVELOPMENT SERVER
if __name__ == "__main__":
    print("🔥 Starting eBay Automation API...")
    uvicorn.run(
        "main:app",
        host="0.0.0.0", 
        port=8000,
        reload=True,
        log_level="info"
    )