# Local Setup Guide (Without Docker)

This guide will help you run and test the application locally without Docker to understand how each layer functions.

## Required External Services

### 1. PostgreSQL with pgvector Extension (REQUIRED)
**Why needed:**
- Stores user accounts and chat sessions
- Persists LangGraph conversation state (checkpointing)
- Powers long-term memory with vector embeddings (mem0ai)

**Installation:**

**On macOS:**
```bash
# Install PostgreSQL
brew install postgresql@17

# Start PostgreSQL service
brew services start postgresql@17

# Install pgvector extension
brew install pgvector

# Connect to PostgreSQL
psql postgres

# Create database and enable pgvector
CREATE DATABASE mydb;
\c mydb
CREATE EXTENSION IF NOT EXISTS vector;
\q
```

**On Ubuntu/Debian:**
```bash
# Install PostgreSQL
sudo apt update
sudo apt install postgresql postgresql-contrib

# Install pgvector
sudo apt install postgresql-16-pgvector

# Start PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database
sudo -u postgres psql
CREATE DATABASE mydb;
\c mydb
CREATE EXTENSION IF NOT EXISTS vector;
\q
```

**On Windows:**
- Download PostgreSQL from https://www.postgresql.org/download/windows/
- Follow installer instructions
- Install pgvector: https://github.com/pgvector/pgvector#installation-notes

### 2. OpenAI API Key (REQUIRED)
**Why needed:**
- Powers the LLM agent responses
- Generates embeddings for long-term memory
- Required for basic chat functionality

**Get your API key:**
1. Go to https://platform.openai.com/api-keys
2. Sign in or create an account
3. Click "Create new secret key"
4. Copy the key (starts with `sk-...`)
5. Store it securely - you'll add it to `.env.development`

### 3. Langfuse (OPTIONAL)
**Why needed:**
- LLM observability and tracing
- Not required for basic functionality

**Options:**
- **Skip it:** Use dummy values in `.env` (app will log warnings but work)
- **Use cloud:** Sign up at https://langfuse.com
- **Self-host:** Follow https://langfuse.com/docs/deployment/self-host

### 4. Prometheus (OPTIONAL)
**Why needed:**
- Collects and stores metrics from the application
- Enables querying and alerting on application performance
- Scrapes `/metrics` endpoint exposed by FastAPI

**Installation on macOS:**
```bash
# Install Prometheus
brew install prometheus

# Verify installation
prometheus --version
```

**Configuration:**

This project includes a pre-configured Prometheus config at `prometheus/prometheus.yml`:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'fastapi'
    metrics_path: '/metrics'
    static_configs:
      - targets: ['localhost:8000']
```

> **Note:** The default config uses `app:8000` (Docker networking). For local development, the target should be `localhost:8000`. You may need to update the config file for local use.

**Start Prometheus with project config:**
```bash
# Run Prometheus with the project configuration
prometheus --config.file=prometheus/prometheus.yml
```

**Or run as background service:**
```bash
# Copy config to Homebrew location and start service
cp prometheus/prometheus.yml /opt/homebrew/etc/prometheus.yml  # Apple Silicon
# cp prometheus/prometheus.yml /usr/local/etc/prometheus.yml   # Intel Mac

brew services start prometheus
```

**Verify Prometheus is running:**
```bash
# Test web UI
open http://localhost:9090

# Check targets are being scraped
open http://localhost:9090/targets
```

### 5. Grafana (OPTIONAL)
**Why needed:**
- Visualizes metrics collected by Prometheus
- Provides dashboards for monitoring LLM latency, request rates, errors
- Alerting capabilities for production monitoring

**Installation on macOS:**
```bash
# Install Grafana
brew install grafana

# Start Grafana service
brew services start grafana

# Verify installation
grafana-server -v
```

**Default Access:**
- URL: http://localhost:3000
- Username: `admin`
- Password: `admin` (change on first login)

**Configure Prometheus Data Source:**
1. Open http://localhost:3000
2. Login with admin/admin
3. Go to **Connections** → **Data Sources** → **Add data source**
4. Select **Prometheus**
5. Set URL: `http://localhost:9090`
6. Click **Save & Test**

