"""
📝 Content Generation Service - AI-Powered eBay Descriptions
SEO-optimierte, verkaufsfördernde Beschreibungen automatisch generieren
"""

import asyncio
import aiohttp
import json
from typing import Dict, List, Optional
from pydantic import BaseModel
import logging
from datetime import datetime

from .vision_service import VisionAnalysisResult
from .ebay_service import EbayMarketInsights

logger = logging.getLogger(__name__)

class ListingContent(BaseModel):
    """Generierter Listing-Content"""
    title: str
    description: str
    subtitle: Optional[str] = None
    bullet_points: List[str]
    seo_keywords: List[str]
    hashtags: List[str]
    condition_description: str
    shipping_description: str
    return_policy: str

class ContentOptimization(BaseModel):
    """Content-Optimierung Metriken"""
    seo_score: float
    readability_score: float
    conversion_potential: float
    keyword_density: Dict[str, float]
    recommendations: List[str]

class AIContentService:
    """AI-powered Content Generation Service"""
    
    def __init__(self, openai_api_key: str):
        self.api_key = openai_api_key
        self.base_url = "https://api.openai.com/v1"
        
        # Deutsche eBay-spezifische Templates
        self.templates = {
            "title_patterns": [
                "{brand} {model} {condition} {key_features}",
                "{product_name} - {condition} - {unique_selling_point}",
                "{brand} {model} | {size} | {color} | {condition}"
            ],
            "description_structure": {
                "opening": "Verkaufe hier mein/meine {product_type}:",
                "highlights": "✅ Highlights:",
                "condition": "🔍 Zustand:",
                "shipping": "📦 Versand:",
                "payment": "💳 Bezahlung:",
                "closing": "Bei Fragen gerne melden! 😊"
            }
        }

    async def generate_listing_content(
        self,
        vision_result: VisionAnalysisResult,
        market_insights: EbayMarketInsights,
        user_preferences: Dict = None
    ) -> ListingContent:
        """
        Generiert kompletten Listing-Content basierend auf Analyse-Ergebnissen
        """
        try:
            # Content-Prompt erstellen
            prompt = self._create_content_prompt(vision_result, market_insights, user_preferences)
            
            # OpenAI API Call
            response = await self._call_openai_gpt(prompt)
            
            # Response parsen
            content = self._parse_content_response(response, vision_result, market_insights)
            
            logger.info(f"Content generated for: {vision_result.product.name}")
            return content
            
        except Exception as e:
            logger.error(f"Content generation failed: {e}")
            raise

    def _create_content_prompt(
        self,
        vision_result: VisionAnalysisResult,
        market_insights: EbayMarketInsights,
        user_preferences: Dict = None
    ) -> str:
        """Erstellt optimierten Prompt für Content-Generierung"""
        
        product = vision_result.product
        market = market_insights.price_data
        
        return f"""
Du bist ein Experte für eBay-Verkäufe und erstellst hochkonvertierende Auktionsbeschreibungen für deutsche Käufer.

PRODUKTINFORMATIONEN:
- Produktname: {product.name}
- Kategorie: {product.category}
- Marke: {product.brand}
- Zustand: {product.condition}
- Farbe: {product.color}
- Features: {', '.join(product.features)}
- Geschätztes Alter: {product.estimated_age}
- Mängel: {', '.join(product.defects) if product.defects else 'Keine sichtbaren Mängel'}

MARKTDATEN:
- Durchschnittspreis: {market.average_price/100:.2f}€
- Empfohlener Preis: {market.competitive_price/100:.2f}€
- Beliebte Keywords: {', '.join(market_insights.popular_keywords[:5])}
- Konkurrenzniveau: {market_insights.competition_level}
- Erfolgschance: {market_insights.success_probability:.0%}

MARKETING-HIGHLIGHTS:
{chr(10).join(f'- {highlight}' for highlight in vision_result.marketing_highlights)}

AUFGABE:
Erstelle eine verkaufsstarke eBay-Auktion auf Deutsch. Antworte NUR mit einem gültigen JSON-Objekt:

{{
  "title": "Optimierter eBay-Titel (max 80 Zeichen, keyword-reich)",
  "subtitle": "Zusätzliche Verkaufsargumente (optional, max 55 Zeichen)",
  "description": "Vollständige HTML-Beschreibung mit Struktur, Emojis und Verkaufsargumenten",
  "bullet_points": ["Bullet Point 1", "Bullet Point 2", "Bullet Point 3"],
  "seo_keywords": ["keyword1", "keyword2", "keyword3"],
  "hashtags": ["#hashtag1", "#hashtag2", "#hashtag3"],
  "condition_description": "Detaillierte Zustandsbeschreibung für Käufer",
  "shipping_description": "Versandinfo (DHL, Hermes, etc.)",
  "return_policy": "Rückgaberegelung nach deutschem Recht"
}}

WICHTIGE REGELN:
1. TITEL: Max 80 Zeichen, wichtigste Keywords zuerst, keine überflüssigen Wörter
2. BESCHREIBUNG: Strukturiert mit Emojis, Verkaufsargumenten, ehrlich über Mängel
3. DEUTSCH: Perfektes Deutsch, eBay.de-typische Sprache
4. SEO: Top-Keywords aus Marktanalyse verwenden
5. VERTRAUEN: Seriös, detailliert, transparent über Zustand
6. VERKAUFSFÖRDERND: Emotionale Trigger, Dringlichkeit, Mehrwert kommunizieren

STIL: Freundlich, kompetent, vertrauenswürdig - wie ein erfahrener eBay-Verkäufer.
"""

    async def _call_openai_gpt(self, prompt: str) -> Dict:
        """OpenAI GPT API Call für Content-Generierung"""
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "gpt-4o",
            "messages": [
                {
                    "role": "system",
                    "content": "Du bist ein Experte für eBay-Verkäufe in Deutschland. Du erstellst immer verkaufsstarke, SEO-optimierte Auktionsbeschreibungen in perfektem Deutsch."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 3000,
            "temperature": 0.7,  # Kreativ aber konsistent
            "response_format": {"type": "json_object"}
        }
        
        # Retry-Logic
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
                            return await response.json()
                        
                        elif response.status == 429:
                            wait_time = 2 ** attempt
                            logger.warning(f"Rate limit, waiting {wait_time}s...")
                            await asyncio.sleep(wait_time)
                        
                        else:
                            error_text = await response.text()
                            logger.error(f"OpenAI API error {response.status}: {error_text}")
                            
            except Exception as e:
                logger.error(f"API call attempt {attempt + 1} failed: {e}")
                if attempt == 2:
                    raise
                await asyncio.sleep(1)

    def _parse_content_response(
        self,
        response: Dict,
        vision_result: VisionAnalysisResult,
        market_insights: EbayMarketInsights
    ) -> ListingContent:
        """OpenAI Response zu strukturiertem Content parsen"""
        
        try:
            content = response["choices"][0]["message"]["content"]
            content_data = json.loads(content)
            
            return ListingContent(
                title=content_data.get("title", f"{vision_result.product.name} - {vision_result.product.condition}"),
                description=content_data.get("description", "Keine Beschreibung verfügbar"),
                subtitle=content_data.get("subtitle"),
                bullet_points=content_data.get("bullet_points", []),
                seo_keywords=content_data.get("seo_keywords", []),
                hashtags=content_data.get("hashtags", []),
                condition_description=content_data.get("condition_description", vision_result.condition_details),
                shipping_description=content_data.get("shipping_description", "Versand mit DHL oder Hermes möglich"),
                return_policy=content_data.get("return_policy", "14 Tage Rückgaberecht nach deutschem Recht")
            )
            
        except Exception as e:
            logger.error(f"Failed to parse content response: {e}")
            
            # Fallback Content generieren
            return self._generate_fallback_content(vision_result, market_insights)

    def _generate_fallback_content(
        self,
        vision_result: VisionAnalysisResult,
        market_insights: EbayMarketInsights
    ) -> ListingContent:
        """Fallback Content wenn AI-Generierung fehlschlägt"""
        
        product = vision_result.product
        
        # Basic Title
        title_parts = [product.brand, product.name, product.condition]
        title = " ".join(filter(None, title_parts))[:80]
        
        # Basic Description Template
        description = f"""
<div style="font-family: Arial, sans-serif; max-width: 800px;">
    <h2>🔥 {product.name}</h2>
    
    <h3>📋 Produktdetails:</h3>
    <ul>
        <li><strong>Marke:</strong> {product.brand or 'Siehe Fotos'}</li>
        <li><strong>Zustand:</strong> {product.condition}</li>
        <li><strong>Farbe:</strong> {product.color or 'Siehe Fotos'}</li>
    </ul>
    
    <h3>🔍 Zustand:</h3>
    <p>{vision_result.condition_details}</p>
    
    <h3>📦 Versand:</h3>
    <p>Schneller und sicherer Versand mit DHL oder Hermes.</p>
    
    <h3>💬 Kontakt:</h3>
    <p>Bei Fragen gerne melden! 😊</p>
</div>
        """.strip()
        
        return ListingContent(
            title=title,
            description=description,
            bullet_points=[
                f"Zustand: {product.condition}",
                f"Marke: {product.brand}" if product.brand else "Siehe Beschreibung",
                "Schneller Versand"
            ],
            seo_keywords=market_insights.popular_keywords[:5],
            hashtags=[f"#{product.brand.lower()}" if product.brand else "#gebraucht"],
            condition_description=vision_result.condition_details,
            shipping_description="Versand mit DHL oder Hermes, gut verpackt",
            return_policy="14 Tage Rückgaberecht gemäß gesetzlichen Bestimmungen"
        )

    async def optimize_content(self, content: ListingContent) -> ContentOptimization:
        """Analysiert und optimiert den generierten Content"""
        
        # SEO Score berechnen
        seo_score = self._calculate_seo_score(content)
        
        # Readability Score
        readability_score = self._calculate_readability_score(content.description)
        
        # Conversion Potential
        conversion_potential = self._estimate_conversion_potential(content)
        
        # Keyword Density
        keyword_density = self._analyze_keyword_density(content)
        
        # Recommendations generieren
        recommendations = self._generate_recommendations(content, seo_score, readability_score)
        
        return ContentOptimization(
            seo_score=seo_score,
            readability_score=readability_score,
            conversion_potential=conversion_potential,
            keyword_density=keyword_density,
            recommendations=recommendations
        )

    def _calculate_seo_score(self, content: ListingContent) -> float:
        """SEO Score basierend auf eBay Best Practices"""
        
        score = 0.0
        max_score = 10.0
        
        # Title Length (optimal 50-80 Zeichen)
        title_len = len(content.title)
        if 50 <= title_len <= 80:
            score += 2.0
        elif title_len < 50:
            score += 1.0
        
        # Keywords in Title
        keywords_in_title = sum(1 for keyword in content.seo_keywords if keyword.lower() in content.title.lower())
        score += min(2.0, keywords_in_title * 0.5)
        
        # Description Length
        desc_len = len(content.description)
        if desc_len > 500:
            score += 2.0
        elif desc_len > 200:
            score += 1.0
        
        # Bullet Points
        if len(content.bullet_points) >= 3:
            score += 1.5
        
        # Structured Description (HTML tags)
        if any(tag in content.description for tag in ['<h', '<ul>', '<li>', '<strong>']):
            score += 1.5
        
        # Keywords in Description
        keywords_in_desc = sum(1 for keyword in content.seo_keywords if keyword.lower() in content.description.lower())
        score += min(1.0, keywords_in_desc * 0.2)
        
        return min(10.0, score)

    def _calculate_readability_score(self, text: str) -> float:
        """Vereinfachter Readability Score für deutschen Text"""
        
        # HTML Tags entfernen für Analyse
        import re
        clean_text = re.sub('<[^<]+?>', '', text)
        
        sentences = len([s for s in clean_text.split('.') if s.strip()])
        words = len(clean_text.split())
        
        if sentences == 0 or words == 0:
            return 5.0
        
        avg_sentence_length = words / sentences
        
        # Optimal: 10-20 Wörter pro Satz
        if 10 <= avg_sentence_length <= 20:
            readability = 10.0
        elif avg_sentence_length < 10:
            readability = 7.0 + (avg_sentence_length / 10) * 3
        else:
            readability = max(1.0, 10.0 - (avg_sentence_length - 20) * 0.2)
        
        return min(10.0, readability)

    def _estimate_conversion_potential(self, content: ListingContent) -> float:
        """Schätzt Conversion-Potenzial basierend auf Content-Qualität"""
        
        score = 5.0  # Baseline
        
        # Positive Faktoren
        conversion_keywords = [
            'neu', 'neuwertig', 'original', 'garantie', 'rechnung', 'ovp',
            'schnell', 'sofort', 'express', 'kostenlos', 'gratis'
        ]
        
        trust_signals = [
            'privatverkauf', 'nichtraucher', 'tierfreier', 'paypal', 'überweisung'
        ]
        
        full_text = (content.title + ' ' + content.description + ' ' + 
                    ' '.join(content.bullet_points)).lower()
        
        # Conversion Keywords
        conversion_matches = sum(1 for keyword in conversion_keywords if keyword in full_text)
        score += min(2.0, conversion_matches * 0.3)
        
        # Trust Signals
        trust_matches = sum(1 for signal in trust_signals if signal in full_text)
        score += min(1.5, trust_matches * 0.3)
        
        # Emoticons/Emojis (Vertrauen schaffen)
        emoji_count = len([char for char in full_text if char in '😊🔥📦💯✅'])
        score += min(1.0, emoji_count * 0.2)
        
        # Strukturierte Beschreibung
        if '<h' in content.description and '<li>' in content.description:
            score += 0.5
        
        return min(10.0, score)

    def _analyze_keyword_density(self, content: ListingContent) -> Dict[str, float]:
        """Analysiert Keyword-Dichte im Content"""
        
        full_text = (content.title + ' ' + content.description).lower()
        words = full_text.split()
        total_words = len(words)
        
        if total_words == 0:
            return {}
        
        keyword_density = {}
        for keyword in content.seo_keywords:
            keyword_count = full_text.count(keyword.lower())
            density = (keyword_count / total_words) * 100
            keyword_density[keyword] = round(density, 2)
        
        return keyword_density

    def _generate_recommendations(
        self,
        content: ListingContent,
        seo_score: float,
        readability_score: float
    ) -> List[str]:
        """Generiert Verbesserungsvorschläge"""
        
        recommendations = []
        
        # SEO Verbesserungen
        if seo_score < 7.0:
            if len(content.title) < 50:
                recommendations.append("Titel verlängern - nutze mehr relevante Keywords")
            
            if len(content.bullet_points) < 3:
                recommendations.append("Mehr Bullet Points hinzufügen für bessere Struktur")
            
            if not any(tag in content.description for tag in ['<h', '<ul>', '<li>']):
                recommendations.append("HTML-Struktur in Beschreibung verwenden (Überschriften, Listen)")
        
        # Readability Verbesserungen
        if readability_score < 6.0:
            recommendations.append("Kürzere Sätze verwenden für bessere Lesbarkeit")
            recommendations.append("Absätze einfügen für übersichtlichere Struktur")
        
        # Content Verbesserungen
        if 'garantie' not in content.description.lower():
            recommendations.append("Garantie-Information hinzufügen falls vorhanden")
        
        if 'versand' not in content.description.lower():
            recommendations.append("Detaillierte Versandinfos ergänzen")
        
        return recommendations[:5]  # Max 5 Recommendations


class MockContentService:
    """Mock Service für Development ohne OpenAI API"""
    
    async def generate_listing_content(
        self,
        vision_result: VisionAnalysisResult,
        market_insights: EbayMarketInsights,
        user_preferences: Dict = None
    ) -> ListingContent:
        """Mock Content-Generierung für Testing"""
        
        await asyncio.sleep(2)  # Simuliere API-Latenz
        
        product = vision_result.product
        
        return ListingContent(
            title=f"{product.brand} {product.name} - {product.condition} - Top Zustand!",
            subtitle="Schneller Versand ✅ PayPal ✅ Privatverkauf",
            description=f"""
<div style="font-family: Arial, sans-serif; max-width: 800px;">
    <h2>🔥 {product.name}</h2>
    
    <h3>📋 Produktdetails:</h3>
    <ul>
        <li><strong>Marke:</strong> {product.brand}</li>
        <li><strong>Modell:</strong> {product.name}</li>
        <li><strong>Zustand:</strong> {product.condition}</li>
        <li><strong>Farbe:</strong> {product.color}</li>
    </ul>
    
    <h3>✅ Highlights:</h3>
    <ul>
        {chr(10).join(f'<li>{feature}</li>' for feature in product.features)}
    </ul>
    
    <h3>🔍 Zustand:</h3>
    <p>{vision_result.condition_details}</p>
    
    <h3>📦 Versand & Bezahlung:</h3>
    <ul>
        <li>Schneller Versand mit DHL (4,99€)</li>
        <li>PayPal, Überweisung möglich</li>
        <li>Gut verpackt und versichert</li>
    </ul>
    
    <h3>💬 Kontakt:</h3>
    <p>Bei Fragen gerne melden! Privatverkauf, daher keine Garantie oder Rücknahme. 😊</p>
</div>
            """,
            bullet_points=[
                f"Zustand: {product.condition}",
                f"Marke: {product.brand}",
                "Schneller Versand",
                "PayPal möglich",
                "Privatverkauf"
            ],
            seo_keywords=[
                product.name.split()[0] if product.name.split() else "produkt",
                product.brand or "marke",
                product.condition.lower(),
                "gebraucht",
                "original"
            ],
            hashtags=[f"#{product.brand.lower()}" if product.brand else "#gebraucht", "#schnellversand"],
            condition_description=vision_result.condition_details,
            shipping_description="Versand mit DHL für 4,99€, gut verpackt und versichert",
            return_policy="Privatverkauf, daher ausgeschlossen"
        )


# Factory Function
def create_content_service(openai_api_key: Optional[str] = None) -> AIContentService | MockContentService:
    """Erstellt Content Service basierend auf API Key"""
    
    if openai_api_key:
        return AIContentService(openai_api_key)
    else:
        logger.warning("No OpenAI API key provided, using mock content service")
        return MockContentService()

# Usage Example:
"""
# In main.py:
from services.content_service import create_content_service

content_service = create_content_service(os.getenv("OPENAI_API_KEY"))

@app.post("/generate-listing")
async def generate_listing(vision_result: dict, market_insights: dict):
    content = await content_service.generate_listing_content(vision_result, market_insights)
    optimization = await content_service.optimize_content(content)
    return {"content": content.dict(), "optimization": optimization.dict()}
"""