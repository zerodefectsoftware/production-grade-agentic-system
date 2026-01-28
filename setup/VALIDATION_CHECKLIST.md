# Build and Startup Validation Checklist

This document provides a comprehensive checklist for validating the build and startup of the application, both with and without Docker.

**Last Updated:** January 23, 2026
**Project:** Production-Grade Agentic System

---

## Table of Contents
- [Pre-Requisites Validation](#pre-requisites-validation)
- [Configuration Validation](#configuration-validation)
- [Local Development (Non-Docker) Validation](#local-development-non-docker-validation)
- [Docker Build Validation](#docker-build-validation)
- [Docker Compose Validation](#docker-compose-validation)
- [Post-Startup Validation](#post-startup-validation)
- [Observability Tools Validation](#observability-tools-validation-local-install)
- [Service URLs and Ports Reference](#service-urls-and-ports-reference)
- [Troubleshooting Guide](#troubleshooting-guide)

---

## Pre-Requisites Validation

### 1. System Dependencies

#### Check Python Version
```bash
python --version
# Expected: Python 3.13.x or higher
```

#### Check UV Package Manager
```bash
uv --version
# Expected: uv x.x.x
# If not installed: pip install uv
```

#### Check Docker (if using Docker)
```bash
docker --version
# Expected: Docker version 20.x or higher

docker-compose --version
# Expected: docker-compose version 1.29.x or higher
```

#### Check PostgreSQL (for local development)
```bash
pg_isready
# Expected: /tmp:5432 - accepting connections

psql --version
# Expected: psql (PostgreSQL) 16.x or 17.x
```

#### Check pgvector Extension
```bash
psql -h localhost -U postgres -d postgres -c "SELECT * FROM pg_available_extensions WHERE name = 'vector';"
# Expected: Row showing vector extension available
```

---

### 2. Project Structure Validation

#### Verify Critical Files Exist
```bash
# Check project structure
ls -la

# Expected files:
# ✓ Makefile
# ✓ Dockerfile
# ✓ docker-compose.yml
# ✓ pyproject.toml
# ✓ .env.example
# ✓ src/main.py
# ✓ scripts/set_env.sh
# ✓ scripts/docker-entrypoint.sh
```

#### Verify Source Code Structure
```bash
ls -la src/
# Expected directories:
# ✓ agent/
# ✓ data/
# ✓ interface/
# ✓ services/
# ✓ system/
# ✓ utils/
# ✓ main.py
```

#### Verify Scripts are Executable
```bash
ls -la scripts/
# Expected: -rwxr-xr-x for .sh files

# If not executable:
chmod +x scripts/set_env.sh
chmod +x scripts/docker-entrypoint.sh
```

---

## Configuration Validation

### 1. Environment File Setup

#### Check Environment Files Exist
```bash
ls -la .env*
# Expected:
# ✓ .env.example
# ✓ .env.development (if not, create from .env.example)
```

#### Create Development Environment File (if missing)
```bash
cp .env.example .env.development
echo "✓ Created .env.development"
```

#### Validate Required Environment Variables
```bash
# Check critical variables are set (not just placeholders)
cat .env.development | grep -E "OPENAI_API_KEY|POSTGRES_HOST|POSTGRES_DB|JWT_SECRET_KEY"

# Expected output showing actual values (not "your-xxx-here")
```

**Critical Variables Checklist:**
- [ ] `OPENAI_API_KEY` - Real API key (starts with `sk-` or `sk-proj-`)
- [ ] `POSTGRES_HOST` - Set to `localhost` for local dev
- [ ] `POSTGRES_DB` - Database name (e.g., `mydb`)
- [ ] `POSTGRES_USER` - Your PostgreSQL username
- [ ] `POSTGRES_PASSWORD` - Your PostgreSQL password (can be empty for local)
- [ ] `JWT_SECRET_KEY` - A secure random string
- [ ] `APP_ENV` - Set to `development`

---

### 2. Makefile Configuration Validation

#### Verify API_MODULE is Set
```bash
grep "API_MODULE" Makefile
# Expected: API_MODULE = src.main:app
```

#### Verify Export Statement
```bash
grep "export API_MODULE" Makefile
# Expected: export API_MODULE
```

#### Verify Correct Module Path in Commands
```bash
grep "uvicorn.*API_MODULE" Makefile
# Expected lines showing $(API_MODULE) usage
```

---

### 3. Dockerfile Validation

#### Verify Correct Module Path
```bash
grep "CMD.*uvicorn" Dockerfile
# Expected: CMD ["/app/.venv/bin/uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
# Should NOT contain ${API_MODULE} or app.main:app
```

---

### 4. docker-compose.yml Validation

#### Verify Correct Volume Mapping
```bash
grep -A2 "volumes:" docker-compose.yml | grep "src"
# Expected: - ./src:/app/src
# Should NOT show ./app:/app/src
```

---

## Local Development (Non-Docker) Validation

### 1. Database Preparation

#### Start PostgreSQL Service (if not running)
```bash
# macOS
brew services start postgresql@17

# Linux
sudo systemctl start postgresql

# Verify running
pg_isready -h localhost
# Expected: localhost:5432 - accepting connections
```

#### Create Database
```bash
# Connect to PostgreSQL
psql -h localhost -U postgres

# In psql prompt:
CREATE DATABASE mydb;
\c mydb
CREATE EXTENSION IF NOT EXISTS vector;
\q
```

#### Verify Database and Extension
```bash
psql -h localhost -U postgres -d mydb -c "SELECT version();"
# Expected: PostgreSQL version output

psql -h localhost -U postgres -d mydb -c "SELECT * FROM pg_extension WHERE extname = 'vector';"
# Expected: Row showing vector extension
```

---

### 2. Python Environment Setup

#### Install Dependencies
```bash
# Install uv (if not already)
pip install uv

# Sync dependencies
uv sync
# Expected: Creating virtual environment at .venv
# Expected: Installed XX packages
```

#### Verify Virtual Environment
```bash
ls -la .venv/
# Expected: bin/, lib/, pyvenv.cfg

source .venv/bin/activate
python --version
# Expected: Python 3.13.x
```

#### Verify Key Packages Installed
```bash
uv pip list | grep -E "fastapi|langchain|langgraph|sqlmodel|uvicorn"
# Expected: List showing all packages installed
```

---

### 3. Start Application (Local)

#### Test Environment Loading
```bash
make set-env ENV=development
# Expected: Setting environment to development
# Expected: Environment summary displayed
```

#### Start Development Server
```bash
make dev
```

**Expected Output:**
```
Starting server in development environment
Loading environment from /path/to/.env.development
Successfully loaded environment variables from .env.development

======= ENVIRONMENT SUMMARY =======
Environment:     development
Project root:    /path/to/project
Project name:    Web Assistant
API version:     1.0.0
Database host:   localhost
Database port:   5432
Database name:   mydb
Database user:   <your-user>
LLM model:       gpt-4o-mini
Log level:       DEBUG
Debug mode:      true

INFO:     Will watch for changes in these directories: ['/path/to/project']
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [XXXXX] using StatReload
INFO:     Started server process [XXXXX]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**Red Flags (should NOT see):**
- ❌ `ModuleNotFoundError: No module named 'app'`
- ❌ `ERROR: [Errno 48] Address already in use`
- ❌ Database connection errors
- ❌ Missing environment variable warnings

---

### 4. Verify Application is Running

#### Check Process
```bash
lsof -ti:8000
# Expected: Process ID number
```

#### Test Health Endpoint
```bash
curl http://localhost:8000/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "environment": "development",
  "components": {
    "api": "healthy",
    "database": "healthy"
  },
  "timestamp": "2026-01-21T..."
}
```

**Validation Checklist:**
- [ ] `status` is `"healthy"`
- [ ] `components.database` is `"healthy"`
- [ ] `environment` matches your ENV setting
- [ ] Response received within 2 seconds

#### Test API Documentation
```bash
# Open in browser
open http://localhost:8000/docs

# Or test with curl
curl http://localhost:8000/docs
# Expected: HTML response with Swagger UI
```

---

### 5. Test Basic Functionality

#### Test User Registration
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPassword123!"
  }'
```

**Expected Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "test@example.com",
    "created_at": "2026-01-21T..."
  }
}
```

#### Save Token and Test Chat
```bash
# Save token from previous response
TOKEN="<your-access-token>"

curl -X POST http://localhost:8000/api/chatbot/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "message": "Hello, can you hear me?"
  }'
```

**Expected Response:**
```json
{
  "session_id": "uuid-here",
  "messages": [
    {
      "role": "user",
      "content": "Hello, can you hear me?"
    },
    {
      "role": "assistant",
      "content": "Yes, I can hear you! How can I help you today?"
    }
  ]
}
```

---

### 6. Check Application Logs

Review logs in terminal where `make dev` is running:

**Expected Log Patterns:**
```
INFO:     127.0.0.1:XXXXX - "POST /api/auth/register HTTP/1.1" 200 OK
INFO:     127.0.0.1:XXXXX - "POST /api/chatbot/chat HTTP/1.1" 200 OK
```

**Red Flags:**
- ❌ ERROR level messages
- ❌ 500 Internal Server Error responses
- ❌ Unhandled exceptions
- ❌ Database connection timeouts

---

### 7. Test Hot Reload (Development Feature)

#### Make a Code Change
```bash
# Edit src/main.py - add a comment at the top
echo "# Test hot reload" >> src/main.py
```

#### Watch Logs
**Expected Output:**
```
INFO:     Detected file change in 'src/main.py'
INFO:     Reloading...
INFO:     Started server process [XXXXX]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

#### Verify Server Still Works
```bash
curl http://localhost:8000/health
# Expected: Same healthy response
```

---

### 8. Stop Local Server

```bash
# In terminal where make dev is running
# Press Ctrl+C

# Verify process stopped
lsof -ti:8000
# Expected: No output (port is free)
```

---

## Docker Build Validation

### 1. Pre-Build Checks

#### Verify Dockerfile Exists
```bash
test -f Dockerfile && echo "✓ Dockerfile exists" || echo "✗ Dockerfile missing"
```

#### Verify Docker Daemon is Running
```bash
docker ps
# Expected: List of running containers (can be empty)
# If error: Start Docker Desktop or Docker daemon
```

---

### 2. Build Docker Image

#### Build for Development Environment
```bash
make docker-build-env ENV=development
```

**Expected Output:**
```
Building Docker image for development environment
Loading environment variables from .env.development (secrets masked)
Environment: development
Database host: ********
Database port: ********
...
[+] Building 45.3s (15/15) FINISHED
 => [internal] load build definition from Dockerfile
 => [internal] load .dockerignore
 => [internal] load metadata for docker.io/library/python:3.13.2-slim
 => CACHED [1/8] FROM docker.io/library/python:3.13.2-slim
 => [2/8] WORKDIR /app
 => [3/8] RUN apt-get update && apt-get install -y build-essential libpq-dev...
 => [4/8] COPY pyproject.toml .
 => [5/8] RUN uv venv && . .venv/bin/activate && uv pip install -e .
 => [6/8] COPY . .
 => [7/8] RUN chmod +x /app/scripts/docker-entrypoint.sh
 => [8/8] RUN useradd -m appuser && chown -R appuser:appuser /app
 => exporting to image
 => naming to docker.io/library/fastapi-langgraph-template:development

Docker image fastapi-langgraph-template:development built successfully
```

**Red Flags:**
- ❌ Build failures
- ❌ Package installation errors
- ❌ Permission denied errors
- ❌ Out of disk space errors

---

### 3. Verify Image Was Created

```bash
docker images | grep fastapi-langgraph-template
```

**Expected Output:**
```
fastapi-langgraph-template   development   abc123def456   2 minutes ago   XXX MB
```

**Validation Checklist:**
- [ ] Image appears in list
- [ ] Tag matches environment (development)
- [ ] Size is reasonable (500MB - 1.5GB typical)
- [ ] Created timestamp is recent

---

### 4. Test Image Directly (Optional)

```bash
# Run container from image
docker run -d \
  --name test-container \
  -p 8000:8000 \
  --env-file .env.development \
  fastapi-langgraph-template:development

# Check if running
docker ps | grep test-container
# Expected: Container status "Up"

# Check logs
docker logs test-container
# Expected: Startup logs, no errors

# Test endpoint
curl http://localhost:8000/health

# Cleanup
docker stop test-container
docker rm test-container
```

---

## Docker Compose Validation

### 1. Pre-Compose Checks

#### Verify docker-compose.yml Exists
```bash
test -f docker-compose.yml && echo "✓ docker-compose.yml exists" || echo "✗ Missing"
```

#### Verify Environment File Exists
```bash
test -f .env.development && echo "✓ .env.development exists" || echo "✗ Missing"
```

#### Check for Port Conflicts
```bash
# Check if ports are available
lsof -ti:5432 && echo "⚠ Port 5432 in use" || echo "✓ Port 5432 available"
lsof -ti:8000 && echo "⚠ Port 8000 in use" || echo "✓ Port 8000 available"
lsof -ti:9090 && echo "⚠ Port 9090 in use" || echo "✓ Port 9090 available"
lsof -ti:3000 && echo "⚠ Port 3000 in use" || echo "✓ Port 3000 available"
```

---

### 2. Start Services with Docker Compose

#### Start API + Database Only
```bash
make docker-run-env ENV=development
```

**Expected Output:**
```
[+] Running 3/3
 ✔ Network production-grade-agentic-system_monitoring  Created
 ✔ Container production-grade-agentic-system-db-1      Started
 ✔ Container fastapi-api-development                   Started
```

---

### 3. Verify Containers are Running

```bash
docker-compose ps
```

**Expected Output:**
```
NAME                                      IMAGE                        STATUS              PORTS
fastapi-api-development                   fastapi-langgraph:dev        Up (healthy)        0.0.0.0:8000->8000/tcp
production-grade-agentic-system-db-1      pgvector/pgvector:pg16       Up (healthy)        0.0.0.0:5432->5432/tcp
```

**Validation Checklist:**
- [ ] Both containers show "Up"
- [ ] Health status shows "(healthy)"
- [ ] Ports are correctly mapped
- [ ] No "Restarting" status

---

### 4. Check Container Logs

#### Check API Logs
```bash
docker-compose logs app
```

**Expected Output:**
```
app  | Starting with these environment variables:
app  | APP_ENV: development
app  | Loading environment from .env.development
app  | Environment: development
app  | INFO:     Started server process [1]
app  | INFO:     Waiting for application startup.
app  | INFO:     Application startup complete.
app  | INFO:     Uvicorn running on http://0.0.0.0:8000
```

#### Check Database Logs
```bash
docker-compose logs db
```

**Expected Output:**
```
db   | PostgreSQL init process complete; ready for start up.
db   | LOG:  database system is ready to accept connections
```

**Red Flags:**
- ❌ Python ModuleNotFoundError
- ❌ Database connection refused
- ❌ Missing environment variables
- ❌ Permission denied errors
- ❌ Container restart loops

---

### 5. Test API Endpoints

#### Test Health Endpoint
```bash
curl http://localhost:8000/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "environment": "development",
  "components": {
    "api": "healthy",
    "database": "healthy"
  },
  "timestamp": "2026-01-21T..."
}
```

#### Test API Documentation
```bash
curl -I http://localhost:8000/docs
# Expected: HTTP/1.1 200 OK
```

---

### 6. Test Database Connectivity

#### Connect to PostgreSQL Container
```bash
docker-compose exec db psql -U ${POSTGRES_USER} -d ${POSTGRES_DB}
```

**In psql prompt:**
```sql
-- Check pgvector extension
SELECT * FROM pg_extension WHERE extname = 'vector';

-- Check for application tables (after first run)
\dt

-- Exit
\q
```

---

### 7. Test Hot Reload in Docker (Development)

#### Make Code Change
```bash
echo "# Docker hot reload test" >> src/main.py
```

#### Watch Container Logs
```bash
docker-compose logs -f app
```

**Expected Output:**
```
app  | INFO:     Detected file change in '/app/src/main.py'
app  | INFO:     Reloading...
app  | INFO:     Application startup complete.
```

#### Verify API Still Works
```bash
curl http://localhost:8000/health
# Expected: Healthy response
```

---

### 8. Check Docker Volumes

```bash
docker volume ls | grep production-grade-agentic-system
```

**Expected Output:**
```
production-grade-agentic-system_postgres-data
production-grade-agentic-system_grafana-storage
```

---

### 9. Start Full Stack (Optional)

```bash
make docker-compose-up ENV=development
```

**Expected Services:**
- ✓ Database (port 5432)
- ✓ API (port 8000)
- ✓ Prometheus (port 9090)
- ✓ Grafana (port 3000)
- ✓ cAdvisor (port 8080)

#### Verify All Services
```bash
# Check all containers
docker-compose ps

# Test Prometheus
curl http://localhost:9090/-/healthy
# Expected: Prometheus is Healthy.

# Test Grafana (in browser)
open http://localhost:3000
# Default credentials: admin/admin => admin/gr@f@n@
```

---

### 10. Stop Docker Compose

```bash
make docker-stop ENV=development
```

**Expected Output:**
```
[+] Running 3/3
 ✔ Container fastapi-api-development                   Removed
 ✔ Container production-grade-agentic-system-db-1      Removed
 ✔ Network production-grade-agentic-system_monitoring  Removed
```

#### Verify Containers Stopped
```bash
docker-compose ps
# Expected: Empty list or "No resources found"
```

---

## Post-Startup Validation

### API Endpoint Tests

#### Authentication Flow

```bash
# 1. Register user
 curl-X POST  http://localhost:8000/api/auth/register \
   -H "Content-Type: application/json" \
    -d '{
    "email": "komali65@gmail.com",
    "password": "K0m@li65"
  }'

# 2. Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=komali65@gmail.com&password=Kom@li65" 
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwiZXhwIjoxNzcxNjE3NTAxLCJpYXQiOjE3NjkwMjU1MDEsImp0aSI6IjEtMTc2OTAyNTUwMS4wNzU2NzgifQ.lPqnKQMunXuIk4W7e1WcKiclPHTs9EOt6K72NwEooaw"
  
  
# 3. Create Session
curl -X POST http://localhost:8000/api/v1/auth/session \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwiZXhwIjoxNzcxNjE3NTAxLCJpYXQiOjE3NjkwMjU1MDEsImp0aSI6IjEtMTc2OTAyNTUwMS4wNzU2NzgifQ.lPqnKQMunXuIk4W7e1WcKiclPHTs9EOt6K72NwEooaw"

#4. Get Sessions
curl -X GET http://localhost:8000/api/v1/auth/sessions \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwiZXhwIjoxNzcxNjE3NTAxLCJpYXQiOjE3NjkwMjU1MDEsImp0aSI6IjEtMTc2OTAyNTUwMS4wNzU2NzgifQ.lPqnKQMunXuIk4W7e1WcKiclPHTs9EOt6K72NwEooaw"


# 5. Test authenticated endpoint
curl -X POST http://localhost:8000/api/chatbot/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "message": "Test message"
  }' | jq
```



---

### Performance Validation

#### Response Time Check
```bash
# Should respond within 2 seconds for health check
time curl http://localhost:8000/health

# Expected: real 0m0.XXXs (under 2 seconds)
```

#### Memory Usage (Docker)
```bash
docker stats --no-stream
```

**Expected:**
- API container: < 500MB memory
- Database container: < 200MB memory

---

### Database Validation

#### Check Tables Were Created
```bash
# For local dev
psql -h localhost -U postgres -d mydb -c "\dt"

# For Docker
docker-compose exec db psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} -c "\dt"
```

**Expected Tables:**
- `user`
- `session`
- `checkpoints`
- `checkpoint_blobs`
- `checkpoint_writes`

#### Check User Data
```bashpsql -h localhost -U postgres -d mydb -c "SELECT id, email, created_at FROM \"user\";"

```

---

## Observability Tools Validation (Local Install)

### 1. Prometheus Validation

#### Check Prometheus is Installed
```bash
prometheus --version
# Expected: prometheus, version X.X.X
```

#### Check Prometheus Service is Running
```bash
brew services list | grep prometheus
# Expected: prometheus started
```

#### Verify Prometheus Configuration
```bash
# Check project Prometheus config
cat prometheus/prometheus.yml

# For local dev, ensure target is localhost:8000 (not app:8000)
```

#### Test Prometheus Web UI
```bash
curl -s http://localhost:9090/-/healthy
# Expected: Prometheus Server is Healthy.

# Or open in browser
open http://localhost:9090
```

#### Verify Prometheus is Scraping FastAPI
1. Open http://localhost:9090
2. Go to **Status** → **Targets**
3. Verify `fastapi` job shows **UP** status

#### Test Prometheus Query
```bash
curl -s "http://localhost:9090/api/v1/query?query=up"
# Expected: JSON response with metric data
```

**Validation Checklist:**
- [ ] `prometheus --version` returns version info
- [ ] Service status shows "started"
- [ ] Web UI accessible at http://localhost:9090
- [ ] FastAPI target shows "UP" in targets page
- [ ] Can query metrics via API

---

### 2. Grafana Validation

#### Check Grafana is Installed
```bash
grafana-server -v
# Expected: Version X.X.X
```

#### Check Grafana Service is Running
```bash
brew services list | grep grafana
# Expected: grafana started
```

#### Test Grafana Web UI
```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/login
# Expected: 200

# Or open in browser
open http://localhost:3000
```

#### Verify Prometheus Data Source
1. Login to Grafana (admin/admin)
2. Go to **Connections** → **Data Sources**
3. Click on Prometheus data source
4. Click **Save & Test**
5. Expected: "Data source is working"

#### Import Project Dashboards
1. Go to **Dashboards** → **New** → **Import**
2. Upload `grafana/dashboards/json/llm_latency.json`
3. Select Prometheus data source
4. Verify panels show data (not "No data")

**Validation Checklist:**
- [ ] `grafana-server -v` returns version info
- [ ] Service status shows "started"
- [ ] Web UI accessible at http://localhost:3000
- [ ] Can login with admin credentials
- [ ] Prometheus data source connected
- [ ] Dashboards display metrics

---

### 3. Metrics Endpoint Validation

#### Verify FastAPI Exposes Metrics
```bash
curl -s http://localhost:8000/metrics | head -20
```

**Expected Output (sample):**
```
# HELP http_requests_total Total number of HTTP requests
# TYPE http_requests_total counter
http_requests_total{method="GET",endpoint="/health",status="200"} 5.0
# HELP http_request_duration_seconds HTTP request duration in seconds
# TYPE http_request_duration_seconds histogram
...
```

#### Check Key Metrics Exist
```bash
# HTTP request metrics
curl -s http://localhost:8000/metrics | grep http_requests_total

# LLM inference metrics
curl -s http://localhost:8000/metrics | grep llm_inference_duration

# Database connection metrics
curl -s http://localhost:8000/metrics | grep db_connections
```

**Validation Checklist:**
- [ ] `/metrics` endpoint returns Prometheus format
- [ ] `http_requests_total` metric present
- [ ] `http_request_duration_seconds` metric present
- [ ] `llm_inference_duration_seconds` metric present
- [ ] `db_connections` metric present

---

## Service URLs and Ports Reference

### Application Services

| Service | URL | Port | Health Check |
|---------|-----|------|--------------|
| FastAPI App | http://localhost:8000 | 8000 | `curl http://localhost:8000/health` |
| API Docs (Swagger) | http://localhost:8000/docs | 8000 | Open in browser |
| API Docs (ReDoc) | http://localhost:8000/redoc | 8000 | Open in browser |
| Metrics Endpoint | http://localhost:8000/metrics | 8000 | `curl http://localhost:8000/metrics` |

### Database

| Service | Host | Port | Connection Test |
|---------|------|------|-----------------|
| PostgreSQL | localhost | 5432 | `pg_isready -h localhost` |

### Observability Stack

| Service | URL | Port | Default Credentials | Health Check |
|---------|-----|------|---------------------|--------------|
| Prometheus | http://localhost:9090 | 9090 | N/A | `curl http://localhost:9090/-/healthy` |
| Grafana | http://localhost:3000 | 3000 | admin / admin | `curl http://localhost:3000/login` |

### Quick Verification Script

```bash
#!/bin/bash
echo "=== Service Status Check ==="

# FastAPI
echo -n "FastAPI (8000): "
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health && echo " ✓" || echo " ✗"

# PostgreSQL
echo -n "PostgreSQL (5432): "
pg_isready -h localhost -q && echo "✓" || echo "✗"

# Prometheus
echo -n "Prometheus (9090): "
curl -s -o /dev/null -w "%{http_code}" http://localhost:9090/-/healthy && echo " ✓" || echo " ✗"

# Grafana
echo -n "Grafana (3000): "
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/login && echo " ✓" || echo " ✗"

echo "=== Done ==="
```

### Port Conflict Resolution

If any port is already in use:

```bash
# Find process using a port
lsof -ti:<PORT>

# Kill process using port
lsof -ti:<PORT> | xargs kill -9

# Common conflicts:
# 5432 - Another PostgreSQL instance
# 8000 - Another Python/Node app
# 9090 - Another Prometheus instance
# 3000 - Node.js apps, other Grafana
```

### Service Management Commands (macOS)

```bash
# Start all services
brew services start postgresql@17
brew services start prometheus
brew services start grafana

# Stop all services
brew services stop grafana
brew services stop prometheus
brew services stop postgresql@17

# Restart a service
brew services restart <service-name>

# Check all services status
brew services list
```

---

## Troubleshooting Guide

### Issue: Port Already in Use

**Symptom:**
```
ERROR: [Errno 48] Address already in use
```

**Solution:**
```bash
# Find process using port
lsof -ti:8000

# Kill process
lsof -ti:8000 | xargs kill -9

# Or change port in config
```

---

### Issue: ModuleNotFoundError: No module named 'app'

**Symptom:**
```
ModuleNotFoundError: No module named 'app'
```

**Root Cause:** Incorrect module path in Makefile or Dockerfile

**Validation:**
```bash
# Check Makefile
grep "API_MODULE" Makefile
# Should show: API_MODULE = src.main:app

# Check Dockerfile
grep "CMD.*uvicorn" Dockerfile
# Should show: "src.main:app"
# Should NOT show: "app.main:app" or "${API_MODULE}"
```

---

### Issue: Database Connection Failed

**Symptom:**
```
"database": "unhealthy"
```

**Solutions:**

#### For Local Development:
```bash
# 1. Check PostgreSQL is running
pg_isready -h localhost
# If not: brew services start postgresql@17

# 2. Check credentials in .env.development
cat .env.development | grep POSTGRES

# 3. Test connection
psql -h localhost -U <POSTGRES_USER> -d <POSTGRES_DB> -c "SELECT 1"
```

#### For Docker:
```bash
# 1. Check db container is healthy
docker-compose ps db

# 2. Check db logs
docker-compose logs db

# 3. Check environment variables
docker-compose exec app env | grep POSTGRES
```

---

### Issue: Docker Volume Mount Not Working

**Symptom:** Code changes not reflected in Docker container

**Validation:**
```bash
# Check docker-compose.yml
grep -A3 "volumes:" docker-compose.yml | grep src
# Should show: - ./src:/app/src
# Should NOT show: - ./app:/app/src
```

**Solution:**
```bash
# 1. Fix volume mapping in docker-compose.yml
# 2. Rebuild and restart
make docker-stop ENV=development
make docker-run-env ENV=development
```

---

### Issue: OpenAI API Authentication Error

**Symptom:**
```
AuthenticationError: Invalid API key
```

**Validation:**
```bash
# Check API key is set
cat .env.development | grep OPENAI_API_KEY

# Verify format (should start with sk-)
# Check not a placeholder value
```

---

### Issue: pgvector Extension Not Found

**Symptom:**
```
ERROR: extension "vector" is not available
```

**Solution:**
```bash
# Local dev - install pgvector
brew install pgvector  # macOS
# or
sudo apt install postgresql-16-pgvector  # Ubuntu

# Enable in database
psql -h localhost -U postgres -d mydb -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

---

### Issue: Docker Build Fails - Out of Space

**Symptom:**
```
no space left on device
```

**Solution:**
```bash
# Clean up Docker system
docker system prune -a --volumes

# Check disk space
docker system df
```

---

### Issue: Hot Reload Not Working

**Symptom:** Code changes not triggering reload

**For Local Dev:**
```bash
# Ensure using --reload flag
grep "reload" Makefile
# dev target should have: --reload
```

**For Docker:**
```bash
# 1. Check volume is mounted
docker-compose exec app ls -la /app/src/

# 2. Check docker-compose command
docker-compose config | grep -A5 "app:" | grep command
# Should include --reload for development
```

---

## Quick Reference Commands

### Local Development
```bash
# Start
make dev

# Stop
Ctrl+C

# Health check
curl http://localhost:8000/health

# View docs
open http://localhost:8000/docs
```

### Docker
```bash
# Build
make docker-build-env ENV=development

# Start
make docker-run-env ENV=development

# Logs
make docker-logs ENV=development

# Stop
make docker-stop ENV=development

# Full stack
make docker-compose-up ENV=development
make docker-compose-down ENV=development
```

### Database
```bash
# Local
psql -h localhost -U postgres -d mydb

# Docker
docker-compose exec db psql -U ${POSTGRES_USER} -d ${POSTGRES_DB}

# Check tables
\dt

# Check users
SELECT * FROM "user";
```

---

## Validation Success Criteria

### ✅ Local Development Success
- [ ] `make dev` starts without errors
- [ ] Health endpoint returns healthy status
- [ ] Database connection successful
- [ ] Can register user and login
- [ ] Can send chat message and receive response
- [ ] Hot reload works when editing files
- [ ] No ERROR level logs in console

### ✅ Docker Success
- [ ] `make docker-build-env ENV=development` completes
- [ ] `make docker-run-env ENV=development` starts containers
- [ ] Both containers show "Up (healthy)" status
- [ ] Health endpoint returns healthy status
- [ ] Volume mount works (code changes detected)
- [ ] Can connect to database from host
- [ ] API endpoints work same as local dev

### ✅ Full Stack Success
- [ ] All services start (API, DB, Prometheus, Grafana, cAdvisor)
- [ ] No container restart loops
- [ ] Monitoring dashboards accessible
- [ ] Metrics being collected
- [ ] All health checks passing

### ✅ Observability Stack Success (Local Install)
- [ ] Prometheus installed and running (`brew services list`)
- [ ] Prometheus scraping FastAPI at http://localhost:9090/targets
- [ ] Grafana installed and running at http://localhost:3000
- [ ] Prometheus data source configured in Grafana
- [ ] Project dashboards imported from `grafana/dashboards/json/`
- [ ] Metrics visible in Grafana panels

---

## Maintenance Commands

### Clean Everything
```bash
# Stop all services
make docker-stop ENV=development

# Remove volumes
docker-compose down -v

# Clean Docker system
docker system prune -a

# Remove local .venv
make clean

# Start fresh
make install
make dev
```

### Check Disk Usage
```bash
# Docker disk usage
docker system df

# Local project size
du -sh .
```

### Update Dependencies
```bash
# Update uv packages
uv sync --upgrade

# Rebuild Docker image
make docker-build-env ENV=development --no-cache
```

---

**Document Version:** 1.1
**Last Validated:** January 23, 2026
