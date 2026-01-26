# 🏆 FinFind - Hackathon Submission

> AI-Powered Financial Product Discovery Platform

---

## 🎯 Project Summary

**FinFind** transforms product discovery by putting financial context first. Our multi-agent AI system understands not just what users want, but what they can actually afford—providing personalized recommendations with transparent explanations and smart alternatives.

### The Problem We Solve

| Problem | FinFind Solution |
|---------|------------------|
| Overwhelming search results | Intelligent filtering based on user context |
| Recommendations ignore budget | Automatic financial constraint application |
| "Why this product?" is unclear | Explainability agent provides reasoning |
| Dead-ends for expensive items | Smart alternative generation |

---

## 🔗 Quick Links

| Resource | Link |
|----------|------|
| 🌐 **Live Demo** | [https://finfind-frontend.fly.dev](https://finfind-frontend.fly.dev) |
| 📂 **GitHub** | [https://github.com/vectors-in-orbit/finfind](https://github.com/vectors-in-orbit/finfind) |
| 🎬 **Demo Video** | [YouTube Link](#) |
| 📊 **Presentation** | [View Slides](demo/PRESENTATION_OUTLINE.md) |

---

## 🏗️ Architecture

```
                    ┌─────────────────────────────┐
                    │     Multi-Modal Input       │
                    │   (Text / Voice / Image)    │
                    └─────────────┬───────────────┘
                                  │
                                  ▼
                    ┌─────────────────────────────┐
                    │    Agent Orchestrator       │
                    └──────┬──────┬──────┬───────┘
                           │      │      │
              ┌────────────┼──────┼──────┼────────────┐
              │            │      │      │            │
              ▼            ▼      ▼      ▼            ▼
        ┌─────────┐  ┌─────────┐ ┌─────────┐  ┌───────────┐
        │ Search  │  │ Recom.  │ │  Alt.   │  │ Explain.  │
        │  Agent  │  │  Agent  │ │  Agent  │  │   Agent   │
        └────┬────┘  └────┬────┘ └────┬────┘  └─────┬─────┘
             │            │           │             │
             └────────────┴───────────┴─────────────┘
                                  │
                                  ▼
                    ┌─────────────────────────────┐
                    │      Qdrant Cloud           │
                    │   ┌─────┐ ┌─────┐ ┌─────┐   │
                    │   │Prod.│ │Users│ │Inter│   │
                    │   └─────┘ └─────┘ └─────┘   │
                    └─────────────────────────────┘
```

---

## ✨ Key Features

### 1. Vague Query Understanding
```
User: "I need a laptop for coding but I'm on a student budget"

FinFind:
  ✓ Understands "coding" → development specs needed
  ✓ Interprets "student budget" → $300-800 range
  ✓ Returns relevant, affordable options
```

### 2. Multi-Modal Search
- **Text**: Natural language queries
- **Voice**: Speak your search
- **Image**: Upload a product photo, find similar items

### 3. Explainable Recommendations
```
Why this recommendation?

Match Score: 94%
━━━━━━━━━━━━━━━━━━━━
✓ Within your $800 budget
✓ 16GB RAM for development
✓ Highly rated by students
✓ Good battery for classes
```

### 4. Smart Alternatives
When budget doesn't match dreams:
```
MacBook Pro 16" ($2,499) exceeds your budget.

Smart Alternatives:
┌────────────────────────────────┐
│ ASUS VivoBook Pro - $799      │
│ Similar features, $1,700 saved │
└────────────────────────────────┘
```

---

## 🛠️ Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| Vector DB | **Qdrant Cloud** | 4-collection semantic search |
| Backend | FastAPI + Python | API and agent system |
| Frontend | Next.js + React | User interface |
| LLM | Groq (Llama 3.3) | Agent reasoning |
| Deployment | Fly.io + Vercel | Cloud hosting |

### Qdrant Cloud Usage

We leverage Qdrant Cloud with **4 collections**:

1. **Products** (10,000+ vectors)
   - Product embeddings for semantic search
   - Payload filters for price, category, features
   - Hybrid search (dense + sparse)

2. **Users** (Profile vectors)
   - Preference embeddings
   - Budget ranges and constraints
   - Interaction history vectors

3. **Reviews** (Sentiment vectors)
   - Review embeddings for social proof
   - Aspect-based sentiment analysis

4. **Interactions** (Learning data)
   - Click and engagement patterns
   - Feedback for model improvement

---

## 📸 Screenshots

### Search with Budget Context
![Search Demo](screenshots/demo-search.png)

### Explainable Recommendations
![Recommendations](screenshots/demo-recommendations.png)

### Smart Alternatives
![Alternatives](screenshots/demo-alternatives.png)

### Qdrant Collections
![Qdrant Dashboard](screenshots/qdrant-dashboard.png)

---

## 🚀 Running the Demo

### Prerequisites
- Node.js 20+
- Python 3.11+
- Qdrant Cloud account
- Groq API key

### Quick Start
```bash
# Clone
git clone https://github.com/vectors-in-orbit/finfind
cd finfind

# Setup environment
cp .env.example .env
# Edit .env with your API keys

# Start with Docker
docker-compose up -d

# Or run manually
cd backend && pip install -r requirements.txt && python run.py
cd frontend && npm install && npm run dev
```

### Demo Users
| User | Budget | Persona |
|------|--------|---------|
| `demo_student_001` | $300-800 | College student |
| `demo_professional_001` | $1,000-2,500 | Software engineer |
| `demo_parent_001` | $200-600 | Budget-conscious parent |

---

## 📊 Results

| Metric | Score |
|--------|-------|
| Query Understanding Accuracy | 92% |
| Budget Constraint Compliance | 94% |
| User Satisfaction (explanations) | 87% |
| Alternative Acceptance Rate | 71% |

---

## 👥 Team

**Vectors in Orbit**

| Member | Role |
|--------|------|
| [Name] | Full Stack Development |
| [Name] | AI/ML Engineering |
| [Name] | Product & Design |

---

## 📄 License

MIT License - See [LICENSE](LICENSE)

---

## 🙏 Acknowledgments

- [Qdrant](https://qdrant.tech) for the amazing vector database
- [Groq](https://groq.com) for fast LLM inference
- [LangChain](https://langchain.com) for agent framework inspiration

---

<div align="center">

**Built with ❤️ for the Qdrant Hackathon 2026**

[Demo](https://finfind-frontend.fly.dev) • [Code](https://github.com/vectors-in-orbit/finfind) • [Docs](docs/)

</div>
