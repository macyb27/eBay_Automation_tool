"""
🧪 COMPLETE PIPELINE TESTS - Production Quality Assurance
Ultra-Fast Performance Testing für eBay Automation Tool
"""

import pytest
import asyncio
import os
import time
from httpx import AsyncClient
from io import BytesIO
from PIL import Image

# Test Configuration
TEST_IMAGE_SIZE = (800, 600)
TEST_TIMEOUT = 30  # seconds

# ========================================
# 🔧 TEST FIXTURES
# ========================================

@pytest.fixture
async def test_client():
    """FastAPI Test Client"""
    from main_optimized import app
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.fixture
def sample_image_data():
    """Generate Sample Product Image for Testing"""
    # Create realistic test image
    img = Image.new('RGB', TEST_IMAGE_SIZE, color='white')
    
    # Add some visual elements to simulate product
    from PIL import ImageDraw, ImageFont
    draw = ImageDraw.Draw(img)
    
    # Draw product outline
    draw.rectangle([100, 100, 700, 500], outline='black', width=3)
    draw.text((300, 250), "TEST PRODUCT", fill='black')
    draw.text((300, 300), "iPhone 12 Pro", fill='blue')
    draw.text((300, 350), "128GB Space Gray", fill='gray')
    
    # Convert to bytes
    buffer = BytesIO()
    img.save(buffer, format='JPEG', quality=85)
    return buffer.getvalue()

@pytest.fixture 
def performance_metrics():
    """Performance Tracking Fixture"""
    return {
        'start_time': time.time(),
        'api_calls': 0,
        'cache_hits': 0,
        'cache_misses': 0
    }

# ========================================
# 🚀 CORE PIPELINE TESTS
# ========================================

