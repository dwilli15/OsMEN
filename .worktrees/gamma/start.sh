#!/bin/bash

# OsMEN Startup Script

echo "=========================================="
echo "  OsMEN - OS Management and Engagement Network"
echo "=========================================="
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running"
    echo "Please start Docker and try again"
    exit 1
fi

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  Warning: .env file not found"
    echo "Creating from .env.example..."
    cp .env.example .env
    echo "✅ Created .env file"
    echo "⚠️  Please edit .env with your settings and run this script again"
    exit 0
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p langflow/flows langflow/config
mkdir -p n8n/workflows
mkdir -p postgres/init
mkdir -p agents/boot_hardening agents/daily_brief agents/focus_guardrails
mkdir -p agents/content_editing agents/research_intel
mkdir -p tools/simplewall tools/sysinternals tools/ffmpeg
mkdir -p docs logs

# Start services
echo "🚀 Starting OsMEN services..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Check service status
echo ""
echo "📊 Service Status:"
docker-compose ps

# Pull Ollama models if Ollama is running
if docker ps | grep -q osmen-ollama; then
    echo ""
    echo "🤖 Checking Ollama models..."
    
    if ! docker exec osmen-ollama ollama list | grep -q llama2; then
        echo "📥 Pulling llama2 model (this may take a while)..."
        docker exec osmen-ollama ollama pull llama2
    else
        echo "✅ llama2 model already available"
    fi
fi

echo ""
echo "=========================================="
echo "✅ OsMEN is ready!"
echo "=========================================="
echo ""
echo "Access the services:"
echo "  🌐 Langflow:  http://localhost:7860"
echo "  🔧 n8n:       http://localhost:5678"
echo "  📊 Qdrant:    http://localhost:6333/dashboard"
echo ""
echo "Default n8n credentials: admin / changeme"
echo ""
echo "View logs: docker-compose logs -f"
echo "Stop services: docker-compose down"
echo ""
echo "📚 Documentation: docs/SETUP.md"
echo "=========================================="
