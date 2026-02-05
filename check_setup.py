#!/usr/bin/env python3
"""
🔍 eBay Tool Setup Checker
Prüft welche API Keys bereits funktionieren und was noch fehlt.
"""

import os
import sys
from dotenv import load_dotenv
import asyncio
import aiohttp
import redis
import psycopg
from typing import Dict, List

# Load environment variables
load_dotenv()

def _env_flag(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}

class SetupChecker:
    def __init__(self):
        self.results: Dict[str, bool] = {}
        self.missing_keys: List[str] = []
        self.working_keys: List[str] = []
        
    async def check_openai_api(self) -> bool:
        """Test OpenAI API Key"""
        api_key = os.getenv('OPENAI_API_KEY', '')
        if not api_key or api_key == 'sk-your-openai-key-here':
            return False
            
        try:
            async with aiohttp.ClientSession() as session:
                headers = {'Authorization': f'Bearer {api_key}'}
                async with session.get('https://api.openai.com/v1/models', headers=headers) as resp:
                    return resp.status == 200
        except Exception as e:
            print(f"❌ OpenAI API Error: {e}")
            return False
    
    async def check_ebay_api(self) -> bool:
        """Test eBay API Keys"""
        app_id = os.getenv('EBAY_APP_ID', '')
        if not app_id or app_id == 'your-ebay-app-id':
            return False
            
        try:
            sandbox_mode = _env_flag("EBAY_SANDBOX", default=False)
            base_url = (
                "https://svcs.sandbox.ebay.com/services/search/FindingService/v1"
                if sandbox_mode
                else "https://svcs.ebay.com/services/search/FindingService/v1"
            )
            # Test eBay Finding API
            url = base_url
            params = {
                'OPERATION-NAME': 'findItemsByKeywords',
                'SERVICE-VERSION': '1.0.0',
                'SECURITY-APPNAME': app_id,
                'RESPONSE-DATA-FORMAT': 'JSON',
                'keywords': 'test'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as resp:
                    return resp.status == 200
        except Exception as e:
            print(f"❌ eBay API Error: {e}")
            return False
    
    def check_database(self) -> bool:
        """Test Database Connection"""
        db_url = os.getenv('DATABASE_URL', '')
        if not db_url:
            return False
            
        try:
            # Test PostgreSQL connection
            with psycopg.connect(db_url, connect_timeout=5) as conn:
                with conn.cursor() as cur:
                    cur.execute('SELECT 1')
                    return cur.fetchone() == (1,)
        except Exception as e:
            print(f"❌ Database Error: {e}")
            return False
    
    def check_redis(self) -> bool:
        """Test Redis Connection"""
        redis_url = os.getenv('REDIS_URL', '')
        if not redis_url:
            return False
            
        try:
            r = redis.from_url(redis_url, socket_timeout=5)
            r.ping()
            return True
        except Exception as e:
            print(f"❌ Redis Error: {e}")
            return False
    
    async def run_all_checks(self):
        """Run all setup checks"""
        print("🔍 **eBay Automation Tool - Setup Check** 🚀\n")
        
        # Check required environment variables
        required_keys = [
            'OPENAI_API_KEY',
            'EBAY_APP_ID', 
            'DATABASE_URL',
            'REDIS_URL',
            'JWT_SECRET'
        ]
        
        print("📋 **Environment Variables Check:**")
        for key in required_keys:
            value = os.getenv(key, '')
            if value and not value.startswith('your-') and not value.endswith('-here'):
                print(f"✅ {key}: Configured")
                self.working_keys.append(key)
            else:
                print(f"❌ {key}: Missing or placeholder")
                self.missing_keys.append(key)
        
        print("\n🔌 **API Connectivity Check:**")
        
        # Test OpenAI
        print("🤖 Testing OpenAI API...", end=" ")
        if await self.check_openai_api():
            print("✅ Working!")
            self.results['openai'] = True
        else:
            print("❌ Failed")
            self.results['openai'] = False
        
        # Test eBay
        print("🛒 Testing eBay API...", end=" ")
        if await self.check_ebay_api():
            print("✅ Working!")
            self.results['ebay'] = True
        else:
            print("❌ Failed (Normal if not configured yet)")
            self.results['ebay'] = False
        
        # Test Database
        print("🗄️  Testing Database...", end=" ")
        if self.check_database():
            print("✅ Connected!")
            self.results['database'] = True
        else:
            print("❌ Failed (Use Docker: docker-compose up -d)")
            self.results['database'] = False
        
        # Test Redis
        print("⚡ Testing Redis...", end=" ")
        if self.check_redis():
            print("✅ Connected!")
            self.results['redis'] = True
        else:
            print("❌ Failed (Use Docker: docker-compose up -d)")
            self.results['redis'] = False
        
        # Summary
        print(f"\n📊 **Setup Summary:**")
        working_count = sum(self.results.values())
        total_count = len(self.results)
        
        print(f"✅ Working: {working_count}/{total_count} services")
        print(f"📝 Environment Keys: {len(self.working_keys)}/{len(required_keys)} configured")
        
        if working_count >= 2:  # OpenAI + Database minimum
            print("\n🚀 **Ready to start development!**")
            print("Run: python main_complete.py")
        else:
            print("\n⚙️  **Next Steps:**")
            if not self.results.get('openai'):
                print("1. Add your OpenAI API key to .env")
            if not self.results.get('database'):
                print("2. Start database: docker-compose up -d")
            if not self.results.get('ebay'):
                print("3. Configure eBay API keys (optional for now)")

def main():
    """Main entry point"""
    checker = SetupChecker()
    asyncio.run(checker.run_all_checks())

if __name__ == "__main__":
    main()