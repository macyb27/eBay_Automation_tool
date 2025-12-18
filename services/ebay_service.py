"""
🏪 eBay Service - Finding & Trading API Integration
Marktpreis-Analyse und automatisches Listing
"""

import asyncio
import aiohttp
import json
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Tuple
from pydantic import BaseModel
from datetime import datetime, timedelta
import hashlib
import hmac
import base64
from urllib.parse import quote
import logging

logger = logging.getLogger(__name__)

class EbayPriceData(BaseModel):
    """Marktpreis-Daten von eBay"""
    average_price: int  # in Cent
    median_price: int
    min_price: int
    max_price: int
    sold_count: int
    active_listings: int
    price_trend: str  # "rising", "stable", "falling"
    competitive_price: int  # Empfohlener Verkaufspreis
    
class EbayMarketInsights(BaseModel):
    """Marktanalyse-Ergebnisse"""
    search_term: str
    price_data: EbayPriceData
    popular_keywords: List[str]
    best_selling_conditions: List[str]
    seasonal_demand: str
    competition_level: str  # "low", "medium", "high"
    success_probability: float

class EbayListingData(BaseModel):
    """Daten für eBay Listing-Erstellung"""
    title: str
    description: str
    category_id: str
    starting_price: int  # in Cent
    buy_it_now_price: Optional[int]
    condition: str
    listing_duration: int  # Tage
    shipping_cost: int
    images: List[str]  # URLs
    item_specifics: Dict[str, str]

