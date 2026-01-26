#!/bin/bash
# Fly.io Deployment Script for FinFind

set -e

echo "🚀 FinFind Deployment to Fly.io"
echo "================================"

# Check if flyctl is installed
if ! command -v flyctl &> /dev/null; then
    echo "❌ flyctl is not installed. Please install it first:"
    echo "   curl -L https://fly.io/install.sh | sh"
    exit 1
fi

# Check if logged in
if ! flyctl auth whoami &> /dev/null; then
    echo "❌ Not logged in to Fly.io. Please run: flyctl auth login"
    exit 1
fi

echo "✅ flyctl is installed and authenticated"

# Function to deploy backend
deploy_backend() {
    echo ""
    echo "📦 Deploying Backend..."
    echo "------------------------"
    
    # Check if app exists
    if ! flyctl apps list | grep -q "finfind-backend"; then
        echo "Creating backend app..."
        flyctl apps create finfind-backend
    fi
    
    # Set secrets if not already set
    echo "Setting secrets..."
    flyctl secrets set GROQ_API_KEY="$GROQ_API_KEY" --app finfind-backend 2>/dev/null || true
    flyctl secrets set QDRANT_URL="$QDRANT_URL" --app finfind-backend 2>/dev/null || true
    flyctl secrets set QDRANT_API_KEY="$QDRANT_API_KEY" --app finfind-backend 2>/dev/null || true
    
    # Deploy
    flyctl deploy --config fly.toml --app finfind-backend
    
    echo "✅ Backend deployed successfully!"
    echo "   URL: https://finfind-backend.fly.dev"
}

# Function to deploy frontend
deploy_frontend() {
    echo ""
    echo "🎨 Deploying Frontend..."
    echo "------------------------"
    
    # Check if app exists
    if ! flyctl apps list | grep -q "finfind-frontend"; then
        echo "Creating frontend app..."
        flyctl apps create finfind-frontend
    fi
    
    # Deploy
    flyctl deploy --config fly.frontend.toml --app finfind-frontend
    
    echo "✅ Frontend deployed successfully!"
    echo "   URL: https://finfind-frontend.fly.dev"
}

# Parse arguments
case "${1:-all}" in
    backend)
        deploy_backend
        ;;
    frontend)
        deploy_frontend
        ;;
    all)
        deploy_backend
        deploy_frontend
        ;;
    *)
        echo "Usage: $0 [backend|frontend|all]"
        exit 1
        ;;
esac

echo ""
echo "🎉 Deployment complete!"
echo ""
echo "Useful commands:"
echo "  flyctl status --app finfind-backend    # Check backend status"
echo "  flyctl logs --app finfind-backend      # View backend logs"
echo "  flyctl status --app finfind-frontend   # Check frontend status"
echo "  flyctl logs --app finfind-frontend     # View frontend logs"
