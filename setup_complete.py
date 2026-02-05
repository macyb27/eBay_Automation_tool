#!/usr/bin/env python3
"""
🚀 eBay Automation Tool - COMPLETE SETUP SCRIPT
One-Click Installation und Konfiguration für Production
"""

import os
import sys
import asyncio
import subprocess
import secrets
import shutil
from pathlib import Path
from typing import Dict, List

# ========================================
# 🎨 COLORED OUTPUT
# ========================================

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(text: str):
    print(f"\n{Colors.HEADER}{Colors.BOLD}🚀 {text}{Colors.ENDC}")

def print_success(text: str):
    print(f"{Colors.GREEN}✅ {text}{Colors.ENDC}")

def print_warning(text: str):
    print(f"{Colors.WARNING}⚠️  {text}{Colors.ENDC}")

def print_error(text: str):
    print(f"{Colors.FAIL}❌ {text}{Colors.ENDC}")

def print_info(text: str):
    print(f"{Colors.CYAN}ℹ️  {text}{Colors.ENDC}")

# ========================================
# 🔧 SETUP CONFIGURATION
# ========================================

class EbayAutomationSetup:
    """Complete Setup Manager"""
    
    def __init__(self):
        self.project_root = Path.cwd()
        self.requirements_installed = False
        self.db_initialized = False
        self.env_configured = False
        
    async def run_complete_setup(self):
        """Run Complete Setup Process"""
        
        print_header("eBay Automation Tool - COMPLETE SETUP")
        print("🎯 Ultra-Fast AI-Powered eBay Listing Generator")
        print("⚡ Performance-Optimized Production Setup\n")
        
        try:
            # Check System Requirements
            await self.check_system_requirements()
            
            # Python Dependencies
            await self.install_python_dependencies()
            
            # Environment Configuration
            await self.setup_environment()
            
            # Database Setup
            await self.setup_database()
            
            # Redis Setup Check
            await self.check_redis_setup()
            
            # API Keys Configuration
            await self.configure_api_keys()
            
            # Test Installation
            await self.test_installation()
            
            # Final Instructions
            self.print_completion_instructions()
            
        except KeyboardInterrupt:
            print_warning("Setup interrupted by user")
            sys.exit(1)
        except Exception as e:
            print_error(f"Setup failed: {e}")
            sys.exit(1)
    
    async def check_system_requirements(self):
        """Check System Requirements"""
        
        print_header("System Requirements Check")
        
        # Python Version
        python_version = sys.version_info
        if python_version >= (3, 11):
            print_success(f"Python {python_version.major}.{python_version.minor} ✅")
        else:
            print_error(f"Python 3.11+ required, found {python_version.major}.{python_version.minor}")
            sys.exit(1)
        
        # Check pip
        try:
            subprocess.run([sys.executable, "-m", "pip", "--version"], 
                         check=True, capture_output=True)
            print_success("pip available ✅")
        except subprocess.CalledProcessError:
            print_error("pip not available")
            sys.exit(1)
        
        # Check Git (Optional)
        try:
            subprocess.run(["git", "--version"], check=True, capture_output=True)
            print_success("git available ✅")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print_warning("git not available (optional)")
        
        # Check Docker (Optional)
        try:
            subprocess.run(["docker", "--version"], check=True, capture_output=True)
            print_success("Docker available ✅")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print_info("Docker not available (optional for production)")
    
    async def install_python_dependencies(self):
        """Install Python Dependencies"""
        
        print_header("Installing Python Dependencies")
        
        # Update requirements.txt if needed
        await self.create_requirements_file()
        
        print_info("Installing dependencies... (this may take a few minutes)")
        
        try:
            # Upgrade pip first
            subprocess.run([
                sys.executable, "-m", "pip", "install", "--upgrade", "pip"
            ], check=True)
            
            # Install requirements
            subprocess.run([
                sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
            ], check=True)
            
            print_success("Dependencies installed successfully")
            self.requirements_installed = True
            
        except subprocess.CalledProcessError as e:
            print_error(f"Failed to install dependencies: {e}")
            print_info("Try running manually: pip install -r requirements.txt")
            raise
    
    async def create_requirements_file(self):
        """Create/Update requirements.txt"""
        
        requirements = [
            "fastapi==0.104.1",
            "uvicorn[standard]==0.24.0",
            "sqlalchemy[asyncio]==2.0.23", 
            "asyncpg==0.29.0",
            "aiosqlite==0.19.0",
            "redis[hiredis]==5.0.1",
            "aiohttp==3.9.0",
            "httpx==0.25.2",
            "pydantic==2.5.0",
            "pillow==10.1.0",
            "python-multipart==0.0.6",
            "python-jose[cryptography]==3.3.0",
            "passlib[bcrypt]==1.7.4",
            "pytest==7.4.3",
            "pytest-asyncio==0.21.1",
            "gunicorn==21.2.0",
            "psutil==5.9.6"
        ]
        
        with open("requirements.txt", "w") as f:
            for req in requirements:
                f.write(f"{req}\n")
        
        print_info("requirements.txt updated")
    
    async def setup_environment(self):
        """Setup Environment Configuration"""
        
        print_header("Environment Configuration")
        
        # Create .env file
        env_file = self.project_root / ".env"
        
        if env_file.exists():
            print_info("Existing .env file found")
            response = input("Do you want to overwrite it? [y/N]: ").strip().lower()
            if response != 'y':
                print_info("Keeping existing .env file")
                return
        
        # Generate secure keys
        secret_key = secrets.token_urlsafe(32)
        jwt_secret = secrets.token_urlsafe(32)
        
        env_content = f"""# 🚀 eBay Automation Tool - Environment Configuration
# Generated by setup script on {os.getcwd()}

# ========================================
# 🤖 AI SERVICE APIS
# ========================================

# OpenAI Configuration (Add your key here)
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o
OPENAI_MAX_TOKENS=2000
OPENAI_TEMPERATURE=0.1

# ========================================
# 🏪 EBAY API CONFIGURATION  
# ========================================

# eBay Developer Credentials (Add your keys here)
EBAY_APP_ID=your_ebay_app_id_here
EBAY_DEV_ID=your_ebay_dev_id_here
EBAY_CERT_ID=your_ebay_cert_id_here
EBAY_USER_TOKEN=your_ebay_user_token_here

# eBay Settings
EBAY_SITE_ID=77
EBAY_SANDBOX=false

# ========================================
# 💾 DATABASE CONFIGURATION
# ========================================

# SQLite für Development (Production: PostgreSQL)
DATABASE_URL=sqlite+aiosqlite:///./ebay_automation.db

# ========================================
# ⚡ REDIS CACHE CONFIGURATION
# ========================================

# Redis für Caching (Optional für Development)
REDIS_URL=redis://localhost:6379/0

# ========================================
# 🚀 APPLICATION SETTINGS
# ========================================

ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO

# Security
SECRET_KEY={secret_key}
JWT_SECRET_KEY={jwt_secret}

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# File Upload
MAX_FILE_SIZE=10485760
UPLOAD_DIR=./uploads

# Performance
REQUEST_TIMEOUT=60
API_CALL_TIMEOUT=30
"""
        
        with open(".env", "w") as f:
            f.write(env_content)
        
        print_success(".env file created")
        print_info("Please edit .env and add your API keys")
        self.env_configured = True
    
    async def setup_database(self):
        """Setup Database"""
        
        print_header("Database Setup")
        
        try:
            # Create database directory
            os.makedirs("database", exist_ok=True)
            
            # Initialize database
            print_info("Initializing database...")
            
            # Import and run database initialization
            try:
                from database.connection import init_db
                await init_db()
                print_success("Database initialized successfully")
                self.db_initialized = True
                
            except Exception as e:
                print_warning(f"Database initialization failed: {e}")
                print_info("Database will be initialized on first run")
                
        except Exception as e:
            print_error(f"Database setup failed: {e}")
            raise
    
    async def check_redis_setup(self):
        """Check Redis Setup"""
        
        print_header("Redis Cache Setup")
        
        try:
            # Try to connect to Redis
            import redis.asyncio as redis
            
            redis_client = redis.from_url("redis://localhost:6379/0")
            await redis_client.ping()
            await redis_client.close()
            
            print_success("Redis is running and accessible ✅")
            
        except Exception as e:
            print_warning("Redis not available")
            print_info("Redis is optional for development but recommended for production")
            print_info("Install Redis: https://redis.io/download")
    
    async def configure_api_keys(self):
        """Guide User Through API Key Configuration"""
        
        print_header("API Keys Configuration")
        
        print_info("To use live AI services, you need API keys:")
        print("")
        
        # OpenAI
        print("🤖 OpenAI GPT-4 Vision (RECOMMENDED)")
        print("   - Go to: https://platform.openai.com/api-keys")
        print("   - Create new secret key")
        print("   - Add to .env: OPENAI_API_KEY=sk-...")
        print("")
        
        # eBay
        print("🏪 eBay Developer APIs (OPTIONAL)")
        print("   - Go to: https://developer.ebay.com/api-docs/static/gs_create-the-ebay-api-keysets.html")
        print("   - Create developer account")
        print("   - Get App ID, Dev ID, Cert ID")
        print("   - Add to .env file")
        print("")
        
        print_info("Without API keys, the system will use mock services for testing")
        
        response = input("Have you configured your API keys? [y/N]: ").strip().lower()
        if response == 'y':
            print_success("API keys configured")
        else:
            print_info("You can configure API keys later by editing .env")
    
    async def test_installation(self):
        """Test Installation"""
        
        print_header("Testing Installation")
        
        try:
            # Test imports
            print_info("Testing imports...")
            
            from main_optimized import app
            from services.vision_service import create_vision_service
            from services.ebay_service import create_ebay_service
            from services.content_service import create_content_service
            
            print_success("All imports successful")
            
            # Test service creation
            print_info("Testing service creation...")
            
            vision_service = create_vision_service(None)  # Mock mode
            ebay_service = create_ebay_service(None, None, None)  # Mock mode
            content_service = create_content_service(None)  # Mock mode
            
            print_success("All services created successfully")
            
            # Test database
            if self.db_initialized:
                print_info("Testing database connection...")
                from database.connection import test_connection
                db_ok = await test_connection()
                if db_ok:
                    print_success("Database connection OK")
                else:
                    print_warning("Database connection failed")
            
            print_success("Installation test completed")
            
        except Exception as e:
            print_error(f"Installation test failed: {e}")
            raise
    
    def print_completion_instructions(self):
        """Print Completion Instructions"""
        
        print_header("🎉 Setup Complete!")
        
        print(f"""
{Colors.GREEN}✅ eBay Automation Tool is ready to use!{Colors.ENDC}

{Colors.BOLD}🚀 Quick Start:{Colors.ENDC}

1. Start the development server:
   {Colors.CYAN}python main_optimized.py{Colors.ENDC}

2. Open your browser:
   {Colors.CYAN}http://localhost:8000{Colors.ENDC}

3. API Documentation:
   {Colors.CYAN}http://localhost:8000/api/docs{Colors.ENDC}

{Colors.BOLD}🔧 Configuration:{Colors.ENDC}

• Edit {Colors.CYAN}.env{Colors.ENDC} file to add your API keys
• For production: Use {Colors.CYAN}docker-compose.production.yml{Colors.ENDC}

{Colors.BOLD}🧪 Testing:{Colors.ENDC}

• Run tests: {Colors.CYAN}pytest tests/ -v{Colors.ENDC}
• Performance tests: {Colors.CYAN}pytest tests/test_complete_pipeline.py -v{Colors.ENDC}

{Colors.BOLD}📊 Features:{Colors.ENDC}

✅ AI Vision Analysis (GPT-4V)
✅ eBay Market Research  
✅ Automated Content Generation
✅ Ultra-Fast Performance
✅ Production-Ready Deployment

{Colors.BOLD}🔗 Next Steps:{Colors.ENDC}

1. Add your OpenAI API key for live vision analysis
2. Add eBay API keys for real market data
3. Test with sample product images
4. Deploy to production when ready

{Colors.WARNING}Need help? Check the documentation or run with --help{Colors.ENDC}
        """)

# ========================================
# 🎯 MAIN EXECUTION
# ========================================

async def main():
    """Main Setup Function"""
    
    # Parse command line arguments
    if len(sys.argv) > 1 and sys.argv[1] in ["--help", "-h"]:
        print("""
🚀 eBay Automation Tool Setup

Usage:
  python setup_complete.py          # Run complete setup
  python setup_complete.py --help   # Show this help

This script will:
✅ Check system requirements
✅ Install Python dependencies  
✅ Configure environment variables
✅ Setup database
✅ Test installation
✅ Provide next steps

Requirements:
• Python 3.11+
• pip
• Internet connection

Optional:
• Redis (for caching)
• Docker (for production)
• eBay API keys (for live market data)
• OpenAI API key (for AI vision analysis)
        """)
        return
    
    # Run setup
    setup = EbayAutomationSetup()
    await setup.run_complete_setup()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print_warning("\nSetup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"Setup failed: {e}")
        sys.exit(1)