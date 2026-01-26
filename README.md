# 🔍 FinFind - AI-Powered Financial Product Discovery

<div align="center">

![FinFind Logo](docs/assets/logo.png)

**Intelligent financial product recommendations powered by multi-agent AI**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Next.js 14](https://img.shields.io/badge/Next.js-14-black.svg)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

[Demo](https://finfind.demo.com) • [Documentation](docs/) • [API Reference](docs/API.md) • [Contributing](CONTRIBUTING.md)

</div>

---

## 📖 Overview

FinFind is an intelligent financial product discovery platform that uses a sophisticated multi-agent AI system to help users find, compare, and understand financial products based on their unique needs and constraints.

### ✨ Key Features

- **🤖 Multi-Agent Architecture**: Specialized AI agents for search, recommendations, alternatives, and explanations
- **🔍 Semantic Search**: Natural language product search with context understanding
- **💡 Smart Recommendations**: Personalized recommendations based on user profiles and preferences
- **📊 Product Alternatives**: Find similar products within your budget constraints
- **📝 Explainability**: Clear explanations of why products match your needs
- **🎤 Multimodal Input**: Support for voice and image-based search
- **📈 Continuous Learning**: System improves based on user interactions

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              Frontend (Next.js)                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │
│  │   Search    │  │  Products   │  │   Profile   │  │  Results    │   │
│  │  Component  │  │    View     │  │    Page     │  │   Display   │   │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           FastAPI Backend                               │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    Agent Orchestrator                            │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐   │   │
│  │  │  Search  │ │  Recom.  │ │   Alt.   │ │  Explainability  │   │   │
│  │  │  Agent   │ │  Agent   │ │  Agent   │ │      Agent       │   │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                     MCP Tools Layer                              │   │
│  │  Search Tools │ Recommendation Tools │ Explainability Tools    │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    Learning System                               │   │
│  │  Interaction Logger │ Feedback Analyzer │ Model Updater         │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          External Services                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │
│  │   Qdrant    │  │    Groq     │  │  Embedding  │  │   Voice/    │   │
│  │  (Vectors)  │  │   (LLM)     │  │   Service   │  │   Image     │   │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- Docker (optional, recommended)
- Qdrant Cloud account or local Qdrant instance
- Groq API key

### Local Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/finfind.git
   cd finfind
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Start with Docker (Recommended)**
   ```bash
   docker-compose up -d
   ```

   Or start services individually:

4. **Backend Setup**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   python run.py
   ```

5. **Frontend Setup**
   ```bash
   cd Frontend
   npm install
   npm run dev
   ```

6. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

---

## 📁 Project Structure

```
FinFind/
├── backend/
│   ├── app/
│   │   ├── agents/           # Multi-agent system
│   │   │   ├── search_agent/
│   │   │   ├── recommendation_agent/
│   │   │   ├── alternative_agent/
│   │   │   ├── explainability_agent/
│   │   │   ├── orchestrator/
│   │   │   └── mcp/          # Model Context Protocol tools
│   │   ├── api/              # FastAPI routes and services
│   │   ├── learning/         # Continuous learning system
│   │   └── multimodal/       # Voice and image processing
│   ├── data_generation/      # Synthetic data generation
│   └── tests/                # Backend tests
├── Frontend/
│   ├── src/
│   │   ├── app/              # Next.js pages
│   │   ├── components/       # React components
│   │   ├── hooks/            # Custom React hooks
│   │   ├── lib/              # Utilities and API client
│   │   └── types/            # TypeScript definitions
│   └── __tests__/            # Frontend tests
├── docs/                     # Documentation
├── scripts/                  # Deployment scripts
└── docker-compose.yml        # Docker configuration
```

---

## 🤖 Agent System

### Search Agent
Handles natural language product search with semantic understanding.
- Interprets vague queries ("something safe for beginners")
- Applies financial filters and constraints
- Supports multimodal input (voice, image)

### Recommendation Agent
Provides personalized product recommendations.
- Analyzes user financial profiles
- Calculates affordability matching
- Ranks products by user constraints

### Alternative Agent
Finds product alternatives within constraints.
- Similar products in different price ranges
- Category-based alternatives
- Upgrade and downgrade paths

### Explainability Agent
Generates clear explanations for recommendations.
- Similarity explanations
- Financial fit analysis
- Natural language summaries

---

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GROQ_API_KEY` | Groq API key for LLM | Yes |
| `QDRANT_URL` | Qdrant cluster URL | Yes |
| `QDRANT_API_KEY` | Qdrant API key | Yes |
| `COLLECTION_NAME` | Product collection name | No |
| `ENVIRONMENT` | development/production | No |
| `LOG_LEVEL` | Logging level | No |

See [.env.example](.env.example) for all configuration options.

---

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest tests/ -v --cov=app
```

### Frontend Tests
```bash
cd Frontend
npm test
npm run test:coverage
```

### E2E Tests
```bash
cd Frontend
npm run test:e2e
```

---

## 🚢 Deployment

### Docker
```bash
# Development
docker-compose up -d

# Production
docker-compose -f docker-compose.prod.yml up -d
```

### Platform Deployments

- **Fly.io**: `./scripts/deploy-fly.sh`
- **Railway**: Configure via `railway.toml`
- **Render**: Deploy via `render.yaml`
- **Vercel** (Frontend): Configure via `vercel.json`

See [Deployment Guide](docs/DEPLOYMENT.md) for detailed instructions.

---

## 📊 API Reference

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/search` | Semantic product search |
| POST | `/search/image` | Image-based search |
| POST | `/search/voice` | Voice-based search |
| GET | `/recommendations/{user_id}` | Get recommendations |
| GET | `/products/{product_id}` | Get product details |
| GET | `/products/{id}/alternatives` | Get alternatives |
| GET | `/products/{id}/explanation` | Get explanation |

See [API Documentation](docs/API.md) for complete reference.

---

## 🛠️ Development

### Adding a New Agent

1. Create agent directory in `backend/app/agents/`
2. Implement `BaseAgent` interface
3. Define agent prompts
4. Register with orchestrator
5. Create MCP tools if needed

See [Developer Guide](docs/DEVELOPER_GUIDE.md) for details.

### Adding New Tools

1. Create tool class in `backend/app/agents/mcp/tools/`
2. Implement `MCPTool` interface
3. Register in tool registry
4. Update agent to use tool

---

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

---

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

- [LangChain](https://langchain.com/) for agent framework inspiration
- [Qdrant](https://qdrant.tech/) for vector database
- [Groq](https://groq.com/) for fast LLM inference
- [Next.js](https://nextjs.org/) for frontend framework

---

<div align="center">

**Built with ❤️ by the FinFind Team**

[Website](https://finfind.com) • [Twitter](https://twitter.com/finfind) • [Discord](https://discord.gg/finfind)

</div>
