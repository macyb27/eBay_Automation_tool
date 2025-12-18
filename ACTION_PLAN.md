# 🎯 eBay Tool - SOFORT UMSETZBARE ACTION ITEMS
## Priorisierte Task-Liste mit konkreten Code-Änderungen

---

## 🔴 PHASE 1: CORE SERVICES FERTIGSTELLEN (Tag 1-3)

### Task 1.1: Vision Service Response Parser ✅
**File:** `services/vision_service.py`  
**Aktueller Status:** Prompt vorhanden, Response Parsing fehlt  
**Estimated Time:** 2h

```python
# ZU IMPLEMENTIEREN in vision_service.py:

def _parse_analysis_response(self, response: Dict) -> VisionAnalysisResult:
    """Parse OpenAI Vision API response"""
    try:
        # Extract JSON from response
        content = response['choices'][0]['message']['content']
        data = json.loads(content)
        
        # Build ProductFeatures
        product = ProductFeatures(
            name=data['product_name'],
            category=data['category'],
            brand=data.get('brand'),
            condition=data['condition'],
            color=data.get('color'),
            size=data.get('size'),
            material=data.get('material'),
            features=data.get('features', []),
            estimated_age=data.get('estimated_age'),
            defects=data.get('defects', [])
        )
        
        # Parse price range (string "50-100" → tuple)
        price_str = data['estimated_value']
        if '-' in price_str:
            min_val, max_val = price_str.split('-')
            price_range = (int(min_val) * 100, int(max_val) * 100)
        else:
            price = int(price_str) * 100
            price_range = (price, price)
        
        return VisionAnalysisResult(
            product=product,
            confidence_score=data['confidence_score'],
            suggested_keywords=data['seo_keywords'],
            category_suggestions=data['category_suggestions'],
            condition_details=data['condition_details'],
            estimated_value_range=price_range,
            marketing_highlights=data['marketing_highlights']
        )
        
    except (KeyError, ValueError, json.JSONDecodeError) as e:
        logger.error(f"Failed to parse vision response: {e}")
        raise ValueError(f"Invalid API response format: {e}")

async def _call_openai_vision(self, base64_image: str, prompt: str) -> Dict:
    """Call OpenAI Vision API"""
    headers = {
        "Authorization": f"Bearer {self.api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": self.model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 1500,
        "temperature": 0.3  # Lower temp for consistent output
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=payload,
            timeout=aiohttp.ClientTimeout(total=30)
        ) as response:
            if response.status != 200:
                error = await response.text()
                raise Exception(f"OpenAI API Error: {error}")
            
            return await response.json()
```

**Testing:**
```bash
# Unit Test erstellen
pytest tests/test_vision_service.py -v
```

---

### Task 1.2: eBay Finding API - Marktpreise ✅
**File:** `services/ebay_service.py`  
**Aktueller Status:** Skelett vorhanden, API Calls fehlen  
**Estimated Time:** 3h

