# FinFind 🔍💰

**AI-Powered Budget-Aware Product Discovery Platform**

FinFind helps users find products that match their needs *and* their budget using semantic search, personalized recommendations, and explainable AI.

---

## Features

- 🔎 **Smart Search** - Natural language queries ("laptop for coding under $500")
- 💵 **Budget-Aware** - Automatically filters by financial constraints
- 🤖 **Multi-Agent AI** - 4 specialized agents working together
- 💡 **Explainable** - Understand *why* products are recommended
- 🎤 **Voice Search** - Speak your query (Whisper)
- 📷 **Image Search** - Find similar products by photo (CLIP)

---

## Architecture

```
Frontend (Next.js) → FastAPI Backend → Multi-Agent System → Qdrant (Vector DB)
                                              ↓
                                    Groq LLM (Llama 3.3)
```

**Agents:**
| Agent | Purpose |
|-------|---------|
| SearchAgent | Semantic product search |
| RecommendationAgent | Personalized suggestions |
| ExplainabilityAgent | "Why this product?" |
| AlternativeAgent | Budget-friendly alternatives |

---

## Tech Stack

- **Backend**: Python, FastAPI
- **Frontend**: Next.js 14, React, TypeScript
- **Vector DB**: Qdrant Cloud
- **LLM**: Groq (Llama 3.3 70B)
- **Embeddings**: sentence-transformers/all-MiniLM-L6-v2
- **Voice**: Whisper
- **Vision**: CLIP

---

## Quick Start

### Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt

# Set environment variables in .env
python run.py
```

### Frontend
```bash
cd Frontend
npm install
npm run dev
```

---

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/search/products?q=...` | Search products |
| `GET /api/v1/recommendations/{user_id}` | Get recommendations |
| `GET /api/v1/products/{id}` | Product details |
| `POST /api/v1/multimodal/voice/search` | Voice search |
| `POST /api/v1/multimodal/image/search` | Image search |

---

## Environment Variables

```env
# Qdrant
QDRANT_URL=your-qdrant-url
QDRANT_API_KEY=your-api-key

# Groq LLM
GROQ_API_KEY=your-groq-key
GROQ_MODEL=llama-3.3-70b-versatile
```

---

*Built for the Vectors In Orbit Hackathon*
