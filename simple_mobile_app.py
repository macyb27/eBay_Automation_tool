#!/usr/bin/env python3
"""
📱 Simple Mobile eBay Tool
Vision-only version for quick testing
"""

import os
import asyncio
import sys
import aiohttp
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn
import logging

# Add services to path
sys.path.append('/home/user/ebay_automation_tool')
from services.vision_service import OpenAIVisionService
from dotenv import load_dotenv

# Load environment
load_dotenv('/home/user/ebay_automation_tool/.env')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(title="📱 Mobile eBay Tool", version="1.0.0")

# Initialize Vision Service
vision_service = OpenAIVisionService(api_key=os.getenv('OPENAI_API_KEY'))

@app.get("/", response_class=HTMLResponse)
async def mobile_app():
    """📱 Mobile-optimierte eBay Tool Interface"""
    
    html_content = """
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>📱 eBay Automation Tool</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 10px;
        }
        
        .container {
            max-width: 400px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            padding: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }
        
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        
        .header h1 {
            font-size: 24px;
            color: #333;
            margin-bottom: 5px;
        }
        
        .header p {
            color: #666;
            font-size: 14px;
        }
        
        .upload-area {
            border: 3px dashed #667eea;
            border-radius: 15px;
            padding: 40px 20px;
            text-align: center;
            margin-bottom: 20px;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .upload-area:hover {
            background: #f8f9ff;
            border-color: #764ba2;
        }
        
        .upload-icon {
            font-size: 48px;
            margin-bottom: 15px;
        }
        
        .upload-text {
            color: #333;
            font-size: 16px;
            margin-bottom: 10px;
        }
        
        .upload-subtext {
            color: #666;
            font-size: 12px;
        }
        
        input[type="file"] {
            display: none;
        }
        
        .preview {
            display: none;
            margin-bottom: 20px;
        }
        
        .preview img {
            width: 100%;
            max-height: 200px;
            object-fit: cover;
            border-radius: 10px;
        }
        
        .analyze-btn {
            width: 100%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 15px;
            border-radius: 10px;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            transition: transform 0.2s ease;
            margin-bottom: 20px;
        }
        
        .analyze-btn:hover {
            transform: translateY(-2px);
        }
        
        .analyze-btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        
        .loading {
            display: none;
            text-align: center;
            padding: 20px;
        }
        
        .spinner {
            width: 40px;
            height: 40px;
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto 15px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .results {
            display: none;
            background: #f8f9fa;
            border-radius: 10px;
            padding: 20px;
            margin-top: 20px;
        }
        
        .result-item {
            margin-bottom: 15px;
            padding-bottom: 15px;
            border-bottom: 1px solid #eee;
        }
        
        .result-item:last-child {
            border-bottom: none;
            margin-bottom: 0;
            padding-bottom: 0;
        }
        
        .result-label {
            font-weight: bold;
            color: #333;
            font-size: 14px;
            margin-bottom: 5px;
        }
        
        .result-value {
            color: #666;
            font-size: 16px;
            line-height: 1.4;
        }
        
        .price-range {
            color: #27AE60;
            font-weight: bold;
            font-size: 18px;
        }
        
        .keywords {
            display: flex;
            flex-wrap: wrap;
            gap: 5px;
            margin-top: 5px;
        }
        
        .keyword {
            background: #667eea;
            color: white;
            padding: 4px 8px;
            border-radius: 15px;
            font-size: 12px;
        }
        
        .error {
            background: #ff6b6b;
            color: white;
            padding: 15px;
            border-radius: 10px;
            margin-top: 20px;
            display: none;
        }
        
        .footer {
            text-align: center;
            margin-top: 30px;
            color: #666;
            font-size: 12px;
        }
        
        .status {
            background: #28a745;
            color: white;
            padding: 10px;
            border-radius: 10px;
            margin-bottom: 20px;
            text-align: center;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 eBay Tool</h1>
            <p>Foto → AI-Analyse → eBay Ready</p>
        </div>
        
        <div class="status">
            ✅ OpenAI Vision API aktiv
        </div>
        
        <div class="upload-area" onclick="document.getElementById('fileInput').click()">
            <div class="upload-icon">📷</div>
            <div class="upload-text">Produktfoto aufnehmen</div>
            <div class="upload-subtext">oder aus Galerie wählen</div>
        </div>
        
        <input type="file" id="fileInput" accept="image/*" capture="environment">
        
        <div class="preview" id="preview">
            <img id="previewImage" src="" alt="Preview">
        </div>
        
        <button class="analyze-btn" id="analyzeBtn" onclick="analyzeProduct()" disabled>
            🤖 Mit AI analysieren
        </button>
        
        <div class="loading" id="loading">
            <div class="spinner"></div>
            <div>AI analysiert dein Produkt...</div>
        </div>
        
        <div class="error" id="error"></div>
        
        <div class="results" id="results">
            <div class="result-item">
                <div class="result-label">📦 Produkt</div>
                <div class="result-value" id="productName">-</div>
            </div>
            
            <div class="result-item">
                <div class="result-label">🏷️ Kategorie</div>
                <div class="result-value" id="category">-</div>
            </div>
            
            <div class="result-item">
                <div class="result-label">💰 Geschätzter Preis</div>
                <div class="result-value price-range" id="priceRange">-</div>
            </div>
            
            <div class="result-item">
                <div class="result-label">⭐ Zustand</div>
                <div class="result-value" id="condition">-</div>
            </div>
            
            <div class="result-item">
                <div class="result-label">🔍 SEO Keywords</div>
                <div class="keywords" id="keywords"></div>
            </div>
            
            <div class="result-item">
                <div class="result-label">📊 Details</div>
                <div class="result-value" id="details">-</div>
            </div>
        </div>
        
        <div class="footer">
            Powered by OpenAI GPT-4V • Made by Macyb
        </div>
    </div>

    <script>
        let currentImage = null;
        
        // File input handler
        document.getElementById('fileInput').addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    currentImage = file;
                    document.getElementById('previewImage').src = e.target.result;
                    document.getElementById('preview').style.display = 'block';
                    document.getElementById('analyzeBtn').disabled = false;
                };
                reader.readAsDataURL(file);
            }
        });
        
        // Analyze function
        async function analyzeProduct() {
            if (!currentImage) return;
            
            // Show loading
            document.getElementById('loading').style.display = 'block';
            document.getElementById('results').style.display = 'none';
            document.getElementById('error').style.display = 'none';
            document.getElementById('analyzeBtn').disabled = true;
            
            try {
                const formData = new FormData();
                formData.append('file', currentImage);
                
                const response = await fetch('/analyze', {
                    method: 'POST',
                    body: formData
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                
                const result = await response.json();
                
                // Hide loading
                document.getElementById('loading').style.display = 'none';
                
                if (result.success) {
                    displayResults(result.data);
                } else {
                    throw new Error(result.error || 'Unbekannter Fehler');
                }
                
            } catch (error) {
                console.error('Error:', error);
                document.getElementById('loading').style.display = 'none';
                document.getElementById('error').textContent = `Fehler: ${error.message}`;
                document.getElementById('error').style.display = 'block';
            }
            
            document.getElementById('analyzeBtn').disabled = false;
        }
        
        function displayResults(data) {
            document.getElementById('productName').textContent = data.product.name;
            document.getElementById('category').textContent = data.product.category;
            document.getElementById('priceRange').textContent = 
                `€${(data.estimated_value_range[0]/100).toFixed(2)} - €${(data.estimated_value_range[1]/100).toFixed(2)}`;
            document.getElementById('condition').textContent = data.product.condition;
            document.getElementById('details').textContent = data.condition_details;
            
            // Keywords
            const keywordsDiv = document.getElementById('keywords');
            keywordsDiv.innerHTML = '';
            data.suggested_keywords.forEach(keyword => {
                const span = document.createElement('span');
                span.className = 'keyword';
                span.textContent = keyword;
                keywordsDiv.appendChild(span);
            });
            
            document.getElementById('results').style.display = 'block';
        }
    </script>
</body>
</html>
    """
    
    return HTMLResponse(content=html_content)

