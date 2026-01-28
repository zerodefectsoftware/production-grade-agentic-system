# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a production-grade agentic AI system built with FastAPI, LangGraph, and PostgreSQL. The system supports multi-environment deployments (development, staging, production) with comprehensive observability through Prometheus and Grafana. It uses LangGraph for agent orchestration with checkpointing, Langfuse for LLM tracing, and mem0ai for long-term memory management.

## Environment Setup

### Initial Setup
```bash
# Install uv package manager and dependencies
make install

# Set environment for a specific mode (development, staging, production, test)
make set-env ENV=development
```

### Environment Files
The project uses environment-specific `.env` files. Create `.env.development`, `.env.staging`, or `.env.production` files based on `.env.example`. The settings loader (`src/config/settings.py`) automatically loads the appropriate file based on the `APP_ENV` environment variable.

## Common Development Commands

### Running the Application

**Development mode (with auto-reload):**
```bash
make dev
```

**Staging:**
```bash
make staging
```

**Production:**
```bash
make prod
```

### Docker Commands

**Build Docker image:**
```bash
make docker-build-env ENV=development
```

**Run with Docker (app + database only):**
```bash
make docker-run-env ENV=development
```

**Full stack (app + database + Prometheus + Grafana + cAdvisor):**
```bash
make docker-compose-up ENV=development
```

**View logs:**
```bash
make docker-logs ENV=development
```

**Stop containers:**
```bash
make docker-stop ENV=development
# or for full stack
make docker-compose-down ENV=development
```

### Code Quality

**Lint code:**
```bash
make lint
```

**Format code:**
```bash
make format
```

### Evaluation Framework

**Run evaluation (interactive mode):**
```bash
make eval
```

**Quick evaluation:**
```bash
make eval-quick
```

**Evaluation without report:**
```bash
make eval-no-report
```

## Architecture Overview

### Core Layer Structure

The codebase follows a modular layered architecture:

1. **Interface Layer** (`src/interface/`): API endpoints and request handling
   - `router.py`: Main API router aggregating auth and chatbot routes
   - `auth.py`: User registration and JWT-based authentication
   - `interaction.py`: Chat endpoints (streaming and non-streaming)

2. **Agent Layer** (`src/agent/`): LangGraph-based agent orchestration
   - `workflow.py`: Core LangGraph workflow with chat and tool_call nodes
   - `tools/`: Agent tools (e.g., web_search.py using DuckDuckGo)
   - `prompts/`: System prompts loaded from markdown files

3. **Service Layer** (`src/services/`): Business logic and external integrations
   - `llm_provider.py`: LLM service with retry logic, circuit breaker, and fallback models

4. **Data Layer** (`src/data/`):
   - `models/`: SQLModel entities (User, Session, Thread)
   - `schemas/`: Pydantic validation schemas (auth, chat, graph state)
   - `db_manager.py`: Database service with connection pooling

5. **System Layer** (`src/system/`): Cross-cutting concerns
   - `logs.py`: Structured logging with structlog
   - `middleware.py`: Logging context and metrics middleware
   - `rate_limit.py`: Rate limiting configuration
   - `telemetry.py`: Prometheus metrics setup

6. **Utils Layer** (`src/utils/`): Shared helpers
   - `auth.py`: JWT and password hashing utilities
   - `graph.py`: Message preparation and processing
   - `sanitization.py`: Input validation and sanitization

### Key Architectural Patterns

**LangGraph Agent Workflow:**
The agent uses a StateGraph with two nodes:
- `chat` node: Calls LLM and decides if tool calls are needed
- `tool_call` node: Executes tools and returns to chat node
- Uses AsyncPostgresSaver for conversation checkpointing
- Integrates long-term memory via mem0ai's AsyncMemory with pgvector

**Connection Pooling:**
- Database: SQLAlchemy QueuePool with environment-specific sizing
- LangGraph checkpointing: AsyncConnectionPool for PostgreSQL
- Pool sizes configured via `POSTGRES_POOL_SIZE` and `POSTGRES_MAX_OVERFLOW`

**LLM Resilience:**
The LLM service (`llm_provider.py`) implements:
- Automatic retries with exponential backoff (tenacity)
- Circuit breaker pattern to prevent cascading failures
- Fallback model support (tries alternative models if primary fails)
- Prometheus metrics for inference latency

**Multi-Environment Configuration:**
The `settings.py` module:
- Loads environment-specific `.env` files
- Applies environment-specific defaults (rate limits, logging, pool sizes)
- Supports development, staging, production, and test environments

**Observability:**
- Structured logging: All logs use structlog with JSON format in production
- Metrics: Prometheus metrics exposed for FastAPI requests and LLM inference
- Tracing: Langfuse callback handlers for LLM observability
- Monitoring stack: Prometheus + Grafana dashboards (see `grafana/dashboards/`)

## Database Schema

The system uses PostgreSQL with pgvector extension:
- **User table**: Authentication (email, hashed_password)
- **Session table**: Chat sessions (id as session_id, user_id, name)
- **LangGraph checkpointing tables**: checkpoint_blobs, checkpoint_writes, checkpoints
- **Long-term memory**: Stored in pgvector collection (configurable via `LONG_TERM_MEMORY_COLLECTION_NAME`)

## API Endpoints

Main routes are versioned under `/api` (configurable via `API_V1_STR`):

**Authentication:**
- `POST /api/auth/register`: User registration
- `POST /api/auth/login`: JWT token generation

**Chat:**
- `POST /api/chatbot/chat`: Non-streaming chat response
- `POST /api/chatbot/chat/stream`: Streaming chat response (Server-Sent Events)
- `GET /api/chatbot/sessions/{session_id}/messages`: Retrieve chat history
- `DELETE /api/chatbot/sessions/{session_id}/messages`: Clear chat history
- Session management endpoints for listing, creating, updating, and deleting sessions

**Health:**
- `GET /health`: Database and API health check

## Evaluation Framework

Located in `evals/`, uses LLM-as-a-Judge pattern:
- Metrics: conciseness, hallucination, helpfulness, relevancy, toxicity
- Each metric has a prompt in `evals/metrics/prompts/`
- Run via `make eval` (interactive), `make eval-quick`, or `make eval-no-report`
- Configured via `EVALUATION_LLM`, `EVALUATION_BASE_URL`, `EVALUATION_API_KEY`

## Testing and Deployment

The project uses uv for dependency management (`pyproject.toml`). Python 3.13+ required.

**Ruff configuration:**
- Line length: 119 characters
- Docstring convention: Google style
- Enabled rules: flake8-bugbear (B), docstrings (D), errors (E), undefined names (F), eradicate (ERA)

**Docker:**
- Multi-stage build with environment-specific configurations
- Full stack includes: app, db (pgvector), Prometheus, Grafana, cAdvisor
- Health checks on database and app containers

## Important Notes

- **Environment Variables**: Always set `APP_ENV` before running the app. Use `make set-env ENV=<env>` or Docker commands with `ENV=<env>`.
- **Database Migrations**: Tables are auto-created via SQLModel on startup. For schema changes in production, add proper migration tooling.
- **Rate Limiting**: Configured per-endpoint in `.env` files using format like `RATE_LIMIT_CHAT="30 per minute"`.
- **Long-term Memory**: Requires OpenAI API key for embeddings and fact extraction (configurable via mem0ai config in `workflow.py`).
- **Checkpointing**: LangGraph uses PostgreSQL for conversation state persistence. Session continuity requires connection pool.
- **Security**: JWT tokens expire based on `JWT_ACCESS_TOKEN_EXPIRE_DAYS`. Always use strong `JWT_SECRET_KEY` in production.
