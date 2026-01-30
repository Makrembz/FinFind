# FinFind 🔍💰

**AI-Powered Budget-Aware Product Discovery Platform**

> Built for the **Vectors In Orbit Hackathon** - An intelligent shopping assistant that combines semantic search, personalized recommendations, and explainable AI to help users find products that match both their needs and their budget.

---

## 📋 Table of Contents

- [Project Overview](#-project-overview)
- [Key Features](#-key-features)
- [Technologies Used](#-technologies-used)
- [Project Architecture](#-project-architecture)
- [Qdrant Integration](#-qdrant-integration)
- [Setup & Installation](#-setup--installation)
- [Usage Examples](#-usage-examples)
- [API Reference](#-api-reference)
- [Project Structure](#-project-structure)
- [Contributing](#-contributing)

---

## 🎯 Project Overview

### The Problem

Online shoppers face several critical challenges:

| Challenge | Impact |
|-----------|--------|
| **Information Overload** | Thousands of results with no personalization |
| **Budget Ignorance** | Recommendations don't consider financial constraints |
| **Black-Box Recommendations** | Users don't understand why products are suggested |
| **Dead-End Searches** | No alternatives offered when budget doesn't match desires |

### Our Solution

FinFind is an **AI-powered product discovery platform** that addresses these challenges through:

- **Semantic Search**: Understands natural language queries (e.g., "I need a laptop for coding under $500")
- **Budget-Aware Filtering**: Automatically applies financial constraints to results
- **Explainable AI**: Provides transparent reasoning for every recommendation
- **Smart Alternatives**: Suggests budget-friendly substitutes when needed
- **Multimodal Input**: Search via text, voice, or image

### Objectives

1. **Enhance Product Discovery** - Use vector similarity search to find semantically relevant products
2. **Personalize Recommendations** - Learn from user behavior and preferences
3. **Ensure Transparency** - Explain every recommendation with clear reasoning
4. **Support Multimodal Search** - Enable voice and image-based product search
5. **Respect Budget Constraints** - Always consider user's financial limitations

---

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| 🔎 **Smart Search** | Natural language queries with semantic understanding |
| 💵 **Budget-Aware** | Automatic filtering by financial constraints |
| 🤖 **Multi-Agent AI** | 4 specialized agents collaborating for optimal results |
| 💡 **Explainable** | Clear reasoning for every recommendation |
| 🎤 **Voice Search** | Speak your query using Whisper speech recognition |
| 📷 **Image Search** | Find similar products by uploading a photo |
| 📈 **Trending Products** | Real-time trending items based on user interactions |
| 🕐 **Recently Viewed** | Track and display browsing history |
| 🔗 **Product Sharing** | Share products via social media |

---

## 🛠 Technologies Used

### Backend

| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.10+ | Core programming language |
| FastAPI | ≥0.109.0 | Web framework for REST APIs |
| Uvicorn | ≥0.27.0 | ASGI server |
| Pydantic | ≥2.10.0 | Data validation |
| Qdrant Client | ≥1.12.0 | Vector database client |
| LangChain | ≥0.3.0 | LLM orchestration framework |
| LangGraph | ≥0.2.0 | Multi-agent workflow graphs |
| Sentence-Transformers | ≥3.0.0 | Text embeddings |
| Groq SDK | ≥0.2.0 | LLM API integration |
| Pytest | ≥8.0.0 | Testing framework |

### Frontend

| Technology | Version | Purpose |
|------------|---------|---------|
| Next.js | 16.1.4 | React framework with SSR |
| React | 19.2.3 | UI component library |
| TypeScript | ^5 | Type-safe JavaScript |
| TailwindCSS | ^4 | Utility-first CSS framework |
| Radix UI | Various | Accessible UI components |
| React Query | 5.90.20 | Server state management |
| Axios | 1.13.3 | HTTP client |
| Lucide React | 0.563.0 | Icon library |
| Jest | 30.2.0 | Testing framework |

### AI/ML Services

| Service | Purpose |
|---------|---------|
| **Qdrant Cloud** | Vector database for semantic search |
| **Groq (Llama 3.3 70B Versatile)** | Large language model for AI agents |
| **Sentence-Transformers (all-MiniLM-L6-v2)** | 384-dimensional text embeddings |
| **OpenAI Whisper** | Voice-to-text transcription |
| **CLIP** | Image similarity search |

### DevOps & Deployment

| Technology | Purpose |
|------------|---------|
| Docker | Containerization |
| Docker Compose | Multi-container orchestration |
| Fly.io | Backend deployment |
| Vercel | Frontend deployment |
| Railway | Alternative deployment |

---

## 🏗 Project Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         FRONTEND (Next.js 16)                           │
│    ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│    │   Text   │  │  Voice   │  │  Image   │  │ Filters  │              │
│    │  Search  │  │  Input   │  │  Upload  │  │& Sorting │              │
│    └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘              │
└─────────┼─────────────┼─────────────┼─────────────┼────────────────────┘
          │             │             │             │
          └─────────────┴──────┬──────┴─────────────┘
                               │ REST API (JSON)
┌──────────────────────────────▼──────────────────────────────────────────┐
│                         BACKEND (FastAPI)                                │
│  ┌────────────────────────────────────────────────────────────────┐     │
│  │                    AGENT ORCHESTRATOR                           │     │
│  │                                                                 │     │
│  │   ┌─────────────┐   ┌─────────────────┐   ┌─────────────────┐  │     │
│  │   │   Search    │   │ Recommendation  │   │ Explainability  │  │     │
│  │   │    Agent    │   │     Agent       │   │     Agent       │  │     │
│  │   │             │   │                 │   │                 │  │     │
│  │   │ - Semantic  │   │ - User prefs    │   │ - Why this?     │  │     │
│  │   │   search    │   │ - Budget match  │   │ - Feature       │  │     │
│  │   │ - Filters   │   │ - Personalized  │   │   highlights    │  │     │
│  │   └──────┬──────┘   └────────┬────────┘   └────────┬────────┘  │     │
│  │          │                   │                     │           │     │
│  │          └───────────────────┼─────────────────────┘           │     │
│  │                              ▼                                 │     │
│  │               ┌──────────────────────────┐                     │     │
│  │               │   Alternative Agent      │                     │     │
│  │               │                          │                     │     │
│  │               │ - Budget-friendly opts   │                     │     │
│  │               │ - Similar but cheaper    │                     │     │
│  │               └──────────────────────────┘                     │     │
│  └─────────────────────────────┬──────────────────────────────────┘     │
└────────────────────────────────┼────────────────────────────────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  QDRANT CLOUD   │    │   GROQ LLM      │    │   EMBEDDINGS    │
│  (Vector DB)    │    │  (Llama 3.3)    │    │  (MiniLM-L6)    │
│                 │    │                 │    │                 │
│ • products      │    │ • Agent logic   │    │ • 384-dim       │
│ • user_profiles │    │ • Reasoning     │    │ • Semantic      │
│ • reviews       │    │ • Explanations  │    │   similarity    │
│ • interactions  │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Multi-Agent System

FinFind uses **4 specialized AI agents** that collaborate to provide comprehensive product recommendations:

| Agent | Role | Capabilities |
|-------|------|--------------|
| **SearchAgent** | Product Discovery | Semantic search with budget filters, category matching |
| **RecommendationAgent** | Personalization | User preference learning, behavior-based suggestions |
| **ExplainabilityAgent** | Transparency | Generate human-readable explanations for recommendations |
| **AlternativeAgent** | Budget Solutions | Find cheaper alternatives, trade-off analysis |

**Agent Communication**: Agents use A2A (Agent-to-Agent) protocol via LangGraph for complex queries requiring multiple capabilities.

---

## 🔷 Qdrant Integration

### Overview

**Qdrant Cloud** serves as the core vector database enabling semantic search and personalization. We leverage Qdrant's high-performance similarity search to match user queries with products based on meaning, not just keywords.

### Collections

We maintain 4 Qdrant collections, each serving a specific purpose:

| Collection | Purpose | Vector Dimensions | Payload Fields |
|------------|---------|-------------------|----------------|
| `products` | Product catalog with embeddings | 384 | name, description, price, category, brand, image_url |
| `user_profiles` | User preferences & budget info | 384 | user_id, budget_range, favorite_categories, interests |
| `reviews` | Product reviews with sentiment | 384 | product_id, rating, text, sentiment_score |
| `user_interactions` | Behavior tracking for learning | 384 | user_id, product_id, action_type, timestamp |

### How Qdrant Powers Our Features

#### 1. Semantic Product Search

```python
# Convert user query to embedding
query_embedding = embedding_model.encode("wireless headphones under $100")

# Search with filters
results = qdrant_client.search(
    collection_name="products",
    query_vector=query_embedding,
    query_filter=Filter(
        must=[
            FieldCondition(key="price", range=Range(lte=100.0)),
            FieldCondition(key="category", match=MatchValue(value="Electronics"))
        ]
    ),
    limit=10
)
```

#### 2. Personalized Recommendations

```python
# Get user's preference vector from profile
user_profile = qdrant_client.retrieve(
    collection_name="user_profiles",
    ids=[user_id]
)

# Find products similar to user's preferences
recommendations = qdrant_client.search(
    collection_name="products",
    query_vector=user_profile.vector,
    query_filter=Filter(
        must=[FieldCondition(key="price", range=Range(lte=user_budget))]
    ),
    limit=20
)
```

#### 3. Finding Alternatives

```python
# Get the original product's vector
original_product = qdrant_client.retrieve(
    collection_name="products",
    ids=[product_id]
)

# Find similar but cheaper products
alternatives = qdrant_client.search(
    collection_name="products",
    query_vector=original_product.vector,
    query_filter=Filter(
        must=[
            FieldCondition(key="price", range=Range(lt=original_product.price)),
            FieldCondition(key="category", match=MatchValue(value=original_product.category))
        ]
    ),
    limit=5
)
```

#### 4. Learning from Interactions

```python
# Log user interaction
interaction_vector = embedding_model.encode(f"user viewed {product_name}")

qdrant_client.upsert(
    collection_name="user_interactions",
    points=[PointStruct(
        id=interaction_id,
        vector=interaction_vector,
        payload={
            "user_id": user_id,
            "product_id": product_id,
            "action": "view",
            "timestamp": datetime.now().isoformat()
        }
    )]
)
```

### Why Qdrant?

| Feature | Benefit for FinFind |
|---------|---------------------|
| **Fast Similarity Search** | Sub-second query responses for real-time search |
| **Filtering** | Combine vector search with exact filters (price, category) |
| **Payload Storage** | Store product metadata alongside vectors |
| **Cloud Hosted** | Managed infrastructure, no maintenance overhead |
| **Scalability** | Handle growing product catalog and user base |

---

## 🚀 Setup & Installation

### Prerequisites

- **Python** 3.10 or higher
- **Node.js** 18.x or higher
- **npm** or **yarn**
- **Git**

### Required API Keys

1. **Qdrant Cloud**: Create account at [cloud.qdrant.io](https://cloud.qdrant.io)
2. **Groq**: Get API key at [console.groq.com](https://console.groq.com)

### Step 1: Clone the Repository

```bash
git clone https://github.com/your-username/finfind.git
cd finfind
```

### Step 2: Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
```

#### Configure Environment Variables

Edit the `.env` file with your API keys:

```env
# Qdrant Configuration
QDRANT_URL=https://your-cluster.qdrant.io:6333
QDRANT_API_KEY=your-qdrant-api-key

# Groq LLM Configuration
GROQ_API_KEY=your-groq-api-key
GROQ_MODEL=llama-3.3-70b-versatile

# Application Settings
DEBUG=true
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:3000

# Optional: Redis for caching
REDIS_URL=redis://localhost:6379
```

#### Start the Backend Server

```bash
python run.py
```

The API will be available at `http://localhost:8000`

### Step 3: Frontend Setup

```bash
# Navigate to frontend directory (from project root)
cd Frontend

# Install dependencies
npm install

# Create environment file
cp .env.example .env.local
```

#### Configure Frontend Environment

Edit `.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

#### Start the Development Server

```bash
npm run dev
```

The frontend will be available at `http://localhost:3000`

### Step 4: Generate Sample Data (Optional)

```bash
cd backend
python -m data_generation.run_generation
```

---

## 📖 Usage Examples

### 1. Basic Text Search

Search for products using natural language:

```bash
# Search for laptops under $800
curl "http://localhost:8000/api/v1/search/products?q=laptop%20for%20programming&max_price=800"
```

**Response:**
```json
{
  "results": [
    {
      "id": "prod_123",
      "name": "Dell XPS 13 Developer Edition",
      "price": 749.99,
      "description": "Lightweight laptop perfect for coding...",
      "relevance_score": 0.92
    }
  ],
  "total": 15,
  "explanation": "Found 15 laptops suitable for programming within your $800 budget"
}
```

### 2. Get Personalized Recommendations

```bash
# Get recommendations for a user
curl "http://localhost:8000/api/v1/recommendations/user_123"
```

### 3. Voice Search

```bash
# Upload audio file for voice search
curl -X POST "http://localhost:8000/api/v1/multimodal/voice/search" \
  -F "audio=@query.wav"
```

### 4. Image Search

```bash
# Upload image to find similar products
curl -X POST "http://localhost:8000/api/v1/multimodal/image/search" \
  -F "image=@product.jpg"
```

### 5. Get Product Alternatives

```bash
# Find cheaper alternatives to a product
curl "http://localhost:8000/api/v1/products/prod_123/alternatives?max_price=500"
```

### 6. Frontend Usage

1. **Open the app** at `http://localhost:3000`
2. **Enter a search query** like "wireless earbuds for running"
3. **Apply filters** for price range, category, or brand
4. **Click on a product** to see details and explanations
5. **View alternatives** if the product is above budget

---

## 📚 API Reference

### Search Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/search/products` | Search products with semantic matching |
| `GET` | `/api/v1/search/suggestions` | Get search autocomplete suggestions |

**Query Parameters:**
- `q` (string): Search query
- `min_price` (float): Minimum price filter
- `max_price` (float): Maximum price filter
- `category` (string): Category filter
- `brand` (string): Brand filter
- `sort_by` (string): Sort field (price, relevance, rating)
- `limit` (int): Number of results (default: 20)

### Recommendation Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/recommendations/{user_id}` | Get personalized recommendations |
| `GET` | `/api/v1/recommendations/trending` | Get trending products |

### Product Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/products/{id}` | Get product details |
| `GET` | `/api/v1/products/{id}/alternatives` | Get cheaper alternatives |
| `GET` | `/api/v1/products/{id}/explanation` | Get AI explanation |

### Multimodal Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/multimodal/voice/search` | Voice-based search |
| `POST` | `/api/v1/multimodal/image/search` | Image-based search |

---

## 📁 Project Structure

```
FinFind/
├── backend/
│   ├── app/
│   │   ├── agents/              # AI Agent implementations
│   │   │   ├── search_agent/    # Semantic search logic
│   │   │   ├── recommendation_agent/
│   │   │   ├── explainability_agent/
│   │   │   ├── alternative_agent/
│   │   │   ├── orchestrator/    # Agent coordination
│   │   │   └── tools/           # Shared agent tools
│   │   ├── api/
│   │   │   ├── routes/          # API endpoints
│   │   │   ├── services/        # Business logic
│   │   │   └── models.py        # Pydantic models
│   │   ├── multimodal/          # Voice & image processing
│   │   ├── learning/            # User behavior learning
│   │   └── config.py            # Configuration
│   ├── data_generation/         # Sample data generation
│   ├── tests/                   # Unit & integration tests
│   ├── requirements.txt         # Python dependencies
│   └── run.py                   # Application entry point
│
├── Frontend/
│   ├── src/
│   │   ├── app/                 # Next.js pages
│   │   ├── components/          # React components
│   │   │   ├── ui/              # Reusable UI components
│   │   │   ├── search/          # Search components
│   │   │   └── product/         # Product components
│   │   ├── hooks/               # Custom React hooks
│   │   ├── lib/                 # Utilities & API client
│   │   └── types/               # TypeScript definitions
│   ├── public/                  # Static assets
│   ├── package.json             # Node dependencies
│   └── tsconfig.json            # TypeScript config
│
├── docs/                        # Documentation
├── scripts/                     # Deployment scripts
├── docker-compose.yml           # Docker orchestration
└── README.md                    # This file
```

---

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Workflow

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes
4. Run tests: `pytest` (backend) / `npm test` (frontend)
5. Commit changes: `git commit -m 'Add amazing feature'`
6. Push to branch: `git push origin feature/amazing-feature`
7. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

- **Qdrant** for the powerful vector database
- **Groq** for fast LLM inference
- **Hugging Face** for open-source embedding models
- **Vectors In Orbit Hackathon** organizers

---

<p align="center">
  Built with ❤️ for the <strong>Vectors In Orbit Hackathon</strong>
</p>
