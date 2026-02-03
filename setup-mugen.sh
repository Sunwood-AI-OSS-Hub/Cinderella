#!/bin/bash

# MultimediaOS-MUGEN Setup Script

echo "=========================================="
echo "Setting up MultimediaOS-MUGEN Environment"
echo "=========================================="

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create directories
echo "📁 Creating required directories..."
mkdir -p config/agent2/MultimediaOS-MUGEN/media
mkdir -p data/screenshots
mkdir -p data/chrome-profile
mkdir -p data/.claude

# Copy environment file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Copying .env.example to .env..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your API keys before starting the services!"
fi

# Build images
echo "🏗️  Building Docker images..."
docker-compose -f docker-compose-mugen.yml build

# Start services
echo "🚀 Starting services..."
docker-compose -f docker-compose-mugen.yml up -d

# Wait for services to start
echo "⏳ Waiting for services to start..."
sleep 10

# Check service status
echo "📊 Checking service status..."
docker-compose -f docker-compose-mugen.yml ps

echo ""
echo "=========================================="
echo "✅ Setup complete!"
echo "=========================================="
echo ""
echo "Service URLs:"
echo "  CC API:          http://localhost:8081"
echo "  Browser API:     http://localhost:8083"
echo "  Browser noVNC:   http://localhost:7900"
echo "  Discord Bot:     http://localhost:8082"
echo ""
echo "To view logs:"
echo "  docker-compose -f docker-compose-mugen.yml logs -f"
echo ""
echo "To stop services:"
echo "  docker-compose -f docker-compose-mugen.yml down"
echo ""