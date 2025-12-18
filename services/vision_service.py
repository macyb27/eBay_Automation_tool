"""
🔍 Vision Service - OpenAI GPT-4V Integration
Produkterkennung und -analyse aus Bildern
"""

import base64
import io
from typing import Dict, List, Optional
import aiohttp
import asyncio
from PIL import Image
from pydantic import BaseModel
import json
import logging

logger = logging.getLogger(__name__)

class ProductFeatures(BaseModel):
    """Erkannte Produktmerkmale"""
    name: str
    category: str
    brand: Optional[str] = None
    condition: str = "Gebraucht"
    color: Optional[str] = None
    size: Optional[str] = None
    material: Optional[str] = None
    features: List[str] = []
    estimated_age: Optional[str] = None
    defects: List[str] = []

class VisionAnalysisResult(BaseModel):
    """Vollständiges Analyse-Ergebnis"""
    product: ProductFeatures
    confidence_score: float
    suggested_keywords: List[str]
    category_suggestions: List[str]
    condition_details: str
    estimated_value_range: tuple[int, int]  # Min, Max in cents
    marketing_highlights: List[str]

class OpenAIVisionService:
    """OpenAI GPT-4V Service für Produktanalyse"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.openai.com/v1"
        self.model = "gpt-4o"  # Latest vision model
        
    async def analyze_product_image(self, image_data: bytes) -> VisionAnalysisResult:
        """
        Analysiert Produktbild und extrahiert alle relevanten Informationen
        """
        try:
            # Bild für API vorbereiten
            base64_image = await self._prepare_image(image_data)
            
            # Vision API Call
            analysis_prompt = self._create_analysis_prompt()
            response = await self._call_openai_vision(base64_image, analysis_prompt)
            
            # Response parsen und strukturieren
            result = self._parse_analysis_response(response)
            
            logger.info(f"Product analysis completed: {result.product.name}")
            return result
            
        except Exception as e:
            logger.error(f"Vision analysis failed: {e}")
            raise

    async def _prepare_image(self, image_data: bytes) -> str:
        """Bild optimieren und zu Base64 konvertieren"""
        
        # Bild laden und optimieren
        image = Image.open(io.BytesIO(image_data))
        
        # Größe optimieren (max 1024x1024 für beste API Performance)
        if image.width > 1024 or image.height > 1024:
            image.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
        
        # Als JPEG speichern für kleinere Dateigröße
        buffer = io.BytesIO()
        if image.mode in ("RGBA", "P"):
            image = image.convert("RGB")
        
        image.save(buffer, format="JPEG", quality=85, optimize=True)
        buffer.seek(0)
        
        # Base64 encoding
        return base64.b64encode(buffer.getvalue()).decode()

    def _create_analysis_prompt(self) -> str:
        """Erstellt optimierten Prompt für Produktanalyse"""
        
        return """
Du bist ein Experte für eBay-Verkäufe und Produktbewertung. Analysiere dieses Produktbild detailliert für eine eBay-Auktion.

WICHTIG: Antworte NUR mit einem gültigen JSON-Objekt in genau diesem Format:

{
  "product": {
    "name": "Genauer Produktname (Marke + Modell wenn erkennbar)",
    "category": "eBay-Kategorie (z.B. Handy & Telefon, Kleidung & Accessoires)",
    "brand": "Markenname oder null",
    "condition": "Neu|Sehr gut|Gut|Gebraucht|Defekt",
    "color": "Hauptfarbe des Produkts",
    "size": "Größe falls relevant (Kleidung, Schuhe)",
    "material": "Material falls erkennbar",
    "features": ["Feature 1", "Feature 2", "Feature 3"],
    "estimated_age": "Geschätztes Alter (z.B. '2-3 Jahre alt', 'Neuwertig')",
    "defects": ["Sichtbare Mängel oder Gebrauchsspuren"]
  },
  "confidence_score": 0.95,
  "suggested_keywords": ["Keyword1", "Keyword2", "Keyword3"],
  "category_suggestions": ["Hauptkategorie", "Alternative Kategorie"],
  "condition_details": "Detaillierte Zustandsbeschreibung für eBay",
  "estimated_value_range": [2000, 5000],
  "marketing_highlights": ["Verkaufsargument 1", "Verkaufsargument 2"]
}

ANALYSE-FOKUS:
- Produktidentifikation: Marke, Modell, genaue Bezeichnung
- Zustandsbewertung: Gebrauchsspuren, Kratzer, Vollständigkeit
- Marktrelevanz: Beliebte Suchbegriffe, Verkaufsargumente
- Preiseinschätzung: Realistische Preisspanne in EUR-Cent
- eBay-Optimierung: Keywords für maximale Sichtbarkeit

