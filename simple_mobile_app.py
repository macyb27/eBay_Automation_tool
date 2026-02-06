#!/usr/bin/env python3
"""
📱 Simple Mobile eBay Tool
Vision-only version for quick testing
"""

import os
import base64
import json
import re
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict, Any

import aiohttp
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn
import logging
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ========================================
# Listing Generation (Vision + Draft)
# ========================================

@dataclass
class ProductInfo:
    name: str
    category: str
    condition: str
    brand: Optional[str]
    features: List[str]

@dataclass
class ListingDraft:
    product: ProductInfo
    estimated_value_range: Tuple[int, int]
    suggested_keywords: List[str]
    condition_details: str
    confidence_score: float
    listing_title: str
    listing_description: str
    recommended_price: int
    shipping_suggestion: str
    source: str

class ListingGenerator:
    def __init__(self, api_key: Optional[str]):
        self.api_key = api_key
        self.base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    def is_live(self) -> bool:
        return bool(self.api_key)

    async def analyze_product_image(self, image_data: bytes, filename: Optional[str]) -> ListingDraft:
        if not self.api_key:
            return self._mock_result(filename, "Demo-Modus aktiv (kein OPENAI_API_KEY).")

        try:
            base64_image = base64.b64encode(image_data).decode("utf-8")
            response = await self._call_openai_vision(base64_image)
            data = self._parse_response(response)
            return self._build_result(data, source="openai")
        except Exception as exc:
            logger.warning("OpenAI analysis failed, using mock: %s", exc)
            return self._mock_result(filename, "OpenAI nicht erreichbar. Demo-Daten generiert.")

    async def _call_openai_vision(self, base64_image: str) -> Dict[str, Any]:
        prompt = (
            "Du bist ein Assistent zur Erstellung von eBay-Listings. "
            "Antworte ausschließlich mit validem JSON ohne Markdown.\n"
            "Schema:\n"
            "{\n"
            "  \"product_name\": \"\",\n"
            "  \"category\": \"\",\n"
            "  \"condition\": \"\",\n"
            "  \"brand\": \"\",\n"
            "  \"features\": [\"\"],\n"
            "  \"condition_details\": \"\",\n"
            "  \"estimated_value_eur\": {\"min\": 0, \"max\": 0},\n"
            "  \"confidence_score\": 0.0,\n"
            "  \"suggested_keywords\": [\"\"],\n"
            "  \"listing_title\": \"\",\n"
            "  \"listing_description\": \"\",\n"
            "  \"price_recommendation_eur\": 0,\n"
            "  \"shipping_suggestion\": \"\"\n"
            "}\n"
            "Regeln: listing_title max 80 Zeichen. "
            "listing_description als kurzer Absatz + Bullet-Liste, ohne HTML."
        )

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
            "max_tokens": 900,
            "temperature": 0.2
        }

        timeout = aiohttp.ClientTimeout(total=40)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise ValueError(f"OpenAI API error {response.status}: {error_text}")
                return await response.json()

    def _parse_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        try:
            content = response["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ValueError(f"Invalid OpenAI response: {exc}") from exc

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", content, re.S)
            if not match:
                raise ValueError("No JSON object found in response.")
            return json.loads(match.group(0))

    def _build_result(self, data: Dict[str, Any], source: str) -> ListingDraft:
        def to_int(value: Any, default: int) -> int:
            try:
                return int(float(value))
            except (TypeError, ValueError):
                return default

        def to_str_list(value: Any) -> List[str]:
            if isinstance(value, list):
                return [str(item).strip() for item in value if str(item).strip()]
            return []

        price_range = data.get("estimated_value_eur", {})
        min_val = max_val = 0
        if isinstance(price_range, dict):
            min_val = to_int(price_range.get("min"), 0)
            max_val = to_int(price_range.get("max"), min_val)
        elif isinstance(price_range, str):
            if "-" in price_range:
                parts = price_range.split("-", 1)
                min_val = to_int(parts[0], 0)
                max_val = to_int(parts[1], min_val)
            else:
                min_val = max_val = to_int(price_range, 0)
        elif isinstance(price_range, (int, float)):
            min_val = max_val = to_int(price_range, 0)

        if min_val <= 0:
            min_val = 20
        if max_val < min_val:
            max_val = min_val

        recommended_price = to_int(data.get("price_recommendation_eur"), 0)
        if recommended_price <= 0:
            recommended_price = int((min_val + max_val) / 2)

        product = ProductInfo(
            name=str(data.get("product_name") or "Unbekanntes Produkt"),
            category=str(data.get("category") or "Sonstiges"),
            condition=str(data.get("condition") or "Gebraucht"),
            brand=str(data.get("brand") or "") or None,
            features=to_str_list(data.get("features"))
        )

        listing_title = str(data.get("listing_title") or product.name).strip()
        listing_description = str(data.get("listing_description") or "").strip()
        if not listing_description:
            listing_description = (
                f"{product.name} in {product.condition}em Zustand.\n"
                f"- Kategorie: {product.category}\n"
                "- Versand nach Absprache\n"
            )

        return ListingDraft(
            product=product,
            estimated_value_range=(min_val * 100, max_val * 100),
            suggested_keywords=to_str_list(data.get("suggested_keywords")),
            condition_details=str(data.get("condition_details") or ""),
            confidence_score=float(data.get("confidence_score") or 0.6),
            listing_title=listing_title[:80],
            listing_description=listing_description,
            recommended_price=recommended_price * 100,
            shipping_suggestion=str(data.get("shipping_suggestion") or "Versand nach Absprache"),
            source=source
        )

    def _mock_result(self, filename: Optional[str], note: str) -> ListingDraft:
        product_name = "Produkt"
        if filename:
            product_name = filename.rsplit(".", 1)[0].replace("_", " ").strip() or product_name

        product = ProductInfo(
            name=product_name,
            category="Sonstiges",
            condition="Gebraucht",
            brand=None,
            features=["Funktionsfaehig", "Gepflegt", "Sofort einsatzbereit"]
        )

        min_val, max_val = 20, 35
        return ListingDraft(
            product=product,
            estimated_value_range=(min_val * 100, max_val * 100),
            suggested_keywords=["gebraucht", "top zustand", "schneller versand"],
            condition_details=note,
            confidence_score=0.4,
            listing_title=f"{product.name} - {product.condition}".strip()[:80],
            listing_description=(
                f"{product.name} in {product.condition}em Zustand.\n"
                "- Lieferung wie abgebildet\n"
                "- Privatverkauf, keine Garantie\n"
            ),
            recommended_price=int(((min_val + max_val) / 2) * 100),
            shipping_suggestion="DHL Paket oder Abholung",
            source="mock"
        )

# Initialize FastAPI
app = FastAPI(title="📱 Mobile eBay Tool", version="1.0.0")

# Initialize Listing Generator
listing_generator = ListingGenerator(api_key=os.getenv('OPENAI_API_KEY'))

@app.get("/", response_class=HTMLResponse)
async def mobile_app():
    """📱 Mobile-optimierte eBay Tool Interface"""

    if listing_generator.is_live():
        status_text = "✅ OpenAI Vision API aktiv"
        status_class = "status"
    else:
        status_text = "⚠️ Demo-Modus (kein OPENAI_API_KEY gesetzt)"
        status_class = "status warning"

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
        
        .status.warning {
            background: #f0ad4e;
            color: #222;
        }
        
        .result-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 10px;
        }
        
        .copy-btn {
            background: #f1f1f1;
            border: none;
            color: #333;
            padding: 6px 10px;
            border-radius: 8px;
            font-size: 12px;
            cursor: pointer;
        }
        
        .copy-btn:active {
            transform: scale(0.98);
        }
        
        .prewrap {
            white-space: pre-wrap;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 eBay Tool</h1>
            <p>Foto → AI-Analyse → eBay Ready</p>
        </div>
        
        <div class="__STATUS_CLASS__">
            __STATUS_TEXT__
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
                <div class="result-label">✅ Empfohlener Preis</div>
                <div class="result-value" id="recommendedPrice">-</div>
            </div>
            
            <div class="result-item">
                <div class="result-label">⭐ Zustand</div>
                <div class="result-value" id="condition">-</div>
            </div>

            <div class="result-item">
                <div class="result-header">
                    <div class="result-label">🏷️ Listing Titel</div>
                    <button class="copy-btn" onclick="copyText('listingTitle')">Kopieren</button>
                </div>
                <div class="result-value" id="listingTitle">-</div>
            </div>

            <div class="result-item">
                <div class="result-header">
                    <div class="result-label">📝 Listing Beschreibung</div>
                    <button class="copy-btn" onclick="copyText('listingDescription')">Kopieren</button>
                </div>
                <div class="result-value prewrap" id="listingDescription">-</div>
            </div>
            
            <div class="result-item">
                <div class="result-label">🔍 SEO Keywords</div>
                <div class="keywords" id="keywords"></div>
            </div>

            <div class="result-item">
                <div class="result-label">📦 Versand</div>
                <div class="result-value" id="shippingSuggestion">-</div>
            </div>
            
            <div class="result-item">
                <div class="result-label">📊 Details</div>
                <div class="result-value" id="details">-</div>
            </div>

            <div class="result-item">
                <div class="result-label">📈 Confidence</div>
                <div class="result-value" id="confidenceScore">-</div>
            </div>
        </div>
        
        <div class="footer">
            Powered by OpenAI GPT-4V • Made by Macyb
        </div>
    </div>

    <script>
        let currentImage = null;

        function copyText(elementId) {
            const element = document.getElementById(elementId);
            if (!element) return;
            const text = element.textContent || '';
            if (!text || text === '-') return;

            if (navigator.clipboard && window.isSecureContext) {
                navigator.clipboard.writeText(text);
            } else {
                const temp = document.createElement('textarea');
                temp.value = text;
                document.body.appendChild(temp);
                temp.select();
                document.execCommand('copy');
                document.body.removeChild(temp);
            }
        }
        
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
            document.getElementById('productName').textContent = data.product?.name || '-';
            document.getElementById('category').textContent = data.product?.category || '-';

            if (data.estimated_value_range && data.estimated_value_range.length >= 2) {
                document.getElementById('priceRange').textContent =
                    `€${(data.estimated_value_range[0]/100).toFixed(2)} - €${(data.estimated_value_range[1]/100).toFixed(2)}`;
            } else {
                document.getElementById('priceRange').textContent = '-';
            }

            if (data.recommended_price) {
                document.getElementById('recommendedPrice').textContent =
                    `€${(data.recommended_price/100).toFixed(2)}`;
            } else {
                document.getElementById('recommendedPrice').textContent = '-';
            }

            document.getElementById('condition').textContent = data.product?.condition || '-';
            document.getElementById('listingTitle').textContent = data.listing_title || '-';
            document.getElementById('listingDescription').textContent = data.listing_description || '-';
            document.getElementById('shippingSuggestion').textContent = data.shipping_suggestion || '-';
            document.getElementById('confidenceScore').textContent = data.confidence_score
                ? `${Math.round(data.confidence_score * 100)}%`
                : '-';

            const detailsParts = [];
            if (data.condition_details) {
                detailsParts.push(data.condition_details);
            }
            if (data.product?.features && data.product.features.length) {
                detailsParts.push(`Features: ${data.product.features.join(', ')}`);
            }
            document.getElementById('details').textContent = detailsParts.length
                ? detailsParts.join(' | ')
                : '-';
            
            // Keywords
            const keywordsDiv = document.getElementById('keywords');
            keywordsDiv.innerHTML = '';
            if (data.suggested_keywords && data.suggested_keywords.length) {
                data.suggested_keywords.forEach(keyword => {
                    const span = document.createElement('span');
                    span.className = 'keyword';
                    span.textContent = keyword;
                    keywordsDiv.appendChild(span);
                });
            }
            
            document.getElementById('results').style.display = 'block';
        }
    </script>
