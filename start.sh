#!/bin/bash
# 🚀 eBay Automation Tool - One-Command Startup Script

echo "🎯 Starting eBay Automation Tool..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    echo "💡 Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose is not installed. Please install it first."
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from template..."
    cp .env.example .env
    echo "📝 Please edit .env file with your API keys before proceeding!"
    echo "🔑 Required: OPENAI_API_KEY, EBAY_APP_ID, etc."
    read -p "Press enter when you've configured your .env file..."
fi

echo "🐳 Starting Docker containers..."
docker-compose up --build -d

echo "⏰ Waiting for services to start..."
sleep 10

# Check if services are running
if docker-compose ps | grep -q "Up"; then
    echo "✅ Services started successfully!"
    echo ""
    echo "🌐 Frontend: http://localhost:3000"
    echo "🔗 Backend API: http://localhost:8000"
    echo "📚 API Docs: http://localhost:8000/docs"
    echo ""
    echo "🎯 Ready to create some eBay magic! 🚀"
else
    echo "❌ Some services failed to start. Check logs:"
    docker-compose logs
    exit 1
fi

# Option to show logs
read -p "Show logs? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    docker-compose logs -f
fi