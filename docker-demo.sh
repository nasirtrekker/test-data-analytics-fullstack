#!/bin/bash

# Content Insights Demo - Docker Mode
# Starts full stack: PostgreSQL, MLflow, Backend, Frontend
# Usage: ./docker-demo.sh [up|down|logs]

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_FILE="$PROJECT_ROOT/docker-compose.prod.yml"
ACTION="${1:-up}"

echo "=========================================="
echo "🐳 Content Insights Demo (Docker)"
echo "=========================================="
echo ""

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo "❌ Docker is not running"
    echo "Start Docker and try again"
    exit 1
fi

case "$ACTION" in
    up)
        echo "🚀 Starting full stack (Docker Compose)..."
        echo ""
        docker compose -f "$COMPOSE_FILE" up -d --build
        
        echo "⏳ Waiting for services to be ready..."
        sleep 60
        
        echo ""
        echo "✅ All services started!"
        echo ""
        echo "📍 Services:"
        docker compose -f "$COMPOSE_FILE" ps
        
        echo ""
        echo "🌐 Open in browser:"
        echo "  1. Frontend Dashboard → http://localhost:5173"
        echo "  2. Backend API        → http://localhost:8000/docs"
        echo "  3. MLflow UI          → http://localhost:5000"
        echo "     (Experiments → content-insights-training)"
        echo ""
        echo "💾 Services:"
        echo "  • PostgreSQL (5432) for MLflow metadata"
        echo "  • MLflow Server (5000) with artifact storage"
        echo "  • Backend API (8000) with model inference"
        echo "  • Frontend (5173) with React dashboard"
        echo ""
        
        # Show logs from training job if it exists
        sleep 2
        echo "📋 Checking training pipeline status..."
        docker compose -f "$COMPOSE_FILE" logs backend 2>/dev/null | tail -10 || true
        
        echo ""
        echo "💡 Tips:"
        echo "  • View logs:     docker compose -f docker-compose.prod.yml logs -f backend"
        echo "  • Stop stack:    ./docker-demo.sh down"
        echo "  • Restart:       ./docker-demo.sh restart"
        echo ""
        ;;
        
    down)
        echo "🛑 Stopping all services..."
        docker compose -f "$COMPOSE_FILE" down -v
        echo "✅ Stack stopped and cleaned up"
        echo ""
        ;;
        
    logs)
        echo "📋 Showing live logs (Ctrl+C to exit)..."
        docker compose -f "$COMPOSE_FILE" logs -f
        ;;
        
    restart)
        echo "🔄 Restarting stack..."
        docker compose -f "$COMPOSE_FILE" restart
        sleep 10
        echo "✅ Stack restarted"
        ;;
        
    *)
        echo "Usage: ./docker-demo.sh [up|down|logs|restart]"
        echo ""
        echo "Commands:"
        echo "  up      - Start full stack (default)"
        echo "  down    - Stop and clean up"
        echo "  logs    - Show live logs"
        echo "  restart - Restart services"
        exit 1
        ;;
esac
