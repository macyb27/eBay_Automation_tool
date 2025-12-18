"""
📊 Database Models - High-Performance SQLAlchemy ORM
Optimized für eBay Automation Workflows
"""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any

from sqlalchemy import Column, String, Text, Integer, Float, DateTime, Boolean, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from pydantic import BaseModel

# ========================================
# 🏗️ BASE CONFIGURATION
# ========================================

Base = declarative_base()

# ========================================
# 📋 PROCESSING JOBS TABLE
# ========================================

class Job(Base):
    """
    Processing Jobs für Async Task Tracking
    Ultra-fast für Real-time Status Updates
    """
    __tablename__ = "jobs"
    
    # Primary Key (UUID für bessere Performance bei Distributed Systems)
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Status Tracking
    status = Column(String, nullable=False, default="queued", index=True)
    progress = Column(Integer, default=0)  # 0-100
    message = Column(Text)
    error = Column(Text)
    
    # Timing (für Performance Monitoring)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Input Data
    original_filename = Column(String)
    image_url = Column(String)
    user_preferences = Column(JSON)  # Flexible User Settings
    
    # Results (JSON für schnelle Serialization)
    result = Column(JSON)
    
    # Performance Metrics
    processing_time_ms = Column(Integer)  # Milliseconds
    ai_calls_count = Column(Integer, default=0)
    
    def __repr__(self):
        return f"<Job(id='{self.id}', status='{self.status}', progress={self.progress})>"

# ========================================
# 🏪 EBAY LISTINGS TABLE
# ========================================

class Listing(Base):
    """
    Generated eBay Listings mit Tracking
    """
    __tablename__ = "listings"
    
    # Primary Key
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Reference to Processing Job
    job_id = Column(String, index=True)
    
    # eBay Information
    ebay_item_id = Column(String, unique=True, index=True)
    ebay_url = Column(String)
    
    # Listing Content
    title = Column(String(80), nullable=False)  # eBay Limit
    description = Column(Text)
    starting_price = Column(Integer)  # in Cent
    buy_it_now_price = Column(Integer)  # in Cent
    category_id = Column(String)
    condition = Column(String)
    
    # SEO & Marketing
    seo_keywords = Column(JSON)
    bullet_points = Column(JSON)
    
    # Status & Performance
    is_published = Column(Boolean, default=False)
    views_count = Column(Integer, default=0)
    watchers_count = Column(Integer, default=0)
    sold_price = Column(Integer)  # Final sale price
    
    # Timing
    created_at = Column(DateTime, default=datetime.utcnow)
    published_at = Column(DateTime)
    ended_at = Column(DateTime)
    
    # Analytics
    performance_score = Column(Float)  # 0.0 - 1.0
    success_factors = Column(JSON)
    
    def __repr__(self):
        return f"<Listing(id='{self.id}', title='{self.title[:30]}...', published={self.is_published})>"

# ========================================
# 📊 ANALYTICS & INSIGHTS TABLE
# ========================================

class Analytics(Base):
    """
    Performance Analytics für Continuous Improvement
    """
    __tablename__ = "analytics"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Reference Data
    job_id = Column(String, index=True)
    listing_id = Column(String, index=True)
    
    # Product Category Analytics
    product_category = Column(String, index=True)
    brand = Column(String, index=True)
    condition = Column(String)
    
    # Market Performance
    estimated_price = Column(Integer)
    actual_price = Column(Integer)
    price_accuracy = Column(Float)  # Estimation vs Reality
    
    # AI Performance
    vision_confidence = Column(Float)
    market_accuracy = Column(Float)
    content_quality_score = Column(Float)
    
    # Success Metrics
    time_to_sell = Column(Integer)  # Hours
    view_to_sale_ratio = Column(Float)
    watcher_to_sale_ratio = Column(Float)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Analytics(job_id='{self.job_id}', price_accuracy={self.price_accuracy})>"

# ========================================
# 🔧 SYSTEM CONFIGURATION TABLE
# ========================================

class SystemConfig(Base):
    """
    System Configuration für Dynamic Settings
    """
    __tablename__ = "system_config"
    
    key = Column(String, primary_key=True)
    value = Column(JSON)
    description = Column(Text)
    
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<SystemConfig(key='{self.key}')>"

# ========================================
# 📱 PYDANTIC RESPONSE MODELS
# ========================================

class JobResponse(BaseModel):
    """Response Model für Job APIs"""
    id: str
    status: str
    progress: int
    message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    processing_time_ms: Optional[int] = None

class ListingResponse(BaseModel):
    """Response Model für Listing APIs"""
    id: str
    title: str
    starting_price: int
    category_id: Optional[str] = None
    is_published: bool
    ebay_item_id: Optional[str] = None
    ebay_url: Optional[str] = None
    created_at: datetime
    performance_score: Optional[float] = None

class AnalyticsResponse(BaseModel):
    """Response Model für Analytics APIs"""
    total_jobs: int
    successful_jobs: int
    average_processing_time: float
    average_price_accuracy: float
    top_categories: Dict[str, int]
    performance_trends: Dict[str, float]

# ========================================
# 🎯 UTILITY FUNCTIONS
# ========================================

def create_sample_config():
    """
    Create Default System Configuration
    """
    return [
        SystemConfig(
            key="vision_model",
            value={"model": "gpt-4o", "max_tokens": 2000},
            description="OpenAI Vision Model Configuration"
        ),
        SystemConfig(
            key="content_model", 
            value={"model": "gpt-4o", "temperature": 0.7},
            description="Content Generation Model Settings"
        ),
        SystemConfig(
            key="price_adjustment",
            value={"competitive_factor": 0.95, "market_boost": 1.05},
            description="Dynamic Price Optimization Settings"
        ),
        SystemConfig(
            key="performance_thresholds",
            value={
                "vision_confidence_min": 0.8,
                "market_data_min_samples": 5,
                "content_quality_min": 7.0
            },
            description="Quality Control Thresholds"
        )
    ]