@app.post("/analyze")
async def analyze_product(file: UploadFile = File(...)):
    """📸 Analysiere hochgeladenes Produktbild"""
    
    try:
        # Read image data
        image_data = await file.read()
        
        # Analyze with Vision Service
        logger.info(f"Analyzing image: {file.filename}, size: {len(image_data)} bytes")
        vision_result = await vision_service.analyze_product_image(image_data)
        
        # Prepare response
        response_data = {
            "product": {
                "name": vision_result.product.name,
                "category": vision_result.product.category,
                "condition": vision_result.product.condition,
                "brand": vision_result.product.brand,
                "features": vision_result.product.features
            },
            "estimated_value_range": vision_result.estimated_value_range,
            "suggested_keywords": vision_result.suggested_keywords,
            "condition_details": vision_result.condition_details,
            "confidence_score": vision_result.confidence_score
        }
        
        return JSONResponse({
            "success": True,
            "data": response_data
        })
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)

@app.get("/health")
async def health_check():
    """🔍 System Health Check"""
    return {
        "status": "healthy",
        "service": "✅ Mobile eBay Tool ready",
        "vision": "✅ OpenAI Vision active"
    }

if __name__ == "__main__":
    print("📱 **Mobile eBay Tool wird gestartet...**")
    print("🌐 **Zugriff über dein Handy möglich!**")
    print("✅ **OpenAI Vision API aktiv**")
    
    # Start server with network access
    uvicorn.run(
        app, 
        host="0.0.0.0",  # Allow access from any device
        port=8000, 
        log_level="info"
    )