**Import Project Dashboards:**

This project includes pre-built dashboards at `grafana/dashboards/json/`:

1. Go to **Dashboards** → **New** → **Import**
2. Click **Upload dashboard JSON file**
3. Select `grafana/dashboards/json/llm_latency.json`
4. Select Prometheus as the data source
5. Click **Import**

**Verify Grafana is running:**
```bash
# Check service status
brew services list | grep grafana

# Test web UI
open http://localhost:3000
```

### 6. Langfuse (OPTIONAL)
**Why needed:**
- LLM observability and tracing
- Not required for basic functionality

**Options:**
- **Skip it:** Use dummy values in `.env` (app will log warnings but work)
- **Use cloud:** Sign up at https://langfuse.com
- **Self-host:** Follow https://langfuse.com/docs/deployment/self-host

---

## Service URLs and Ports (Quick Reference)

| Service | URL | Port | Purpose |
|---------|-----|------|---------|
| FastAPI App | http://localhost:8000 | 8000 | Main application |
| API Documentation | http://localhost:8000/docs | 8000 | Swagger UI |
| Health Check | http://localhost:8000/health | 8000 | Health endpoint |
| Metrics | http://localhost:8000/metrics | 8000 | Prometheus metrics |
| PostgreSQL | localhost:5432 | 5432 | Database |
| Prometheus | http://localhost:9090 | 9090 | Metrics collection |
| Grafana | http://localhost:3000 | 3000 | Metrics visualization |

---

## Step-by-Step Setup

### Step 1: Install Python Dependencies

```bash
# Make sure you're in the project directory
cd /Users/zerodefectsoftware2025/learn_llm/production-grade-agentic-system

# Install uv package manager
pip install uv

# Install all project dependencies
uv sync
```

This creates a `.venv` virtual environment and installs all dependencies from `pyproject.toml`.

### Step 2: Configure Environment Variables

Create a `.env.development` file:

```bash
cp .env.example .env.development
```

Edit `.env.development` with your settings:

```bash
# Application Settings
APP_ENV=development
PROJECT_NAME="My AI Agent"
VERSION=1.0.0
DEBUG=true

# API Settings
API_V1_STR=/api

# CORS Settings (allow local testing)
ALLOWED_ORIGINS="http://localhost:3000,http://localhost:8000"

# Langfuse Settings (use dummy values if not using Langfuse)
LANGFUSE_PUBLIC_KEY="pk-test-dummy"
LANGFUSE_SECRET_KEY="sk-test-dummy"
LANGFUSE_HOST=https://cloud.langfuse.com

# LLM Settings - IMPORTANT: Add your real OpenAI API key
OPENAI_API_KEY="sk-your-actual-openai-key-here"
DEFAULT_LLM_MODEL=gpt-4o-mini
DEFAULT_LLM_TEMPERATURE=0.2
MAX_TOKENS=2000
MAX_LLM_CALL_RETRIES=3

# Long-term Memory Settings
LONG_TERM_MEMORY_MODEL=gpt-4o-mini
LONG_TERM_MEMORY_EMBEDDER_MODEL=text-embedding-3-small
LONG_TERM_MEMORY_COLLECTION_NAME=longterm_memory

# JWT Settings (generate a secure random string)
JWT_SECRET_KEY="your-super-secret-jwt-key-change-this"
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_DAYS=30

# Database Settings - LOCAL PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_DB=mydb
POSTGRES_USER=postgres  # or your postgres username
POSTGRES_PORT=5432
POSTGRES_PASSWORD=postgres  # or your postgres password
POSTGRES_POOL_SIZE=5
POSTGRES_MAX_OVERFLOW=10

# Rate Limiting Settings (relaxed for development)
RATE_LIMIT_DEFAULT="1000 per day,200 per hour"
RATE_LIMIT_CHAT="100 per minute"
RATE_LIMIT_CHAT_STREAM="100 per minute"
RATE_LIMIT_MESSAGES="200 per minute"
RATE_LIMIT_LOGIN="100 per minute"

# Logging
LOG_LEVEL=DEBUG
LOG_FORMAT=console
```

