# 📚 FinFind API Documentation

## Overview

The FinFind API provides access to the intelligent financial product discovery platform. This RESTful API enables semantic search, personalized recommendations, product alternatives, and explainability features.

**Base URL**: `http://localhost:8000` (development) or `https://api.finfind.com` (production)

---

## Authentication

Currently, the API uses API key authentication for protected endpoints.

```bash
curl -H "X-API-Key: your_api_key" https://api.finfind.com/endpoint
```

---

## Common Response Format

All API responses follow this structure:

```json
{
  "success": true,
  "data": { ... },
  "meta": {
    "timestamp": "2024-01-15T10:30:00Z",
    "request_id": "req_abc123"
  }
}
```

Error responses:

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input parameters",
    "details": { ... }
  }
}
```

---

## Endpoints

### Search

#### POST /search

Perform semantic search for financial products.

**Request Body:**
```json
{
  "query": "safe investment options for beginners",
  "user_id": "user_123",
  "filters": {
    "min_price": 0,
    "max_price": 10000,
    "category": "investments",
    "risk_level": "low"
  },
  "limit": 10
}
```

**Parameters:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `query` | string | Yes | Natural language search query |
| `user_id` | string | No | User ID for personalization |
| `filters.min_price` | number | No | Minimum price filter |
| `filters.max_price` | number | No | Maximum price filter |
| `filters.category` | string | No | Product category |
| `filters.risk_level` | string | No | Risk level (low, medium, high) |
| `limit` | integer | No | Number of results (default: 10, max: 50) |

**Response:**
```json
{
  "success": true,
  "data": {
    "results": [
      {
        "id": "prod_001",
        "name": "SafeStart Savings Account",
        "description": "Perfect for beginners with FDIC insurance",
        "category": "savings",
        "price": 0,
        "risk_level": "low",
        "score": 0.95,
        "highlights": ["No minimum balance", "FDIC insured"]
      }
    ],
    "total": 25,
    "query_interpretation": "Looking for low-risk investment products suitable for beginners"
  }
}
```

---

#### POST /search/image

Search for products using an image.

**Request:**
```
Content-Type: multipart/form-data

image: <file>
user_id: user_123 (optional)
```

**Response:**
```json
{
  "success": true,
  "data": {
    "detected_features": ["credit card", "rewards", "travel"],
    "results": [...]
  }
}
```

---

#### POST /search/voice

Search for products using voice input.

**Request:**
```
Content-Type: multipart/form-data

audio: <file>
user_id: user_123 (optional)
```

**Response:**
```json
{
  "success": true,
  "data": {
    "transcription": "I need a credit card with good travel rewards",
    "results": [...]
  }
}
```

---

### Recommendations

#### GET /recommendations/{user_id}

Get personalized product recommendations for a user.

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `user_id` | string | The user's unique identifier |

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `category` | string | No | Filter by category |
| `limit` | integer | No | Number of recommendations (default: 5) |
| `include_explanation` | boolean | No | Include explanations (default: false) |

**Response:**
```json
{
  "success": true,
  "data": {
    "recommendations": [
      {
        "product": {
          "id": "prod_002",
          "name": "GrowthMax IRA",
          "category": "retirement",
          "price": 500
        },
        "match_score": 0.92,
        "reasons": [
          "Matches your moderate risk tolerance",
          "Within your budget range",
          "Aligns with your retirement goals"
        ]
      }
    ],
    "profile_summary": {
      "risk_tolerance": "moderate",
      "investment_goals": ["retirement", "growth"],
      "budget_range": [0, 1000]
    }
  }
}
```

---

#### POST /recommendations/feedback

Submit feedback on a recommendation.

**Request Body:**
```json
{
  "user_id": "user_123",
  "product_id": "prod_002",
  "recommendation_id": "rec_456",
  "feedback_type": "helpful",
  "rating": 5,
  "comment": "Great suggestion, exactly what I was looking for"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "feedback_id": "fb_789",
    "message": "Thank you for your feedback"
  }
}
```

---

### Products

#### GET /products/{product_id}

Get detailed information about a product.

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `product_id` | string | The product's unique identifier |

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "prod_001",
    "name": "SafeStart Savings Account",
    "description": "A beginner-friendly savings account with competitive rates",
    "category": "savings",
    "subcategory": "high-yield",
    "price": 0,
    "features": [
      {
        "name": "APY",
        "value": "4.5%"
      },
      {
        "name": "Minimum Balance",
        "value": "$0"
      },
      {
        "name": "FDIC Insured",
        "value": "Yes"
      }
    ],
    "pros": [
      "No minimum balance required",
      "Competitive interest rate",
      "Easy online access"
    ],
    "cons": [
      "Limited branch locations",
      "No physical checks"
    ],
    "risk_level": "low",
    "suitable_for": ["beginners", "conservative investors"],
    "provider": {
      "name": "SafeBank",
      "rating": 4.5
    }
  }
}
```

---

#### GET /products/{product_id}/alternatives

Get alternative products within specified constraints.

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `product_id` | string | The reference product ID |

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `max_price` | number | No | Maximum price for alternatives |
| `same_category` | boolean | No | Limit to same category (default: true) |
| `limit` | integer | No | Number of alternatives (default: 5) |