@pytest.mark.asyncio
class TestCompletePipeline:
    """Complete End-to-End Pipeline Tests"""
    
    async def test_health_check(self, test_client):
        """🏥 API Health Check"""
        response = await test_client.get("/api/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] in ["healthy", "degraded"]
        assert "services" in data
    
    async def test_root_endpoint(self, test_client):
        """🏠 Root Endpoint Information"""
        response = await test_client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert "eBay Automation API" in data["message"]
        assert data["status"] == "blazing_fast"
        assert "features" in data
    
    async def test_complete_workflow_performance(self, test_client, sample_image_data, performance_metrics):
        """
        🎯 MAIN TEST: Complete Workflow Performance
        Target: < 15 seconds für komplette Pipeline
        """
        
        start_time = time.time()
        
        # STEP 1: Upload Image und Start Analysis
        files = {"file": ("test_product.jpg", sample_image_data, "image/jpeg")}
        response = await test_client.post("/api/analyze-product", files=files)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "job_id" in data
        
        job_id = data["job_id"]
        upload_time = time.time() - start_time
        print(f"📤 Upload completed in: {upload_time:.2f}s")
        
        # STEP 2: Poll Status bis Completion
        max_polls = 60  # 60 polls x 0.5s = 30s max
        poll_count = 0
        
        while poll_count < max_polls:
            await asyncio.sleep(0.5)  # 500ms between polls
            
            response = await test_client.get(f"/api/status/{job_id}")
            assert response.status_code == 200
            
            status_data = response.json()
            print(f"📊 Status: {status_data['status']} - Progress: {status_data['progress']}%")
            
            if status_data["status"] == "ready":
                total_time = time.time() - start_time
                print(f"✅ Pipeline completed in: {total_time:.2f}s")
                
                # Performance Assertion
                assert total_time < TEST_TIMEOUT, f"Pipeline too slow: {total_time:.2f}s > {TEST_TIMEOUT}s"
                
                # Validate Result Structure
                assert "result" in status_data
                result = status_data["result"]
                
                # Product Analysis Validation
                assert "product_analysis" in result
                product = result["product_analysis"]
                assert product["confidence_score"] > 0.5
                assert len(product["suggested_keywords"]) > 0
                
                # Market Analysis Validation
                assert "market_analysis" in result
                market = result["market_analysis"]
                assert market["price_data"]["average_price"] > 0
                assert market["competition_level"] in ["low", "medium", "high"]
                
                # Listing Content Validation
                assert "listing_content" in result
                content = result["listing_content"]
                assert len(content["title"]) <= 80  # eBay limit
                assert len(content["description"]) > 100
                assert len(content["seo_keywords"]) > 0
                
                return True
                
            elif status_data["status"] == "error":
                pytest.fail(f"Pipeline failed: {status_data.get('error', 'Unknown error')}")
            
            poll_count += 1
        
        pytest.fail(f"Pipeline timeout after {max_polls * 0.5}s")
    
    async def test_preview_generation(self, test_client, sample_image_data):
        """📱 Preview Generation Test"""
        
        # Upload und Complete Pipeline
        files = {"file": ("test_product.jpg", sample_image_data, "image/jpeg")}
        response = await test_client.post("/api/analyze-product", files=files)
        job_id = response.json()["job_id"]
        
        # Wait for completion (simplified)
        for _ in range(30):
            await asyncio.sleep(1)
            status_response = await test_client.get(f"/api/status/{job_id}")
            if status_response.json()["status"] == "ready":
                break
        
        # Test Preview Generation
        preview_response = await test_client.get(f"/api/preview/{job_id}")
        assert preview_response.status_code == 200
        assert "text/html" in preview_response.headers.get("content-type", "")
        
        html_content = preview_response.text
        assert "eBay Preview" in html_content
        assert "Produktdetails" in html_content
        assert "Empfohlener Startpreis" in html_content

# ========================================
# 🔥 PERFORMANCE TESTS
# ========================================

@pytest.mark.asyncio 
class TestPerformance:
    """Ultra-High Performance Tests"""
    
    async def test_concurrent_requests(self, test_client, sample_image_data):
        """🚀 Concurrent Request Handling"""
        
        async def single_request():
            files = {"file": ("test_product.jpg", sample_image_data, "image/jpeg")}
            response = await test_client.post("/api/analyze-product", files=files)
            return response.status_code == 200
        
        # Test 5 concurrent requests
        start_time = time.time()
        tasks = [single_request() for _ in range(5)]
        results = await asyncio.gather(*tasks)
        
        total_time = time.time() - start_time
        success_count = sum(results)
        
        print(f"🔥 5 concurrent requests completed in: {total_time:.2f}s")
        print(f"✅ Success rate: {success_count}/5")
        
        assert success_count >= 4  # Allow 1 failure
        assert total_time < 10  # All 5 requests < 10s
    
    async def test_large_image_handling(self, test_client):
        """📸 Large Image Processing Performance"""
        
        # Create large test image (2MB+)
        large_img = Image.new('RGB', (2000, 2000), color='red')
        buffer = BytesIO()
        large_img.save(buffer, format='JPEG', quality=95)
        large_image_data = buffer.getvalue()
        
        print(f"📸 Testing large image: {len(large_image_data) / 1024 / 1024:.2f}MB")
        
        start_time = time.time()
        files = {"file": ("large_product.jpg", large_image_data, "image/jpeg")}
        response = await test_client.post("/api/analyze-product", files=files)
        
        upload_time = time.time() - start_time
        print(f"📤 Large image upload: {upload_time:.2f}s")
        
        assert response.status_code == 200
        assert upload_time < 5  # Upload < 5s
    
    async def test_memory_usage(self, test_client, sample_image_data):
        """💾 Memory Usage Optimization"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Process multiple images
        for i in range(3):
            files = {"file": (f"test_{i}.jpg", sample_image_data, "image/jpeg")}
            await test_client.post("/api/analyze-product", files=files)
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        print(f"💾 Memory usage: {initial_memory:.1f}MB -> {final_memory:.1f}MB (+{memory_increase:.1f}MB)")
        
        # Memory shouldn't increase by more than 100MB for 3 images
        assert memory_increase < 100

# ========================================
# 🔧 SERVICE TESTS
# ========================================

@pytest.mark.asyncio
class TestServices:
    """Individual Service Component Tests"""
    
    async def test_vision_service_performance(self, sample_image_data):
        """👁️ Vision Service Speed Test"""
        from services.vision_service import create_vision_service
        
        vision_service = create_vision_service(os.getenv("OPENAI_API_KEY"))
        
        start_time = time.time()
        result = await vision_service.analyze_product_image(sample_image_data)
        analysis_time = time.time() - start_time
        
        print(f"👁️ Vision analysis: {analysis_time:.2f}s")
        print(f"🎯 Confidence: {result.confidence_score:.2f}")
        print(f"📦 Product: {result.product.name}")
        
        # Assertions
        assert analysis_time < 10  # Vision analysis < 10s
        assert result.confidence_score > 0.3  # Minimum confidence
        assert result.product.name  # Product name detected
        assert len(result.suggested_keywords) > 0
    
    async def test_ebay_service_performance(self):
        """🏪 eBay Service Speed Test"""
        from services.ebay_service import create_ebay_service
        
        ebay_service = create_ebay_service(
            os.getenv("EBAY_APP_ID"),
            os.getenv("EBAY_DEV_ID"), 
            os.getenv("EBAY_CERT_ID")
        )
        
        start_time = time.time()
        insights = await ebay_service.analyze_market_prices("iPhone 12 Pro 128GB")
        analysis_time = time.time() - start_time
        
        print(f"🏪 Market analysis: {analysis_time:.2f}s")
        print(f"💰 Average price: {insights.price_data.average_price/100:.2f}€")
        print(f"📊 Competition: {insights.competition_level}")
        
        # Assertions
        assert analysis_time < 15  # Market analysis < 15s
        assert insights.price_data.average_price > 0
        assert insights.success_probability > 0
    
    async def test_content_service_performance(self):
        """✍️ Content Service Speed Test"""
        from services.content_service import create_content_service
        from services.vision_service import VisionAnalysisResult, ProductFeatures
        from services.ebay_service import EbayMarketInsights, EbayPriceData
        
        content_service = create_content_service(os.getenv("OPENAI_API_KEY"))
        
        # Mock input data
        vision_result = VisionAnalysisResult(
            product=ProductFeatures(
                name="iPhone 12 Pro",
                category="Smartphones",
                brand="Apple",
                condition="Sehr gut",
                features=["5G", "Pro Kamera", "128GB"]
            ),
            confidence_score=0.95,
            suggested_keywords=["iPhone", "Apple", "128GB", "Pro"],
            category_suggestions=["Handys"],
            condition_details="Sehr gut erhalten",
            estimated_value_range=(40000, 50000),
            marketing_highlights=["Top Zustand", "Beliebtes Modell"]
        )
        
        market_insights = EbayMarketInsights(
            search_term="iPhone 12 Pro",
            price_data=EbayPriceData(
                average_price=45000,
                median_price=44000,
                min_price=35000,
                max_price=55000,
                sold_count=50,
                active_listings=25,
                price_trend="stable",
                competitive_price=42000
            ),
            popular_keywords=["iPhone", "Pro", "Apple"],
            best_selling_conditions=["Sehr gut", "Neu"],
            seasonal_demand="normal",
            competition_level="medium",
            success_probability=0.85
        )
        
        start_time = time.time()
        content = await content_service.generate_listing_content(vision_result, market_insights)
        generation_time = time.time() - start_time
        
        print(f"✍️ Content generation: {generation_time:.2f}s")
        print(f"📝 Title length: {len(content.title)}")
        print(f"📋 Description length: {len(content.description)}")
        
        # Assertions
        assert generation_time < 10  # Content generation < 10s
        assert len(content.title) <= 80  # eBay limit
        assert len(content.description) > 50
        assert len(content.seo_keywords) > 0

# ========================================
# 🎯 RUN CONFIGURATION
# ========================================

if __name__ == "__main__":
    # Run tests with performance reporting
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--durations=10",
        "--capture=no"
    ])