**Important:** Replace these values:
- `OPENAI_API_KEY`: Your actual OpenAI API key
- `JWT_SECRET_KEY`: A secure random string
- `POSTGRES_USER` and `POSTGRES_PASSWORD`: Your local PostgreSQL credentials

### Step 3: Verify Database Connection

Test that PostgreSQL is running and accessible:

```bash
# Try connecting to your database
psql -h localhost -U postgres -d mydb -c "SELECT version();"

# Verify pgvector extension is installed
psql -h localhost -U postgres -d mydb -c "SELECT * FROM pg_extension WHERE extname = 'vector';"
```

If you see version info and the pgvector extension listed, you're good!

### Step 4: Run the Application

```bash
# Set environment and run in development mode
make dev
```

This command:
1. Sources the `.env.development` file
2. Activates the virtual environment
3. Runs uvicorn with auto-reload on port 8000

You should see output like:
```
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 5: Verify the Application is Running

Open your browser or use curl:

```bash
# Check health endpoint
curl http://localhost:8000/health

# You should see:
# {
#   "status": "healthy",
#   "version": "1.0.0",
#   "environment": "development",
#   "components": {"api": "healthy", "database": "healthy"},
#   "timestamp": "2024-01-19T..."
# }
```

If database shows "unhealthy", check your PostgreSQL connection settings in `.env.development`.

---

## Testing Basic Chat Functionality

Now let's test the chat functionality to understand how each layer works!

### Test 1: Register a User (Interface + Data Layer)

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePassword123!"
  }'
```

**Expected response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "test@example.com",
    "created_at": "2024-01-19T..."
  }
}
```

**What happened in each layer:**
1. **Interface Layer** (`src/interface/auth.py`): Received request, validated email/password format
2. **Utils Layer** (`src/utils/auth.py`): Hashed the password using bcrypt
3. **Data Layer** (`src/data/db_manager.py`): Created user record in PostgreSQL
4. **Utils Layer** (`src/utils/auth.py`): Generated JWT token
5. **Interface Layer**: Returned token to client

### Test 2: Login (Authentication Flow)

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePassword123!"
  }'
```

Save the `access_token` from the response - you'll need it for chat requests.

### Test 3: Send a Chat Message (Full Stack Test)

```bash
# Replace YOUR_TOKEN with the access_token from login
curl -X POST http://localhost:8000/api/chatbot/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "message": "Hello! Can you explain what you can do?"
  }'
```

**Expected response:**
```json
{
  "session_id": "uuid-here",
  "messages": [
    {
      "role": "user",
      "content": "Hello! Can you explain what you can do?"
    },
    {
      "role": "assistant",
      "content": "I'm an AI assistant that can help you with..."
    }
  ]
}
```

**What happened in each layer:**

1. **System Layer** (`src/system/middleware.py`):
   - LoggingContextMiddleware: Added request ID and context
   - MetricsMiddleware: Started tracking request metrics

2. **Interface Layer** (`src/interface/interaction.py`):
   - Validated JWT token
   - Extracted user info from token
   - Validated message schema

3. **Data Layer** (`src/data/db_manager.py`):
   - Created or retrieved chat session
   - Associated session with user

4. **Agent Layer** (`src/agent/workflow.py`):
   - `_get_relevant_memory()`: Queried long-term memory (mem0ai + pgvector)
   - Created LangGraph with StateGraph
   - Initialized AsyncPostgresSaver for checkpointing

5. **Service Layer** (`src/services/llm_provider.py`):
   - Called OpenAI API with retry logic
   - Circuit breaker monitored for failures
   - If failure, would try fallback models

6. **Agent Layer** (continued):
   - `_chat()` node: Processed LLM response
   - Checked for tool calls (none in this case)
   - Routed to END

7. **Agent Layer** (background):
   - `_update_long_term_memory()`: Asynchronously stored conversation in pgvector

