# FinFind - Technical Report

**AI-Powered Financial Product Discovery Platform**

---

## 1. Problem Statement & Solution

### The Problem

Online shoppers face several challenges when searching for products:

| Challenge | Impact |
|-----------|--------|
| **Information Overload** | Thousands of results with no personalization |
| **Budget Ignorance** | Recommendations don't consider financial constraints |
| **Black-Box Recommendations** | Users don't understand why products are suggested |
| **Dead-End Searches** | No alternatives offered when budget doesn't match desires |

### Our Solution: FinFind

FinFind is an **AI-powered product discovery platform** that combines:

- **Semantic Search**: Understands natural language queries ("I need a laptop for coding under $500")
- **Budget-Aware Filtering**: Automatically applies financial constraints
- **Explainable AI**: Transparent reasoning for every recommendation
- **Smart Alternatives**: Suggests budget-friendly substitutes when needed
- **Multimodal Input**: Search via text, voice, or image

---

## 2. Architecture

### 2.1 System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (Next.js)                       │
│         Text Search │ Voice Input │ Image Upload │ Filters       │
└────────────────────────────────┬────────────────────────────────┘
                                 │ REST API
┌────────────────────────────────▼────────────────────────────────┐
│                      FastAPI Backend                             │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              Agent Orchestrator                          │    │
│  │  ┌───────────┐ ┌──────────────┐ ┌──────────────────┐    │    │
│  │  │  Search   │ │Recommendation│ │  Explainability  │    │    │
│  │  │  Agent    │ │    Agent     │ │     Agent        │    │    │
│  │  └─────┬─────┘ └──────┬───────┘ └────────┬─────────┘    │    │
│  │        │              │                  │               │    │
│  │  ┌─────▼──────────────▼──────────────────▼─────┐        │    │
│  │  │           Alternative Agent                  │        │    │
│  │  └──────────────────────────────────────────────┘        │    │
│  └─────────────────────────┬───────────────────────────────┘    │
└────────────────────────────┼────────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  Qdrant Cloud │    │   Groq LLM   │    │  Embeddings  │
│  (Vector DB)  │    │ (Llama 3.3)  │    │ (MiniLM-L6)  │
└──────────────┘    └──────────────┘    └──────────────┘
```

### 2.2 Multi-Agent System

We use **4 specialized AI agents**, each with a specific role:

| Agent | Role | Key Capability |
|-------|------|----------------|
| **SearchAgent** | Product discovery | Semantic search with budget filters |
| **RecommendationAgent** | Personalization | User-preference matching |
| **ExplainabilityAgent** | Transparency | "Why this product?" explanations |
| **AlternativeAgent** | Budget solutions | Find cheaper alternatives |

**Agent Communication**: Agents communicate via A2A (Agent-to-Agent) protocol for complex queries requiring multiple capabilities.

### 2.3 Qdrant Integration

Qdrant serves as our **vector database** for semantic search and personalization.

**Collections:**

| Collection | Purpose | Vector Dim |
|------------|---------|------------|
| `products` | Product catalog with embeddings | 384 |
| `user_profiles` | User preferences & budget info | 384 |
| `reviews` | Product reviews with sentiment | 384 |
| `user_interactions` | Behavior tracking for learning | 384 |

**Key Operations:**

```python
# Semantic Search with Filters
results = qdrant.semantic_search(
    collection="products",
    query_vector=embedding,
    filters={"price": {"lte": max_budget}, "category": category},
    limit=10
)