DEUTSCHE MARKT-SPEZIFIKA:
- Deutsche Produktnamen und Begriffe verwenden
- eBay.de Kategorien berücksichtigen
- Deutsche Größen/Standards (EU-Größen, etc.)
- Lokale Marken und Präferenzen einbeziehen
"""

    async def _call_openai_vision(self, base64_image: str, prompt: str) -> Dict:
        """OpenAI Vision API Call mit Retry-Logic"""
        
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
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}",
                                "detail": "high"  # Für bessere Analyse-Qualität
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 2000,
            "temperature": 0.1,  # Niedrig für konsistente Ergebnisse
            "response_format": {"type": "json_object"}
        }
        
        # Retry-Logic für API Calls
        for attempt in range(3):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{self.base_url}/chat/completions",
                        headers=headers,
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=60)
                    ) as response:
                        
                        if response.status == 200:
                            result = await response.json()
                            return result
                        
                        elif response.status == 429:  # Rate limit
                            wait_time = 2 ** attempt
                            logger.warning(f"Rate limit hit, waiting {wait_time}s...")
                            await asyncio.sleep(wait_time)
                            
                        else:
                            error_text = await response.text()
                            logger.error(f"OpenAI API error {response.status}: {error_text}")
                            
            except Exception as e:
                logger.error(f"API call attempt {attempt + 1} failed: {e}")
                if attempt == 2:  # Last attempt
                    raise
                await asyncio.sleep(1)

    def _parse_analysis_response(self, response: Dict) -> VisionAnalysisResult:
        """OpenAI Response zu strukturiertem Ergebnis parsen"""
        
        try:
            content = response["choices"][0]["message"]["content"]
            analysis_data = json.loads(content)
            
            # Pydantic Validation und Parsing
            return VisionAnalysisResult(
                product=ProductFeatures(**analysis_data["product"]),
                confidence_score=analysis_data.get("confidence_score", 0.8),
                suggested_keywords=analysis_data.get("suggested_keywords", []),
                category_suggestions=analysis_data.get("category_suggestions", []),
                condition_details=analysis_data.get("condition_details", ""),
                estimated_value_range=tuple(analysis_data.get("estimated_value_range", [1000, 3000])),
                marketing_highlights=analysis_data.get("marketing_highlights", [])
            )
            
        except Exception as e:
            logger.error(f"Failed to parse analysis response: {e}")
            logger.debug(f"Response content: {response}")
            
            # Fallback mit Default-Werten
            return VisionAnalysisResult(
                product=ProductFeatures(
                    name="Unbekanntes Produkt",
                    category="Sonstige",
                    condition="Gebraucht"
                ),
                confidence_score=0.1,
                suggested_keywords=["gebraucht", "verkauf"],
                category_suggestions=["Sonstige"],
                condition_details="Produkt konnte nicht vollständig analysiert werden",
                estimated_value_range=(500, 2000),
                marketing_highlights=["Günstiger Preis"]
            )

class MockVisionService:
    """Mock Service für Development/Testing"""
    
    async def analyze_product_image(self, image_data: bytes) -> VisionAnalysisResult:
        """Simuliert Vision-Analyse für Testing"""
        
        await asyncio.sleep(2)  # Simuliere API-Latenz
        
        return VisionAnalysisResult(
            product=ProductFeatures(
                name="Apple iPhone 12 Pro 128GB",
                category="Handy & Telefon > Smartphones",
                brand="Apple",
                condition="Sehr gut",
                color="Space Grau",
                size="128GB",
                features=[
                    "6.1 Zoll Super Retina XDR Display",
                    "A14 Bionic Chip",
                    "Pro Kamera-System",
                    "5G fähig",
                    "MagSafe kompatibel"
                ],
                estimated_age="2-3 Jahre alt",
                defects=["Leichte Gebrauchsspuren am Rahmen"]
            ),
            confidence_score=0.92,
            suggested_keywords=[
                "iPhone 12 Pro", "Apple", "128GB", "Space Grau", 
                "5G", "unlocked", "ohne Vertrag", "ProMax"
            ],
            category_suggestions=[
                "Handy & Telefon > Smartphones",
                "Handy & Telefon > Apple iPhone"
            ],
            condition_details="Sehr gut erhaltenes iPhone 12 Pro. Display einwandfrei, keine Risse. Leichte Gebrauchsspuren am Metallrahmen, typisch für normalen Gebrauch. Akku-Gesundheit geschätzt 85-90%.",
            estimated_value_range=(45000, 55000),  # 450-550 EUR in Cent
            marketing_highlights=[
                "Beliebtes iPhone 12 Pro Modell",
                "128GB Speicher - perfekt für den täglichen Gebrauch",
                "5G-fähig für schnelle Internetverbindung",
                "Premium Pro Kamera-System",
                "Sehr guter Zustand"
            ]
        )

# Factory Function für Service-Erstellung
def create_vision_service(api_key: Optional[str] = None) -> OpenAIVisionService | MockVisionService:
    """Erstellt Vision Service basierend auf verfügbarem API Key"""
    
    if api_key:
        return OpenAIVisionService(api_key)
    else:
        logger.warning("No OpenAI API key provided, using mock service")
        return MockVisionService()

# Usage Example:
"""
# In main.py:
from services.vision_service import create_vision_service

vision_service = create_vision_service(os.getenv("OPENAI_API_KEY"))

@app.post("/analyze-product")
async def analyze_product(file: UploadFile = File(...)):
    image_data = await file.read()
    result = await vision_service.analyze_product_image(image_data)
    return result.dict()
"""