8. **System Layer**:
   - Recorded Prometheus metrics (latency, model used)
   - Logged to Langfuse (if configured)
   - Structured logs written

9. **Interface Layer**:
   - Formatted response
   - Returned JSON to client

### Test 4: Stream Response (Streaming API)

```bash
curl -X POST http://localhost:8000/api/chatbot/chat/stream \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "message": "Tell me a short story",
    "session_id": "SESSION_ID_FROM_PREVIOUS_RESPONSE"
  }'
```

You'll see tokens streamed in real-time using Server-Sent Events (SSE).

**Key difference in layers:**
- **Agent Layer** uses `_graph.astream()` instead of `_graph.ainvoke()`
- **Interface Layer** uses `StreamingResponse` with `AsyncGenerator`
- Tokens yield immediately as they arrive from OpenAI

### Test 5: Get Chat History (Checkpointing Test)

```bash
curl -X GET "http://localhost:8000/api/chatbot/sessions/SESSION_ID/messages" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**What happened:**
- **Agent Layer** (`workflow.py`): `get_chat_history()` method
- **LangGraph**: Retrieved state from PostgreSQL checkpointing tables
- Shows conversation persistence across requests

### Test 6: Test with Tool Calling

```bash
curl -X POST http://localhost:8000/api/chatbot/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "message": "Search the web for latest news about AI agents"
  }'
```

**What happens differently:**
1. **Agent Layer** `_chat()` node: LLM decides to use `web_search` tool
2. Routes to `tool_call` node instead of END
3. **Agent Layer** `_tool_call()`: Executes `src/agent/tools/web_search.py`
4. Tool uses DuckDuckGo to search
5. Returns to `_chat()` node with search results
6. LLM generates final response with search context

---

## Observing Each Layer in Action

### Enable Detailed Logging

In your terminal where the app is running, you'll see structured logs for each request:

```
{"event": "request_started", "path": "/api/chatbot/chat", "method": "POST"}
{"event": "llm_response_generated", "session_id": "...", "model": "gpt-4o-mini"}
{"event": "request_completed", "duration": 1.234}
```

### Check Database Tables

See what's stored in PostgreSQL:

```bash
# Connect to database
psql -h localhost -U postgres -d mydb

# See users
SELECT * FROM user;

# See sessions
SELECT * FROM session;

# See LangGraph checkpoints
SELECT thread_id, COUNT(*) FROM checkpoints GROUP BY thread_id;

# Exit
\q
```

### Monitor API with Swagger UI

Open http://localhost:8000/docs in your browser to see interactive API documentation and test endpoints visually.

---

## Troubleshooting

### Issue: Database connection failed
**Solution:**
- Verify PostgreSQL is running: `brew services list` (macOS) or `sudo systemctl status postgresql` (Linux)
- Check credentials in `.env.development` match your PostgreSQL setup
- Test connection: `psql -h localhost -U postgres -d mydb`

### Issue: OpenAI API errors
**Solution:**
- Verify API key is correct in `.env.development`
- Check you have credits: https://platform.openai.com/usage
- Try a different model: change `DEFAULT_LLM_MODEL=gpt-3.5-turbo`

### Issue: pgvector extension not found
**Solution:**
```bash
# Connect to database and enable extension
psql -h localhost -U postgres -d mydb
CREATE EXTENSION IF NOT EXISTS vector;
\q
```

### Issue: Port 8000 already in use
**Solution:**
```bash
# Find and kill process using port 8000
lsof -ti:8000 | xargs kill -9

# Or run on different port
uv run uvicorn src.main:app --reload --port 8001
```

---

## Next Steps

Once you're comfortable with basic functionality:

1. **Explore the code:** Add `print()` statements in different layers to trace request flow
2. **Try different prompts:** Test how the agent handles various queries
3. **Inspect Prometheus metrics:** Visit http://localhost:8000/metrics
4. **Add a custom tool:** Create a new tool in `src/agent/tools/`
5. **Modify system prompt:** Edit `src/agent/prompts/system.md`
6. **Add new API endpoints:** Create routes in `src/interface/`

Now you're ready to expand and build more backend services on this foundation!