# MMR Search for Diversity
results = qdrant.mmr_search(
    collection="products",
    query_vector=embedding,
    diversity=0.3,  # Balance relevance vs diversity
    limit=10
)
```

**Why Qdrant?**
- Fast semantic similarity search
- Payload filtering (price, category, brand)
- MMR support for diverse results
- Cloud-hosted for scalability

---

## 3. Data Pipeline

### 3.1 Data Generation Flow

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Generators     │ ──▶ │  Embeddings     │ ──▶ │  Qdrant Upload  │
│  (Synthetic)    │     │  (MiniLM-L6)    │     │  (4 Collections)│
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

### 3.2 Data Generation

We generate realistic synthetic data for demonstration:

| Data Type | Count | Key Attributes |
|-----------|-------|----------------|
| **Products** | 500 | Title, description, price, category, brand, rating |
| **Users** | 100 | Persona type, budget range, preferences |
| **Reviews** | 1,200 | Rating, sentiment, text |
| **Interactions** | 2,500 | Views, clicks, purchases |

**Product Categories Distribution:**
- Electronics: 25%
- Fashion: 20%
- Home & Kitchen: 15%
- Sports & Fitness: 13%
- Beauty: 15%
- Books & Media: 12%

**User Budget Personas:**
- Tight Budget: 25%
- Moderate: 40%
- Comfortable: 25%
- Luxury: 10%

### 3.3 Embedding Pipeline

```python
# Text to Vector Pipeline
text = "Laptop 16GB RAM for programming"
     ↓
embedding = sentence_transformer.encode(text)  # [384 dimensions]
     ↓
normalized = l2_normalize(embedding)
     ↓
qdrant.upsert(collection="products", vector=normalized, payload={...})
```

**Model:** `sentence-transformers/all-MiniLM-L6-v2`
- Dimension: 384
- Fast inference
- Good semantic understanding

---

## 4. Project Timeline

### ✅ Work Completed

| Phase | Tasks | Status |
|-------|-------|--------|
| **Planning** | Problem definition, architecture design | ✅ Done |
| **Data Layer** | Qdrant setup, data generation pipeline, embeddings | ✅ Done |
| **Backend Core** | FastAPI setup, API routes (search, products, users, recommendations) | ✅ Done |
| **Agent System** | 4 agents implemented, orchestrator, A2A communication | ✅ Done |
| **Search** | Semantic search, filters, categories, brands | ✅ Done |
| **Recommendations** | Personalized recommendations, budget filtering | ✅ Done |
| **Explainability** | Match explanations, financial fit analysis | ✅ Done |
| **Alternatives** | Budget-friendly alternatives finder | ✅ Done |
| **Multimodal** | Voice search (Whisper), Image search (CLIP) | ✅ Done |
| **Frontend** | Next.js UI, search interface, product display | ✅ Done |
| **LLM Integration** | Groq (Llama 3.3) for agent reasoning | ✅ Done |

### 🔄 Work In Progress

| Task | Description | Progress |
|------|-------------|----------|
| **API Testing** | Comprehensive endpoint validation | 90% |
| **Agent Refinement** | Improving tool execution | 80% |
| **UI Polish** | Better UX for multimodal features | 70% |

### 📋 Future Work

| Task | Priority | Description |
|------|----------|-------------|
| **Learning System** | High | Implement feedback loop for better recommendations |
| **A/B Testing** | Medium | Compare recommendation strategies |
| **Real Data** | High | Replace synthetic with real product data |
| **Performance** | Medium | Optimize query latency |
| **Mobile App** | Low | React Native mobile version |

---

## 5. Technology Stack

| Component | Technology |
|-----------|------------|
| **Vector Database** | Qdrant Cloud |
| **Backend** | Python, FastAPI |
| **Frontend** | Next.js 14, React, TypeScript |
| **LLM** | Groq (Llama 3.3 70B) |
| **Embeddings** | sentence-transformers/all-MiniLM-L6-v2 |
| **Voice** | Whisper |
| **Vision** | CLIP |

---

## 6. Key Differentiators

1. **Budget-First Design**: Every search and recommendation respects user's financial constraints
2. **Explainable AI**: Users understand why products are recommended
3. **Multi-Agent Collaboration**: Specialized agents work together for complex queries
4. **Multimodal Search**: Text, voice, and image input supported
5. **Qdrant-Powered**: Fast semantic search with advanced filtering

---

*FinFind - Making product discovery smarter, more personal, and budget-aware.*
