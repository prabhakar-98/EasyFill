# EasyFill

AI-powered auto-fill for Google Forms. EasyFill extracts form fields from any Google Form, matches them against your stored profile data, and fills them in automatically using LLM-driven field mapping.

## Architecture

```
Chrome Extension  <-->  React Frontend  <-->  FastAPI Backend  <-->  PostgreSQL + Redis
                                                   |
                                          LLM Gateway (multi-provider)
                                          Playwright (form extraction)
```

- **Chrome Extension** - Detects Google Forms, extracts fields (text, radio, checkbox, dropdown, grid, date, time, file upload), and fills values via a content script.
- **Frontend** - React + Vite + Tailwind CSS dashboard for managing profiles, reviewing autofill tasks, and approving field mappings.
- **Backend** - FastAPI with an agentic workflow engine (LangGraph-style), tool registry, structured logging, and JWT auth.
- **Database** - PostgreSQL with pgvector for semantic search over user data embeddings. Redis for caching.
- **LLM Gateway** - Multi-provider support with automatic fallback: Ollama (local dev), OpenRouter, OpenAI, Anthropic, Google, and AWS Bedrock.

## Features

- Automatic Google Form field extraction and classification
- Semantic matching of form fields to user profile data using embeddings (BAAI/bge-m3)
- Human-in-the-loop approval workflow before submitting
- Resume parsing and profile indexing
- Multi-provider LLM routing with configurable fallback chain
- Real-time browser streaming via WebSocket
- Structured logging with correlation IDs and PII redaction

## Prerequisites

- Docker and Docker Compose
- Node.js (for local frontend development)
- Python 3.12+ (for local backend development)
- Chrome/Chromium (for the extension)

## Quick Start

### 1. Clone and configure

```bash
cp .env.example .env
# Edit .env with your API keys (or leave defaults for local Ollama)
```

### 2. Start with Docker Compose

```bash
docker compose up --build
```

This starts:
| Service    | URL                    |
|------------|------------------------|
| Frontend   | http://localhost:5173   |
| Backend    | http://localhost:8000   |
| PostgreSQL | localhost:5432          |
| Redis      | localhost:6379          |

### 3. Install the Chrome Extension

1. Open `chrome://extensions/`
2. Enable **Developer mode**
3. Click **Load unpacked** and select the `extension/` folder
4. Navigate to any Google Form - EasyFill will appear in the side panel

## Local Development

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
playwright install chromium
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Environment Variables

See [`.env.example`](.env.example) for all configuration options. Key variables:

| Variable | Description |
|----------|-------------|
| `MODEL_PROVIDER` | Primary LLM provider (`ollama`, `openrouter`, `openai`, `anthropic`, `google`, `bedrock`) |
| `OPENROUTER_API_KEY` | API key for OpenRouter (one key for all cloud models) |
| `OLLAMA_MODEL` | Local model for development (default: `qwen3:7b`) |
| `EMBEDDING_MODEL` | Embedding model for semantic search (default: `BAAI/bge-m3`) |
| `BROWSER_HEADLESS` | Run Playwright in headless mode (default: `true`) |

## Project Structure

```
EasyFill/
├── backend/
│   ├── app/
│   │   ├── api/            # FastAPI route handlers
│   │   ├── agents/         # AI agent definitions
│   │   ├── browser/        # Playwright form extraction
│   │   ├── database/       # SQLAlchemy models, migrations, repositories
│   │   ├── logging/        # Structured logging, PII redaction
│   │   ├── models/         # LLM providers, gateway, prompt templates
│   │   ├── security/       # JWT auth, password hashing
│   │   ├── services/       # Indexing, canonical embeddings
│   │   ├── tools/          # Tool registry (browser, retrieval, validation)
│   │   └── workflows/      # Autofill workflow graph, HITL nodes
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/     # React components
│   │   └── pages/          # Route pages
│   └── Dockerfile
├── extension/
│   ├── manifest.json       # Chrome MV3 manifest
│   ├── content.js          # Google Forms field extractor
│   ├── sidepanel.js        # Side panel UI
│   └── background.js       # Service worker
├── docker-compose.yml
└── .env.example
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, Vite, Tailwind CSS, Zustand |
| Backend | FastAPI, SQLAlchemy, Playwright, LangGraph |
| Database | PostgreSQL 16 + pgvector, Redis 7 |
| LLM | Ollama, OpenRouter, OpenAI, Anthropic, Google, Bedrock |
| Embeddings | FastEmbed (BAAI/bge-m3) |
| Extension | Chrome Manifest V3 |
| Infrastructure | Docker Compose |

## License

Private - All rights reserved.