```python
# ZU IMPLEMENTIEREN in ebay_service.py:

async def _get_completed_listings(
    self, 
    product_name: str, 
    category_id: str = None
) -> List[Dict]:
    """Fetch completed/sold listings from eBay Finding API"""
    
    params = {
        'OPERATION-NAME': 'findCompletedItems',
        'SERVICE-VERSION': '1.0.0',
        'SECURITY-APPNAME': self.app_id,
        'GLOBAL-ID': 'EBAY-DE',
        'RESPONSE-DATA-FORMAT': 'JSON',
        'REST-PAYLOAD': '',
        'keywords': product_name,
        'itemFilter(0).name': 'SoldItemsOnly',
        'itemFilter(0).value': 'true',
        'itemFilter(1).name': 'ListingType',
        'itemFilter(1).value': 'FixedPrice',
        'sortOrder': 'EndTimeSoonest',
        'paginationInput.entriesPerPage': '100'
    }
    
    if category_id:
        params['categoryId'] = category_id
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(
                self.finding_api_url,
                params=params,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status != 200:
                    logger.error(f"eBay API error: {response.status}")
                    return []
                
                data = await response.json()
                
                # Parse response
                search_result = data.get('findCompletedItemsResponse', [{}])[0]
                items = search_result.get('searchResult', [{}])[0].get('item', [])
                
                return [self._parse_ebay_item(item) for item in items]
                
        except asyncio.TimeoutError:
            logger.error("eBay API timeout")
            return []
        except Exception as e:
            logger.error(f"Failed to fetch completed listings: {e}")
            return []

async def _get_active_listings(
    self,
    product_name: str,
    category_id: str = None
) -> List[Dict]:
    """Fetch active listings from eBay Finding API"""
    
    params = {
        'OPERATION-NAME': 'findItemsAdvanced',
        'SERVICE-VERSION': '1.0.0',
        'SECURITY-APPNAME': self.app_id,
        'GLOBAL-ID': 'EBAY-DE',
        'RESPONSE-DATA-FORMAT': 'JSON',
        'REST-PAYLOAD': '',
        'keywords': product_name,
        'itemFilter(0).name': 'ListingType',
        'itemFilter(0).value': 'FixedPrice',
        'sortOrder': 'BestMatch',
        'paginationInput.entriesPerPage': '100'
    }
    
    if category_id:
        params['categoryId'] = category_id
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(
                self.finding_api_url,
                params=params,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status != 200:
                    return []
                
                data = await response.json()
                search_result = data.get('findItemsAdvancedResponse', [{}])[0]
                items = search_result.get('searchResult', [{}])[0].get('item', [])
                
                return [self._parse_ebay_item(item) for item in items]
                
        except Exception as e:
            logger.error(f"Failed to fetch active listings: {e}")
            return []

def _parse_ebay_item(self, item: Dict) -> Dict:
    """Parse single eBay item from API response"""
    try:
        selling_status = item.get('sellingStatus', [{}])[0]
        price = selling_status.get('currentPrice', [{}])[0]
        
        return {
            'item_id': item.get('itemId', [''])[0],
            'title': item.get('title', [''])[0],
            'price': float(price.get('__value__', '0')) * 100,  # Convert to cents
            'condition': item.get('condition', [{}])[0].get('conditionDisplayName', [''])[0],
            'sold': 'soldDate' in selling_status,
            'shipping_cost': self._extract_shipping_cost(item),
            'location': item.get('location', [''])[0],
            'url': item.get('viewItemURL', [''])[0]
        }
    except (KeyError, IndexError, ValueError) as e:
        logger.warning(f"Failed to parse eBay item: {e}")
        return {}

def _calculate_price_statistics(
    self,
    sold_data: List[Dict],
    active_data: List[Dict]
) -> EbayPriceData:
    """Calculate comprehensive price statistics"""
    
    # Filter valid prices
    sold_prices = [item['price'] for item in sold_data if item.get('price', 0) > 0]
    active_prices = [item['price'] for item in active_data if item.get('price', 0) > 0]
    
    if not sold_prices and not active_prices:
        # Return defaults if no data
        return EbayPriceData(
            average_price=0,
            median_price=0,
            min_price=0,
            max_price=0,
            sold_count=0,
            active_listings=0,
            price_trend="unknown",
            competitive_price=0
        )
    
    # Statistics
    all_prices = sold_prices + active_prices
    
    import statistics
    avg_price = int(statistics.mean(all_prices)) if all_prices else 0
    median_price = int(statistics.median(all_prices)) if all_prices else 0
    min_price = min(all_prices) if all_prices else 0
    max_price = max(all_prices) if all_prices else 0
    
    # Competitive pricing (5% below median for better sell chance)
    competitive_price = int(median_price * 0.95) if median_price else 0
    
    # Price trend analysis
    trend = "stable"
    if len(sold_prices) >= 5 and len(active_prices) >= 5:
        recent_sold_avg = statistics.mean(sold_prices[-5:])
        active_avg = statistics.mean(active_prices[:5])
        
        if active_avg > recent_sold_avg * 1.1:
            trend = "rising"
        elif active_avg < recent_sold_avg * 0.9:
            trend = "falling"
    
    return EbayPriceData(
        average_price=avg_price,
        median_price=median_price,
        min_price=min_price,
        max_price=max_price,
        sold_count=len(sold_prices),
        active_listings=len(active_prices),
        price_trend=trend,
        competitive_price=competitive_price
    )
```

