# 🛒 SmartStore AI Advisor

> An AI-powered agent for **Naver Smart Store** sellers — analyzes niches, competitors, and trends, then generates professional PDF reports based on real Naver DataLab and Naver Shopping data.

![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110-green?logo=fastapi)
![LangGraph](https://img.shields.io/badge/LangGraph-latest-orange)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

---

## 📋 Table of Contents

- [About](#-about)
- [Features](#-features)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Quick Start](#-quick-start)
- [Project Structure](#-project-structure)
- [API Reference](#-api-reference)
- [Testing](#-testing)
- [Deployment](#-deployment)

---

## 🎯 About

SmartStore AI Advisor is an intelligent agent for sellers on the Korean marketplace Naver Smart Store. The agent autonomously collects data from Naver DataLab and Naver Shopping, analyzes it, and generates professional PDF reports.

The project solves a real problem: Naver sellers spend hours manually analyzing market data — the agent does it in minutes.

---

## ✨ Features

### 🤖 AI Agent
- Conversations in **Russian and Korean** languages
- Automatic keyword translation to Korean before Naver API calls
- Persistent conversation memory via **PostgresSaver**
- Conversation summarization — compresses long dialogues to save tokens

### 📊 Naver API Analytics
- **Naver DataLab** — search demand trends by keyword
- **Naver Shopping** — competitor data, prices, and reviews
- **Tavily** — real-time web search

### 📄 PDF Reports (5 Types)
| Type | Description |
|------|-------------|
| 🔍 Niche Analysis | Demand trends, top competitors, average prices |
| 🩺 Sales Diagnostics | Why is it not selling? Problems and recommendations |
| ✍️ SEO Optimization | New title, description, and keywords |
| 📅 Seasonal Analysis | Demand peaks and price dynamics by month |
| ⚔️ Competitor Analysis | Top products, prices, review counts |

### 📁 RAG (Retrieval-Augmented Generation)
- Upload personal seller documents (TXT, DOCX, XLSX)
- Document search with **multilingual-e5-large** embeddings
- **Cross-encoder reranking** for improved accuracy
- Per-user data isolation in Qdrant

### 🔐 Security
- JWT authentication
- Data isolation in Qdrant by `user_id`
- Health-check endpoint for monitoring

---

## 🏗 Architecture

```
┌─────────────┐     ┌─────────────────────────────────────┐
│  Frontend   │────▶│           FastAPI Backend            │
│  (HTML/JS)  │     │                                     │
└─────────────┘     │  ┌──────────┐  ┌─────────────────┐  │
                    │  │ LangGraph│  │   MCP Server    │  │
                    │  │  Agent   │──│  (FastMCP SSE)  │  │
                    │  └──────────┘  └────────┬────────┘  │
                    │                         │            │
                    └─────────────────────────┼────────────┘
                                              │
                    ┌─────────────────────────▼────────────┐
                    │              MCP Tools               │
                    │  Naver DataLab │ Naver Shopping      │
                    │  Tavily Search │ generate_report     │
                    └──────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│                      Data Layer                          │
│  PostgreSQL (users, products, reports, checkpoints)      │
│  Qdrant (vector database for RAG)                        │
└──────────────────────────────────────────────────────────┘
```

---

## 🛠 Tech Stack

| Category | Technologies |
|----------|-------------|
| **Backend** | FastAPI, Uvicorn |
| **AI Agent** | LangGraph, LangChain, Groq (llama-3.3-70b-versatile) |
| **RAG** | sentence-transformers (multilingual-e5-large), Qdrant, cross-encoder |
| **MCP** | FastMCP (SSE transport) |
| **Database** | PostgreSQL, SQLAlchemy 2.0 (async), Alembic |
| **Auth** | JWT (python-jose), bcrypt |
| **Reports** | WeasyPrint, Jinja2, Matplotlib |
| **Testing** | pytest, pytest-asyncio |
| **CI/CD** | GitHub Actions |
| **Deploy** | Docker, Docker Compose |

---

## 🚀 Quick Start

### Requirements
- Python 3.12+
- PostgreSQL 15+
- Qdrant (local or cloud)

### 1. Clone the repository

```bash
git clone https://github.com/khvandima/smartstore-agent.git
cd smartstore-agent
```

### 2. Create virtual environment

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
# Edit .env — fill in your API keys
```

Required variables:
```env
GROQ_API_KEY=        # Groq API key
NAVER_CLIENT_ID=     # Naver API Client ID
NAVER_CLIENT_SECRET= # Naver API Client Secret
TAVILY_API_KEY=      # Tavily API key
DATABASE_URL=        # postgresql+asyncpg://...
SECRET_KEY=          # Secret key for JWT
QDRANT_HOST=localhost
QDRANT_PORT=6333
```

### 5. Apply migrations

```bash
alembic upgrade head
```

### 6. Start the MCP server (separate terminal)

```bash
python -m app.mcp.server
```

### 7. Start the application

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open in browser: **http://localhost:8000**

---

## 📁 Project Structure

```
smartstore-agent/
├── app/
│   ├── agent/              # LangGraph agent
│   │   ├── graph.py        # Graph with conversation summarization
│   │   ├── mcp_client.py   # MCP client
│   │   └── state.py        # TypedDict state
│   ├── api/                # HTTP layer
│   │   ├── routes/
│   │   │   ├── auth.py     # Register, login
│   │   │   ├── chat.py     # Chat with agent
│   │   │   ├── documents.py # Document upload
│   │   │   └── reports.py  # Report generation
│   │   └── dependencies.py # JWT auth
│   ├── db/                 # Database
│   │   ├── models.py       # SQLAlchemy models
│   │   ├── session.py      # Async engine
│   │   ├── checkpointer.py # PostgresSaver
│   │   └── migrations/     # Alembic migrations
│   ├── mcp/                # MCP tools
│   │   ├── server.py       # FastMCP server
│   │   └── tools/
│   │       ├── naver_datalab.py    # Naver DataLab API
│   │       ├── naver_shopping.py   # Naver Shopping API
│   │       ├── tavily.py           # Web search
│   │       └── report_generator.py # PDF generation via agent
│   ├── rag/                # RAG pipeline
│   │   ├── ingestion.py    # Document loading and indexing
│   │   ├── retrieval.py    # Vector search
│   │   └── reranker.py     # Cross-encoder reranking
│   ├── reports/            # PDF generation
│   │   ├── pdf_generator.py
│   │   └── templates/      # Jinja2 + CSS templates
│   ├── schemas/            # Pydantic models
│   ├── config.py           # Settings (Pydantic Settings)
│   ├── constants.py        # ReportType enum, system prompt
│   ├── logger.py           # Logging setup
│   └── main.py             # FastAPI entry point
├── frontend/               # HTML/CSS/JS interface
│   ├── index.html
│   ├── style.css
│   └── chat.js
├── tests/
│   ├── unit/
│   │   ├── test_rag.py
│   │   └── test_retrieval_reranker.py
│   └── integration/
│       └── test_api.py
├── .github/workflows/
│   └── deploy.yml          # CI/CD pipeline
├── docker-compose.yml
├── Dockerfile
├── alembic.ini
├── pyproject.toml
├── requirements.txt
└── requirements-dev.txt
```

---

## 📡 API Reference

### Authentication
```
POST /auth/register    # Register new user
POST /auth/login       # Login (OAuth2 form)
```

### Chat
```
POST /chat/            # Send message to agent
```

### Documents
```
GET    /documents/           # List indexed documents
POST   /documents/upload     # Upload and index file
DELETE /documents/{filename} # Remove document from index
```

### Reports
```
POST /reports/{report_type}  # Generate PDF report
```

Available types: `niche_analysis`, `diagnostics`, `seo`, `seasonal`, `competitors`

### System
```
GET /health    # Health check — status of all components
```

---

## 🧪 Testing

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Unit tests
pytest tests/unit/ -v

# Integration tests (requires PostgreSQL)
pytest tests/integration/ -v

# All tests with coverage
pytest --cov=app tests/
```

---

## 🐳 Deployment

### Docker Compose

```bash
# Copy and fill in environment variables
cp .env.example .env

# Start all services
docker-compose up -d

# Apply migrations
docker-compose exec app alembic upgrade head
```

Services:
- **app** — FastAPI on port 8000
- **postgres** — PostgreSQL 15
- **qdrant** — Vector database on port 6333
- **mcp** — MCP server on port 8001

### GitHub Actions CI/CD

CI runs automatically on every push to `main`:
1. Runs unit tests
2. On success — deploys to server via SSH

To activate deployment, add GitHub Secrets:
- `SERVER_HOST` — server IP address
- `SERVER_USER` — SSH username
- `SERVER_SSH_KEY` — private SSH key
- `SERVER_PORT` — SSH port (usually 22)

---

## 📝 License

MIT License — free to use.

---

<div align="center">
  Built with ❤️ for Naver Smart Store sellers
</div>