class EbayService:
    """eBay API Integration Service"""
    
    def __init__(self, app_id: str, dev_id: str, cert_id: str, user_token: str = None):
        self.app_id = app_id
        self.dev_id = dev_id
        self.cert_id = cert_id
        self.user_token = user_token
        
        # eBay API Endpoints
        self.finding_api_url = "https://svcs.ebay.com/services/search/FindingService/v1"
        self.trading_api_url = "https://api.ebay.com/ws/api.dll"
        self.shopping_api_url = "https://open.api.ebay.com/shopping"
        
        # Deutsche eBay Site ID
        self.site_id = "77"  # eBay.de
        
    async def analyze_market_prices(self, product_name: str, category_id: str = None) -> EbayMarketInsights:
        """
        Analysiert Marktpreise für ein Produkt auf eBay.de
        """
        try:
            # Sold Listings analysieren (letzte 90 Tage)
            sold_data = await self._get_completed_listings(product_name, category_id)
            
            # Aktive Listings analysieren
            active_data = await self._get_active_listings(product_name, category_id)
            
            # Preisstatistiken berechnen
            price_data = self._calculate_price_statistics(sold_data, active_data)
            
            # Market Insights generieren
            insights = EbayMarketInsights(
                search_term=product_name,
                price_data=price_data,
                popular_keywords=self._extract_popular_keywords(sold_data + active_data),
                best_selling_conditions=self._analyze_conditions(sold_data),
                seasonal_demand=self._analyze_seasonal_demand(sold_data),
                competition_level=self._assess_competition(active_data),
                success_probability=self._calculate_success_probability(sold_data, active_data)
            )
            
            logger.info(f"Market analysis completed for: {product_name}")
            return insights
            
        except Exception as e:
            logger.error(f"Market analysis failed: {e}")
            raise

    async def _get_completed_listings(self, product_name: str, category_id: str = None) -> List[Dict]:
        """Abgeschlossene/verkaufte Listings der letzten 90 Tage"""
        
        params = {
            "OPERATION-NAME": "findCompletedItems",
            "SERVICE-VERSION": "1.0.0",
            "SECURITY-APPNAME": self.app_id,
            "RESPONSE-DATA-FORMAT": "JSON",
            "REST-PAYLOAD": "",
            "keywords": product_name,
            "GLOBAL-ID": "EBAY-DE",
            "itemFilter(0).name": "SoldItemsOnly",
            "itemFilter(0).value": "true",
            "itemFilter(1).name": "EndTimeFrom",
            "itemFilter(1).value": (datetime.now() - timedelta(days=90)).isoformat(),
            "sortOrder": "EndTimeSoonest",
            "paginationInput.entriesPerPage": "100"
        }
        
        if category_id:
            params["categoryId"] = category_id
            
        async with aiohttp.ClientSession() as session:
            async with session.get(
                self.finding_api_url,
                params=params,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    return self._parse_finding_response(data)
                else:
                    logger.error(f"eBay Finding API error: {response.status}")
                    return []

    async def _get_active_listings(self, product_name: str, category_id: str = None) -> List[Dict]:
        """Aktive Listings für Konkurrenzanalyse"""
        
        params = {
            "OPERATION-NAME": "findItemsAdvanced",
            "SERVICE-VERSION": "1.0.0",
            "SECURITY-APPNAME": self.app_id,
            "RESPONSE-DATA-FORMAT": "JSON",
            "REST-PAYLOAD": "",
            "keywords": product_name,
            "GLOBAL-ID": "EBAY-DE",
            "itemFilter(0).name": "ListingType",
            "itemFilter(0).value(0)": "FixedPrice",
            "itemFilter(0).value(1)": "Auction",
            "sortOrder": "PricePlusShippingLowest",
            "paginationInput.entriesPerPage": "100"
        }
        
        if category_id:
            params["categoryId"] = category_id
            
        async with aiohttp.ClientSession() as session:
            async with session.get(
                self.finding_api_url,
                params=params,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    return self._parse_finding_response(data)
                else:
                    logger.error(f"eBay Finding API error: {response.status}")
                    return []

    def _parse_finding_response(self, data: Dict) -> List[Dict]:
        """eBay Finding API Response parsen"""
        
        try:
            search_result = data.get("findCompletedItemsResponse", data.get("findItemsAdvancedResponse", [{}]))[0]
            search_result = search_result.get("searchResult", [{}])[0]
            items = search_result.get("item", [])
            
            parsed_items = []
            for item in items:
                try:
                    # Preis extrahieren
                    selling_status = item.get("sellingStatus", [{}])[0]
                    price_info = selling_status.get("currentPrice", selling_status.get("convertedCurrentPrice", [{}]))[0]
                    price = float(price_info.get("__value__", 0))
                    currency = price_info.get("@currencyId", "EUR")
                    
                    # Preis zu Cent konvertieren
                    price_cents = int(price * 100) if currency == "EUR" else int(price * 85)  # Rough USD conversion
                    
                    parsed_item = {
                        "title": item.get("title", [""])[0],
                        "price_cents": price_cents,
                        "condition": item.get("condition", [{"conditionDisplayName": ["Gebraucht"]}])[0].get("conditionDisplayName", ["Gebraucht"])[0],
                        "listing_type": item.get("listingInfo", [{}])[0].get("listingType", [""])[0],
                        "end_time": item.get("listingInfo", [{}])[0].get("endTime", [""])[0],
                        "category_id": item.get("primaryCategory", [{}])[0].get("categoryId", [""])[0],
                        "watch_count": int(item.get("listingInfo", [{}])[0].get("watchCount", [0])[0]),
                        "shipping_cost": self._extract_shipping_cost(item)
                    }
                    parsed_items.append(parsed_item)
                    
                except Exception as e:
                    logger.warning(f"Failed to parse item: {e}")
                    continue
                    
            return parsed_items
            
        except Exception as e:
            logger.error(f"Failed to parse eBay response: {e}")
            return []

    def _extract_shipping_cost(self, item: Dict) -> int:
        """Versandkosten extrahieren"""
        try:
            shipping_info = item.get("shippingInfo", [{}])[0]
            shipping_cost = shipping_info.get("shippingServiceCost", [{"__value__": "0"}])[0].get("__value__", "0")
            return int(float(shipping_cost) * 100)  # Zu Cent
        except:
            return 499  # Default 4.99€ Versand

    def _calculate_price_statistics(self, sold_data: List[Dict], active_data: List[Dict]) -> EbayPriceData:
        """Preisstatistiken aus Verkaufs- und aktiven Daten berechnen"""
        
        if not sold_data:
            # Fallback auf aktive Listings
            prices = [item["price_cents"] for item in active_data if item["price_cents"] > 0]
        else:
            prices = [item["price_cents"] for item in sold_data if item["price_cents"] > 0]
        
        if not prices:
            return EbayPriceData(
                average_price=2000, median_price=2000, min_price=1000, 
                max_price=3000, sold_count=0, active_listings=len(active_data),
                price_trend="unknown", competitive_price=2000
            )
        
        prices.sort()
        
        average_price = sum(prices) // len(prices)
        median_price = prices[len(prices) // 2]
        min_price = min(prices)
        max_price = max(prices)
        
        # Trend-Analyse (vereinfacht)
        recent_prices = [item["price_cents"] for item in sold_data[-10:]]
        older_prices = [item["price_cents"] for item in sold_data[:-10]]
        
        if recent_prices and older_prices:
            recent_avg = sum(recent_prices) / len(recent_prices)
            older_avg = sum(older_prices) / len(older_prices)
            
            if recent_avg > older_avg * 1.05:
                trend = "rising"
            elif recent_avg < older_avg * 0.95:
                trend = "falling"
            else:
                trend = "stable"
        else:
            trend = "unknown"
        
        # Competitive Price: Leicht unter dem Durchschnitt für schnellen Verkauf
        competitive_price = int(average_price * 0.95)
        
        return EbayPriceData(
            average_price=average_price,
            median_price=median_price,
            min_price=min_price,
            max_price=max_price,
            sold_count=len(sold_data),
            active_listings=len(active_data),
            price_trend=trend,
            competitive_price=competitive_price
        )

    def _extract_popular_keywords(self, items: List[Dict]) -> List[str]:
        """Beliebte Keywords aus Titeln extrahieren"""
        
        word_counts = {}
        stopwords = {
            "und", "der", "die", "das", "mit", "für", "von", "zu", "in", "an", "auf", "bei", "aus",
            "gebraucht", "neu", "original", "top", "super", "sehr", "gut", "schön", "toll"
        }
        
        for item in items:
            title = item.get("title", "").lower()
            words = title.split()
            
            for word in words:
                word = word.strip(".,!?()[]{}\"'")
                if len(word) > 2 and word not in stopwords and not word.isdigit():
                    word_counts[word] = word_counts.get(word, 0) + 1
        
        # Top 10 Keywords
        popular_keywords = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        return [word for word, count in popular_keywords]

    def _analyze_conditions(self, sold_data: List[Dict]) -> List[str]:
        """Erfolgreichste Zustandskategorien analysieren"""
        
        condition_counts = {}
        for item in sold_data:
            condition = item.get("condition", "Gebraucht")
            condition_counts[condition] = condition_counts.get(condition, 0) + 1
        
        # Nach Häufigkeit sortieren
        sorted_conditions = sorted(condition_counts.items(), key=lambda x: x[1], reverse=True)
        return [condition for condition, count in sorted_conditions[:3]]

    def _analyze_seasonal_demand(self, sold_data: List[Dict]) -> str:
        """Saisonale Nachfrage analysieren (vereinfacht)"""
        
        current_month = datetime.now().month
        
        # Vereinfachte saisonale Kategorisierung
        if current_month in [11, 12, 1]:  # Winter/Weihnachten
            return "high"  # Hohe Nachfrage vor Weihnachten
        elif current_month in [6, 7, 8]:  # Sommer
            return "medium"
        else:
            return "normal"

    def _assess_competition(self, active_data: List[Dict]) -> str:
        """Konkurrenz-Level bewerten"""
        
        active_count = len(active_data)
        
        if active_count > 100:
            return "high"
        elif active_count > 30:
            return "medium"
        else:
            return "low"

    def _calculate_success_probability(self, sold_data: List[Dict], active_data: List[Dict]) -> float:
        """Verkaufserfolgs-Wahrscheinlichkeit berechnen"""
        
        sold_count = len(sold_data)
        active_count = len(active_data)
        
        if sold_count == 0 and active_count == 0:
            return 0.3  # Niedrig, da kein Markt
        elif sold_count == 0:
            return 0.2  # Niedrig, da keine Verkäufe
        elif active_count == 0:
            return 0.9  # Hoch, da keine Konkurrenz
        
        # Ratio von verkauften zu aktiven Listings
        success_ratio = sold_count / (sold_count + active_count)
        
        # Weitere Faktoren einbeziehen
        if success_ratio > 0.7:
            return min(0.95, success_ratio + 0.1)
        elif success_ratio > 0.3:
            return success_ratio
        else:
            return max(0.1, success_ratio - 0.1)

    async def get_category_suggestions(self, product_name: str) -> List[Tuple[str, str]]:
        """eBay Kategorie-Vorschläge basierend auf Produktname"""
        
        # Vereinfachte Kategorie-Zuordnung (in Produktion: eBay Categories API verwenden)
        category_mapping = {
            # Electronics
            "iphone": ("9355", "Handy & Telefon > Apple iPhone"),
            "samsung": ("9355", "Handy & Telefon > Samsung"),
            "laptop": ("177", "Computer, Tablets & Netzwerk > Laptops & Netbooks"),
            "playstation": ("139973", "PC- & Videospiele > Konsolen"),
            
            # Fashion
            "nike": ("15709", "Kleidung & Accessoires > Herrenmode"),
            "adidas": ("15709", "Kleidung & Accessoires > Herrenmode"),
            "jeans": ("11554", "Kleidung & Accessoires > Herrenmode > Hosen"),
            
            # Home
            "ikea": ("11700", "Möbel & Wohnen > Möbel"),
            "kitchen": ("20625", "Möbel & Wohnen > Küche & Esszimmer"),
            
            # Default
            "default": ("99", "Sonstige")
        }
        
        product_lower = product_name.lower()
        
        for keyword, (cat_id, cat_name) in category_mapping.items():
            if keyword in product_lower:
                return [(cat_id, cat_name)]
        
        return [category_mapping["default"]]


class MockEbayService:
    """Mock Service für Development ohne API Keys"""
    
    async def analyze_market_prices(self, product_name: str, category_id: str = None) -> EbayMarketInsights:
        """Mock Marktanalyse für Testing"""
        
        await asyncio.sleep(3)  # Simuliere API-Latenz
        
        # Realistische Mock-Daten basierend auf Produkttyp
        base_price = 25000  # 250€
        
        if "iphone" in product_name.lower():
            base_price = 45000
        elif "laptop" in product_name.lower():
            base_price = 35000
        elif "nike" in product_name.lower():
            base_price = 8000
        
        return EbayMarketInsights(
            search_term=product_name,
            price_data=EbayPriceData(
                average_price=base_price,
                median_price=int(base_price * 0.95),
                min_price=int(base_price * 0.6),
                max_price=int(base_price * 1.4),
                sold_count=45,
                active_listings=23,
                price_trend="stable",
                competitive_price=int(base_price * 0.92)
            ),
            popular_keywords=[
                product_name.split()[0] if product_name.split() else "produkt",
                "gebraucht", "gut", "zustand", "original", "schnell"
            ],
            best_selling_conditions=["Sehr gut", "Gut", "Gebraucht"],
            seasonal_demand="normal",
            competition_level="medium",
            success_probability=0.78
        )
    
    async def get_category_suggestions(self, product_name: str) -> List[Tuple[str, str]]:
        """Mock Kategorie-Vorschläge"""
        return [("99", "Sonstige > Allgemein")]

# Factory Function
def create_ebay_service(
    app_id: Optional[str] = None,
    dev_id: Optional[str] = None,
    cert_id: Optional[str] = None,
    user_token: Optional[str] = None
) -> EbayService | MockEbayService:
    """Erstellt eBay Service basierend auf verfügbaren API Keys"""
    
    if all([app_id, dev_id, cert_id]):
        return EbayService(app_id, dev_id, cert_id, user_token)
    else:
        logger.warning("eBay API credentials not found, using mock service")
        return MockEbayService()

# Usage Example:
"""
# In main.py:
from services.ebay_service import create_ebay_service

ebay_service = create_ebay_service(
    app_id=os.getenv("EBAY_APP_ID"),
    dev_id=os.getenv("EBAY_DEV_ID"), 
    cert_id=os.getenv("EBAY_CERT_ID")
)

@app.get("/market-analysis/{product_name}")
async def get_market_analysis(product_name: str):
    insights = await ebay_service.analyze_market_prices(product_name)
    return insights.dict()
"""