**Testing:**
```bash
# Integration Test mit echten API Calls
pytest tests/test_ebay_service.py::test_market_analysis -v
```

---

### Task 1.3: Content Generation - GPT-4 Integration ✅
**File:** `services/content_service.py`  
**Aktueller Status:** Template vorhanden, API Call fehlt  
**Estimated Time:** 2h

```python
# ZU IMPLEMENTIEREN in content_service.py:

async def _call_openai_gpt(self, prompt: str) -> Dict:
    """Call OpenAI GPT-4 for content generation"""
    
    headers = {
        "Authorization": f"Bearer {self.api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "gpt-4-turbo-preview",  # or gpt-4
        "messages": [
            {
                "role": "system",
                "content": """Du bist ein Experte für erfolgreiche eBay-Verkäufe. 
                Erstelle verkaufsfördernde, SEO-optimierte Beschreibungen in deutsch.
                Nutze Emojis sparsam aber wirkungsvoll. Sei ehrlich und präzise."""
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.7,
        "max_tokens": 1500,
        "response_format": {"type": "json_object"}  # Force JSON output
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status != 200:
                    error = await response.text()
                    raise Exception(f"OpenAI API Error: {error}")
                
                return await response.json()
                
        except asyncio.TimeoutError:
            raise Exception("OpenAI API timeout")

def _parse_content_response(
    self,
    response: Dict,
    vision_result: VisionAnalysisResult,
    market_insights: EbayMarketInsights
) -> ListingContent:
    """Parse GPT-4 response and build ListingContent"""
    
    try:
        content = response['choices'][0]['message']['content']
        data = json.loads(content)
        
        return ListingContent(
            title=data['title'][:80],  # eBay limit
            description=data['description'],
            subtitle=data.get('subtitle'),
            bullet_points=data.get('bullet_points', []),
            seo_keywords=data.get('seo_keywords', vision_result.suggested_keywords),
            hashtags=data.get('hashtags', []),
            condition_description=data.get('condition_description', vision_result.condition_details),
            shipping_description=data.get('shipping_description', 'Versand mit DHL, 1-2 Werktage'),
            return_policy=data.get('return_policy', '14 Tage Rückgaberecht')
        )
        
    except (KeyError, json.JSONDecodeError) as e:
        logger.error(f"Failed to parse content response: {e}")
        # Fallback: Generate basic content from vision result
        return self._generate_fallback_content(vision_result, market_insights)

def _generate_fallback_content(
    self,
    vision_result: VisionAnalysisResult,
    market_insights: EbayMarketInsights
) -> ListingContent:
    """Fallback content generation without GPT-4"""
    
    product = vision_result.product
    
    # Simple title
    title_parts = [product.brand, product.name, product.condition]
    title = ' '.join(filter(None, title_parts))[:80]
    
    # Basic description
    description = f"""
    <h2>{product.name}</h2>
    <p><strong>Zustand:</strong> {product.condition}</p>
    <p>{vision_result.condition_details}</p>
    
    <h3>Features:</h3>
    <ul>
    {''.join(f'<li>{feature}</li>' for feature in product.features[:5])}
    </ul>
    
    <p>Bei Fragen gerne melden!</p>
    """
    
    return ListingContent(
        title=title,
        description=description.strip(),
        bullet_points=product.features[:5],
        seo_keywords=vision_result.suggested_keywords[:10],
        hashtags=[],
        condition_description=vision_result.condition_details,
        shipping_description="Versand mit DHL",
        return_policy="14 Tage Rückgaberecht"
    )
```

---