</body>
</html>
    """
    html_content = (
        html_content
        .replace("__STATUS_TEXT__", status_text)
        .replace("__STATUS_CLASS__", status_class)
    )

    return HTMLResponse(content=html_content)

@app.post("/analyze")
async def analyze_product(file: UploadFile = File(...)):
    """📸 Analysiere hochgeladenes Produktbild"""
    
    try:
        # Read image data
        image_data = await file.read()
        
        # Analyze and build listing draft
        logger.info(f"Analyzing image: {file.filename}, size: {len(image_data)} bytes")
        listing_result = await listing_generator.analyze_product_image(image_data, file.filename)
        
        # Prepare response
        response_data = {
            "product": {
                "name": listing_result.product.name,
                "category": listing_result.product.category,
                "condition": listing_result.product.condition,
                "brand": listing_result.product.brand,
                "features": listing_result.product.features
            },
            "estimated_value_range": listing_result.estimated_value_range,
            "suggested_keywords": listing_result.suggested_keywords,
            "condition_details": listing_result.condition_details,
            "confidence_score": listing_result.confidence_score,
            "listing_title": listing_result.listing_title,
            "listing_description": listing_result.listing_description,
            "recommended_price": listing_result.recommended_price,
            "shipping_suggestion": listing_result.shipping_suggestion,
            "source": listing_result.source
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
    mode = "openai" if listing_generator.is_live() else "mock"
    return {
        "status": "healthy",
        "service": "✅ Mobile eBay Tool ready",
        "vision": "✅ OpenAI Vision active" if mode == "openai" else "⚠️ Demo mode",
        "mode": mode
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