**Response:**
```json
{
  "success": true,
  "data": {
    "reference_product": {
      "id": "prod_001",
      "name": "SafeStart Savings Account",
      "price": 0
    },
    "alternatives": [
      {
        "product": {
          "id": "prod_010",
          "name": "ValueSaver Account",
          "price": 0
        },
        "similarity_score": 0.88,
        "comparison": {
          "better": ["Higher APY (4.8%)"],
          "worse": ["Higher minimum balance ($100)"],
          "same": ["FDIC insured", "Online access"]
        }
      }
    ],
    "upgrade_options": [...],
    "downgrade_options": [...]
  }
}
```

---

#### GET /products/{product_id}/explanation

Get an explanation of why a product matches user criteria.

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `product_id` | string | The product ID |

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `user_id` | string | Yes | User ID for personalized explanation |
| `query` | string | No | Original search query for context |

**Response:**
```json
{
  "success": true,
  "data": {
    "product_id": "prod_001",
    "explanation": {
      "summary": "This savings account is an excellent match for your needs as a beginner investor looking for safe options.",
      "match_factors": [
        {
          "factor": "Risk Level",
          "match": "high",
          "explanation": "Your profile indicates low risk tolerance, and this account is FDIC insured"
        },
        {
          "factor": "Budget",
          "match": "high",
          "explanation": "No minimum balance fits your flexible budget requirements"
        },
        {
          "factor": "Experience",
          "match": "high",
          "explanation": "Designed for beginners with simple, straightforward features"
        }
      ],
      "confidence": 0.92
    }
  }
}
```

---

### Users

#### GET /users/{user_id}/profile

Get user profile and preferences.

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "user_123",
    "profile": {
      "risk_tolerance": "moderate",
      "investment_experience": "beginner",
      "goals": ["retirement", "emergency_fund"],
      "budget_range": {
        "min": 0,
        "max": 5000
      },
      "preferred_categories": ["savings", "investments"]
    },
    "interaction_summary": {
      "total_searches": 45,
      "products_viewed": 120,
      "recommendations_rated": 15
    }
  }
}
```

---

#### PUT /users/{user_id}/profile

Update user profile and preferences.

**Request Body:**
```json
{
  "risk_tolerance": "moderate",
  "investment_experience": "intermediate",
  "goals": ["retirement", "growth"],
  "budget_range": {
    "min": 100,
    "max": 10000
  }
}
```

---

### Agent Operations

#### POST /agent/query

Send a query to the multi-agent system.

**Request Body:**
```json
{
  "query": "Compare savings accounts with the best interest rates",
  "user_id": "user_123",
  "context": {
    "previous_queries": ["safe investments"],
    "viewed_products": ["prod_001", "prod_002"]
  },
  "options": {
    "include_alternatives": true,
    "include_explanation": true
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "response": "Based on your interest in safe investments, here are the top savings accounts...",
    "products": [...],
    "alternatives": [...],
    "explanation": "...",
    "agents_used": ["search", "recommendation", "explainability"],
    "processing_time_ms": 1250
  }
}
```

---

#### POST /agent/workflow

Execute a specific agent workflow.

**Request Body:**
```json
{
  "workflow": "comprehensive_search",
  "input": {
    "query": "retirement planning options",
    "user_id": "user_123"
  }
}
```

**Available Workflows:**
- `comprehensive_search` - Full search with recommendations
- `product_comparison` - Compare multiple products
- `budget_optimization` - Find best options within budget
- `risk_assessment` - Assess products for user risk profile

---

### Learning System

#### POST /learning/interaction

Log a user interaction for learning.

**Request Body:**
```json
{
  "user_id": "user_123",
  "interaction_type": "click",
  "product_id": "prod_001",
  "context": {
    "search_query": "savings accounts",
    "position_in_results": 3
  }
}
```

---

#### GET /learning/metrics

Get learning system metrics (admin only).

**Response:**
```json
{
  "success": true,
  "data": {
    "total_interactions": 150000,
    "active_experiments": 3,
    "model_performance": {
      "precision": 0.85,
      "recall": 0.82,
      "f1_score": 0.83
    },
    "last_model_update": "2024-01-15T00:00:00Z"
  }
}
```

---

### Health & Monitoring

#### GET /health

Check API health status.

**Response:**
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

---

#### GET /metrics

Get Prometheus-compatible metrics.

---

## Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Invalid request parameters |
| `NOT_FOUND` | 404 | Resource not found |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Server error |
| `SERVICE_UNAVAILABLE` | 503 | External service unavailable |

---

## Rate Limiting

- **Standard endpoints**: 100 requests/minute
- **Search endpoints**: 30 requests/minute
- **Agent endpoints**: 20 requests/minute

Rate limit headers:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1705312200
```

---

## SDKs & Libraries

- **Python**: `pip install finfind-sdk`
- **JavaScript**: `npm install @finfind/sdk`

---

## Changelog

### v1.0.0 (2024-01-15)
- Initial API release
- Core search and recommendation endpoints
- Multi-agent query system
- Learning system integration

---

## Support

- **Email**: api-support@finfind.com
- **Documentation**: https://docs.finfind.com
- **Status Page**: https://status.finfind.com
