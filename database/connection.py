"""
💾 Database Connection Manager - Ultra-Fast Async PostgreSQL
Performance-optimized für eBay Automation Tool
"""

import os
import logging
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool

logger = logging.getLogger(__name__)

# ========================================
# 🔧 DATABASE CONFIGURATION
# ========================================

# Database URL mit Fallback für Development
DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'sqlite+aiosqlite:///./ebay_automation.db'  # SQLite für lokales Development
)

# Performance-optimized Engine Configuration
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Disable für Production Performance
    pool_size=20,           # Concurrent connections
    max_overflow=30,        # Additional connections unter Load
    pool_pre_ping=True,     # Connection health checks
    pool_recycle=3600,      # Recycle connections nach 1h
    connect_args={} if "postgresql" in DATABASE_URL else {"check_same_thread": False}
)

# Async Session Factory (Thread-safe)
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Keep objects after commit
    autoflush=True,          # Auto-flush für consistency
    autocommit=False
)

# ========================================
# 🔄 SESSION MANAGEMENT
# ========================================

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI Dependency für Database Sessions
    Optimized für Production mit Error Handling
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()

# ========================================
# 🚀 DATABASE LIFECYCLE
# ========================================

async def init_db():
    """
    Database Initialization - Production Ready
    """
    from .models import Base
    
    try:
        async with engine.begin() as conn:
            # Create all tables
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("✅ Database initialized successfully")
        
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise

async def close_db():
    """
    Graceful Database Shutdown
    """
    try:
        await engine.dispose()
        logger.info("✅ Database connections closed")
    except Exception as e:
        logger.error(f"❌ Database shutdown error: {e}")

# ========================================
# 🔧 UTILITY FUNCTIONS
# ========================================

async def test_connection():
    """
    Database Connection Health Check
    """
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute("SELECT 1")
            return result.scalar() == 1
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False

async def get_connection_info():
    """
    Get Database Connection Information
    """
    return {
        "url": DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else DATABASE_URL,
        "pool_size": engine.pool.size(),
        "checked_out": engine.pool.checkedout(),
        "overflow": engine.pool.overflow(),
        "checked_in": engine.pool.checkedin()
    }