### Task 1.4: Database Connection Setup ✅
**New File:** `database/connection.py`  
**Estimated Time:** 1.5h

```python
# NEU ERSTELLEN: database/connection.py

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
import os
from typing import AsyncGenerator

# Database URL from environment
DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'postgresql+asyncpg://user:password@localhost:5432/ebay_automation'
)

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=True if os.getenv('DEBUG') == 'true' else False,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,  # Verify connections before using
    pool_recycle=3600  # Recycle connections after 1 hour
)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for FastAPI routes"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

async def init_db():
    """Initialize database (create tables)"""
    from .models import Base  # Import after engine creation
    
    async with engine.begin() as conn:
        # Drop all tables (only for development!)
        # await conn.run_sync(Base.metadata.drop_all)
        
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
    
    print("✅ Database initialized")

async def close_db():
    """Close database connections"""
    await engine.dispose()
    print("✅ Database connections closed")
```

**Integration in main.py:**
```python
# In main.py - Update lifespan

from database.connection import init_db, close_db, get_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    """App Startup/Shutdown Logic"""
    # Startup
    print("🚀 eBay Automation Engine starting up...")
    await init_db()  # Initialize database
    # Test Redis connection
    await redis_client.ping()
    print("✅ Redis connected")
    
    yield
    
    # Shutdown  
    print("🔄 Graceful shutdown...")
    await redis_client.close()
    await close_db()
```

---

### Task 1.5: Redis Caching Layer ✅
**New File:** `cache/redis_manager.py`  
**Estimated Time:** 1h

```python
# NEU ERSTELLEN: cache/redis_manager.py

import redis.asyncio as redis
import json
import hashlib
from typing import Optional, Any
from datetime import timedelta
import os

class RedisCache:
    """Async Redis Cache Manager"""
    
    def __init__(self):
        self.redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        self.client: Optional[redis.Redis] = None
    
    async def connect(self):
        """Initialize Redis connection"""
        self.client = redis.from_url(
            self.redis_url,
            encoding="utf-8",
            decode_responses=True
        )
        await self.client.ping()
    
    async def close(self):
        """Close Redis connection"""
        if self.client:
            await self.client.close()
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            value = await self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            print(f"Cache get error: {e}")
            return None
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: int = 3600
    ):
        """Set value in cache with TTL (seconds)"""
        try:
            await self.client.setex(
                key,
                ttl,
                json.dumps(value)
            )
        except Exception as e:
            print(f"Cache set error: {e}")
    
    async def delete(self, key: str):
        """Delete key from cache"""
        try:
            await self.client.delete(key)
        except Exception as e:
            print(f"Cache delete error: {e}")
    
    @staticmethod
    def generate_key(*args) -> str:
        """Generate cache key from arguments"""
        key_string = ':'.join(str(arg) for arg in args)
        return hashlib.md5(key_string.encode()).hexdigest()

# Singleton instance
cache = RedisCache()

# Decorator for caching
def cached(ttl: int = 3600):
    """Decorator to cache function results"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = cache.generate_key(func.__name__, *args, *kwargs.values())
            
            # Try to get from cache
            result = await cache.get(cache_key)
            if result is not None:
                return result
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Store in cache
            await cache.set(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator
```

**Usage in eBay Service:**
```python
# In ebay_service.py

from cache.redis_manager import cache, cached

@cached(ttl=3600)  # Cache for 1 hour
async def analyze_market_prices(self, product_name: str, category_id: str = None):
    # ... existing implementation
    pass
```

---

## 🟡 PHASE 2: INTEGRATION & TESTING (Tag 4-5)

### Task 2.1: Complete Main Pipeline
**File:** `main.py`  
**Estimated Time:** 2h

