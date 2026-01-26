# 🚀 FinFind Deployment Guide

This guide covers deploying FinFind to various platforms including Docker, Railway, Render, Fly.io, and Vercel.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Variables](#environment-variables)
3. [Docker Deployment](#docker-deployment)
4. [Railway Deployment](#railway-deployment)
5. [Render Deployment](#render-deployment)
6. [Fly.io Deployment](#flyio-deployment)
7. [Vercel Deployment](#vercel-deployment-frontend)
8. [Production Checklist](#production-checklist)
9. [Monitoring & Logging](#monitoring--logging)
10. [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before deploying, ensure you have:

- [ ] Qdrant Cloud account with cluster created
- [ ] Groq API key
- [ ] Domain name (optional but recommended)
- [ ] SSL certificate (for custom domain)

---

## Environment Variables

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `GROQ_API_KEY` | Groq API key | `gsk_xxxx...` |
| `QDRANT_URL` | Qdrant cluster URL | `https://xxx.qdrant.io` |
| `QDRANT_API_KEY` | Qdrant API key | `xxx...` |

### Optional Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `COLLECTION_NAME` | `finfind_products` | Product collection name |
| `USER_COLLECTION` | `finfind_users` | User collection name |
| `ENVIRONMENT` | `production` | Environment name |
| `LOG_LEVEL` | `INFO` | Logging level |
| `CORS_ORIGINS` | `*` | Allowed CORS origins |

---

## Docker Deployment

### Local Development

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Production Deployment

```bash
# Build production images
docker-compose -f docker-compose.prod.yml build

# Start production services
docker-compose -f docker-compose.prod.yml up -d

# Scale services
docker-compose -f docker-compose.prod.yml up -d --scale backend=3
```

### With Local Qdrant

```bash
# Include local Qdrant instance
docker-compose --profile local-db up -d
```

### Custom Docker Registry

```bash
# Tag images
docker tag finfind-backend:latest your-registry/finfind-backend:v1.0.0
docker tag finfind-frontend:latest your-registry/finfind-frontend:v1.0.0

# Push to registry
docker push your-registry/finfind-backend:v1.0.0
docker push your-registry/finfind-frontend:v1.0.0
```

---

## Railway Deployment

### Initial Setup

1. Install Railway CLI:
   ```bash
   npm install -g @railway/cli
   railway login
   ```

2. Create a new project:
   ```bash
   railway init
   ```

3. Set environment variables:
   ```bash
   railway variables set GROQ_API_KEY=your_key
   railway variables set QDRANT_URL=your_url
   railway variables set QDRANT_API_KEY=your_key
   ```

### Deploy

```bash
# Deploy from CLI
railway up

# Or connect to GitHub for automatic deploys
railway link
```

### Configuration

The `railway.toml` file is pre-configured:

```toml
[build]
builder = "DOCKERFILE"
dockerfilePath = "backend/Dockerfile"

[deploy]
startCommand = "python -m uvicorn app.api.main:app --host 0.0.0.0 --port $PORT"
healthcheckPath = "/health"
```

### Custom Domain

```bash
railway domain
# Follow prompts to add custom domain
```

---

## Render Deployment

### Using render.yaml (Recommended)

1. Connect your GitHub repository to Render
2. Render will automatically detect `render.yaml`
3. Review and approve the configuration
4. Set secret environment variables in Render dashboard

### Manual Setup

1. Create a new Web Service
2. Select your repository
3. Configure:
   - **Environment**: Docker
   - **Dockerfile Path**: `backend/Dockerfile`
   - **Start Command**: (use Dockerfile CMD)

### Environment Variables

Set in Render dashboard:
- Go to your service → Environment
- Add each variable from `.env.example`

### Auto-Deploy

Render automatically deploys on:
- Push to main branch
- Manual trigger from dashboard

---

## Fly.io Deployment

### Initial Setup

1. Install flyctl:
   ```powershell
   # Windows
   iwr https://fly.io/install.ps1 -useb | iex
   
   # macOS/Linux
   curl -L https://fly.io/install.sh | sh
   ```

2. Login:
   ```bash
   flyctl auth login
   ```

### Deploy Backend

```bash
# Create app (first time only)
flyctl apps create finfind-backend

# Set secrets
flyctl secrets set GROQ_API_KEY=your_key --app finfind-backend
flyctl secrets set QDRANT_URL=your_url --app finfind-backend
flyctl secrets set QDRANT_API_KEY=your_key --app finfind-backend

# Deploy
flyctl deploy --config fly.toml --app finfind-backend
```

### Deploy Frontend

```bash
# Create app
flyctl apps create finfind-frontend

# Deploy
flyctl deploy --config fly.frontend.toml --app finfind-frontend
```

### Using Deploy Script

```powershell
# Windows
.\scripts\deploy-fly.ps1 -Target all

# Linux/macOS
./scripts/deploy-fly.sh all
```

### Scaling

```bash
# Scale backend
flyctl scale count 3 --app finfind-backend

# Scale memory
flyctl scale memory 2048 --app finfind-backend
```

### Custom Domain

```bash
flyctl certs create yourdomain.com --app finfind-frontend
```

---

## Vercel Deployment (Frontend)

### Setup

1. Install Vercel CLI:
   ```bash
   npm install -g vercel
   ```

2. Login:
   ```bash
   vercel login
   ```

### Deploy

```bash
cd Frontend

# Preview deployment
vercel

# Production deployment
vercel --prod
```

### Configuration

The `vercel.json` is pre-configured:

```json
{
  "framework": "nextjs",
  "rewrites": [
    {
      "source": "/api/:path*",
      "destination": "https://your-backend.fly.dev/:path*"
    }
  ]
}
```

### Environment Variables

Set in Vercel dashboard or CLI:

```bash
vercel env add NEXT_PUBLIC_API_URL
# Enter: https://finfind-backend.fly.dev
```

### GitHub Integration

1. Connect repository in Vercel dashboard
2. Configure:
   - Framework Preset: Next.js
   - Root Directory: `Frontend`
   - Build Command: `npm run build`
   - Output Directory: `.next`

---

## Production Checklist

### Security

- [ ] All API keys are stored as secrets (not in code)
- [ ] CORS is configured for production domains only
- [ ] HTTPS is enforced
- [ ] Rate limiting is enabled
- [ ] Input validation is in place
- [ ] Security headers are configured

### Performance

- [ ] Gzip compression enabled
- [ ] Static assets are cached
- [ ] Database connection pooling configured
- [ ] CDN configured for static assets
- [ ] Image optimization enabled

### Reliability

- [ ] Health checks configured
- [ ] Auto-restart on failure enabled
- [ ] Backup strategy in place
- [ ] Monitoring configured
- [ ] Error tracking enabled (e.g., Sentry)

### Scaling

- [ ] Horizontal scaling tested
- [ ] Load balancing configured
- [ ] Database can handle load
- [ ] Caching strategy implemented

---

## Monitoring & Logging

### Application Logging

Configure structured logging:

```python
# backend/app/config.py

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "class": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(name)s %(levelname)s %(message)s"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json"
        }
    },
    "root": {
        "level": "INFO",
        "handlers": ["console"]
    }
}
```

### Metrics

Prometheus metrics are exposed at `/metrics`:

```python
# Key metrics
- http_requests_total
- http_request_duration_seconds
- agent_queries_total
- search_latency_seconds
- recommendation_score_histogram
```

### Health Checks

Health endpoint at `/health` returns:

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "services": {
    "database": "connected",
    "vector_store": "connected",
    "llm": "connected"
  }
}
```

### Error Tracking (Sentry)

```python
# Add Sentry DSN to environment
SENTRY_DSN=https://xxx@sentry.io/xxx

# Automatically captures:
# - Unhandled exceptions
# - Performance metrics
# - User context
```

---

## Troubleshooting

### Common Issues

#### Container won't start

```bash
# Check logs
docker logs finfind-backend

# Common causes:
# - Missing environment variables
# - Port already in use
# - Insufficient memory
```

#### Connection refused to Qdrant

```bash
# Verify Qdrant URL
curl https://your-cluster.qdrant.io/collections

# Check if API key is correct
# Ensure cluster is running
```

#### LLM API errors

```bash
# Verify Groq API key
curl -H "Authorization: Bearer $GROQ_API_KEY" \
  https://api.groq.com/openai/v1/models

# Check rate limits
# Verify model availability
```

#### Frontend can't reach backend

```bash
# Check CORS configuration
# Verify NEXT_PUBLIC_API_URL is set correctly
# Check if backend is accessible
curl https://your-backend.fly.dev/health
```

### Debug Mode

Enable debug mode for more information:

```bash
# Backend
LOG_LEVEL=DEBUG python run.py

# Frontend
DEBUG=* npm run dev
```

### Getting Help

- Check logs first
- Review error messages carefully
- Search GitHub issues
- Ask in Discord community
- Contact support@finfind.com

---

## Rollback

### Docker

```bash
# Roll back to previous version
docker-compose down
docker-compose -f docker-compose.prev.yml up -d
```

### Fly.io

```bash
# List releases
flyctl releases --app finfind-backend

# Roll back
flyctl releases rollback v5 --app finfind-backend
```

### Vercel

Roll back from Vercel dashboard:
1. Go to Deployments
2. Find previous successful deployment
3. Click "..." → "Promote to Production"

---

*Need help? Contact devops@finfind.com*