```python
# UPDATES in main.py:

from database.connection import get_db
from database.models import Job, Listing
from cache.redis_manager import cache

async def process_product_pipeline(job_id: str, file: UploadFile, db: AsyncSession):
    """Complete Processing Pipeline with DB persistence"""
    
    job = await db.get(Job, job_id)
    if not job:
        logger.error(f"Job {job_id} not found in database")
        return
    
    try:
        # STEP 1: Save uploaded image
        job.status = ListingStatus.ANALYZING.value
        job.progress = 10
        await db.commit()
        
        image_data = await file.read()
        # TODO: Upload to S3/Cloud Storage
        image_url = await upload_image_to_storage(image_data)
        job.image_url = image_url
        
        # STEP 2: Vision Analysis
        job.progress = 30
        await db.commit()
        
        product_analysis = await automation_engine.process_product_image(image_data)
        
        # STEP 3: Market Research  
        job.status = ListingStatus.RESEARCHING.value
        job.progress = 50
        await db.commit()
        
        market_data = await automation_engine.research_market(product_analysis)
        
        # STEP 4: Content Generation
        job.status = ListingStatus.GENERATING.value
        job.progress = 80
        await db.commit()
        
        listing_content = await automation_engine.generate_listing(
            product_analysis, 
            market_data
        )
        
        # STEP 5: Save results
        job.status = ListingStatus.READY.value
        job.progress = 100
        job.result = {
            "product": product_analysis.dict(),
            "market": market_data.dict(),
            "listing": listing_content.dict()
        }
        await db.commit()
        
        logger.info(f"✅ Job {job_id} completed successfully")
        
    except Exception as e:
        job.status = ListingStatus.ERROR.value
        job.error = str(e)
        await db.commit()
        logger.error(f"❌ Job {job_id} failed: {e}")
```

---

### Task 2.2: Unit Tests schreiben
**New Directory:** `tests/`  
**Estimated Time:** 3h

```python
# tests/test_vision_service.py

import pytest
from services.vision_service import OpenAIVisionService
import os

@pytest.fixture
def vision_service():
    return OpenAIVisionService(api_key=os.getenv('OPENAI_API_KEY'))

@pytest.mark.asyncio
async def test_analyze_product_image(vision_service):
    # Load test image
    with open('tests/fixtures/test_product.jpg', 'rb') as f:
        image_data = f.read()
    
    result = await vision_service.analyze_product_image(image_data)
    
    assert result.product.name
    assert result.confidence_score > 0.5
    assert len(result.suggested_keywords) > 0
    assert result.estimated_value_range[0] > 0

# tests/test_ebay_service.py

@pytest.mark.asyncio
async def test_market_analysis(ebay_service):
    insights = await ebay_service.analyze_market_prices(
        product_name="iPhone 13 Pro 256GB",
        category_id="9355"
    )
    
    assert insights.price_data.median_price > 0
    assert insights.price_data.sold_count >= 0
    assert insights.competition_level in ["low", "medium", "high"]
```

---

## 🎯 ZUSAMMENFASSUNG - WAS JETZT ZU TUN IST

### **Option A: Schrittweise Fertigstellung** 
Ich implementiere Task für Task und du kannst zwischendurch testen:

1. **Tag 1:** Vision Service finalisieren (2h)
2. **Tag 2:** eBay API Integration (3h)  
3. **Tag 3:** Content Generation + Database (3.5h)
4. **Tag 4:** Redis Caching + Pipeline Integration (3h)
5. **Tag 5:** Testing + Bugfixes (3h)

**Total: ~14.5h reine Development Time**

### **Option B: Komplett-Paket**
Ich erstelle alle Files in einem Durchgang, du deployest und testest dann alles zusammen.

### **Option C: Prioritäten setzen**
Du sagst mir, welche Features am wichtigsten sind, und ich fokussiere mich darauf.

---

## 📞 NÄCHSTER SCHRITT

**Was möchtest du als Erstes fertigstellen?**

1. ✅ Vision Service komplett funktionsfähig
2. ✅ eBay Marktpreise live abrufen
3. ✅ Content Generation mit GPT-4
4. ✅ Alles zusammen in volle Pipeline integrieren
5. ⚡ Oder: "Gib Gas, mach alles fertig!" 🚀

**Sag mir, wo ich ansetzen soll, und wir rocken das Ding! 💪**
