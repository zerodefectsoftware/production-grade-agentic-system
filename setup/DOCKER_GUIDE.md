# Docker Deployment Guide

This guide covers building, deploying, testing, and monitoring all services using Docker.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Environment Configuration](#environment-configuration)
- [Building Docker Images](#building-docker-images)
- [Running Services](#running-services)
- [Service Architecture](#service-architecture)
- [Observability Stack](#observability-stack)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [Command Reference](#command-reference)

---

## Prerequisites

- Docker Engine 20.10+
- Docker Compose v2.0+
- Make (for convenience commands)
- At least 4GB RAM available for Docker

Verify your installation:

```bash
docker --version
docker compose version
```

---

## Quick Start

```bash
# 1. Create environment file
cp .env.example .env.development

# 2. Edit .env.development with your API keys
#    Required: OPENAI_API_KEY, JWT_SECRET_KEY

# 3. Start the full stack
make docker-compose-up ENV=development

# 4. Verify services are running
docker ps

# 5. Access the services
#    - API:        http://localhost:8000
#    - API Docs:   http://localhost:8000/docs
#    - Grafana:    http://localhost:3000 (admin/admin)
#    - Prometheus: http://localhost:9090
#    - cAdvisor:   http://localhost:8080
```

---

## Environment Configuration

### Create Environment Files

Create environment-specific `.env` files based on your deployment target:

```bash
# Development
cp .env.example .env.development

# Staging
cp .env.example .env.staging

# Production
cp .env.example .env.production
```

### Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `OPENAI_API_KEY` | LLM API key | `sk-...` |
| `JWT_SECRET_KEY` | Secret for JWT tokens | `your-secure-secret-key` |
| `POSTGRES_PASSWORD` | Database password | `mypassword` |

### Optional Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_ENV` | `development` | Environment mode |
| `DEFAULT_LLM_MODEL` | `gpt-4o-mini` | LLM model to use |
| `POSTGRES_HOST` | `db` | Database host (use `db` for Docker) |
| `POSTGRES_PORT` | `5432` | Database port |
| `POSTGRES_DB` | `mydb` | Database name |
| `POSTGRES_USER` | `myuser` | Database user |
| `POSTGRES_POOL_SIZE` | `5` | Connection pool size |
| `LOG_LEVEL` | `DEBUG` | Logging level |
| `LANGFUSE_PUBLIC_KEY` | - | Langfuse public key (optional) |
| `LANGFUSE_SECRET_KEY` | - | Langfuse secret key (optional) |

### Environment-Specific Settings

**Development:**
```env
APP_ENV=development
DEBUG=true
LOG_LEVEL=DEBUG
LOG_FORMAT=console
POSTGRES_HOST=db
```

**Production:**
```env
APP_ENV=production
DEBUG=false
LOG_LEVEL=WARNING
LOG_FORMAT=json
POSTGRES_HOST=db
```

---

## Building Docker Images

### Build for Specific Environment

```bash
# Development
make docker-build-env ENV=development

# Staging
make docker-build-env ENV=staging

# Production
make docker-build-env ENV=production
```

### Manual Build

```bash
# Build with specific environment
docker build -t fastapi-langgraph-template --build-arg APP_ENV=development .

# Build with no cache (clean build)
docker build --no-cache -t fastapi-langgraph-template --build-arg APP_ENV=production .
```

### Build Details

The Dockerfile uses a multi-stage approach:
- Base image: `python:3.13.2-slim`
- Package manager: `uv` for fast dependency installation
- Non-root user: `appuser` for security
- Exposed port: `8000`

---

## Running Services

### Option 1: Full Stack (Recommended)

Starts all services: API, Database, Prometheus, Grafana, cAdvisor

```bash
# Start
make docker-compose-up ENV=development

# View logs
make docker-compose-logs ENV=development

# Stop
make docker-compose-down ENV=development
```

### Option 2: App + Database Only

Starts only the API and PostgreSQL database (no monitoring):

```bash
# Start
make docker-run-env ENV=development

# View logs
make docker-logs ENV=development

# Stop
make docker-stop ENV=development
```

### Option 3: Manual Docker Compose

```bash
# Start all services
APP_ENV=development docker-compose --env-file .env.development up -d

# Start specific services
APP_ENV=development docker-compose --env-file .env.development up -d app db

# Start with rebuild
APP_ENV=development docker-compose --env-file .env.development up -d --build

# Stop all services
APP_ENV=development docker-compose --env-file .env.development down

# Stop and remove volumes (WARNING: deletes data)
APP_ENV=development docker-compose --env-file .env.development down -v
```

---

## Service Architecture

### Services Overview

| Service | Port | Description |
|---------|------|-------------|
| `app` | 8000 | FastAPI application |
| `db` | 5432 | PostgreSQL with pgvector |
| `prometheus` | 9090 | Metrics collection |
| `grafana` | 3000 | Metrics visualization |
| `cadvisor` | 8080 | Container metrics |

### Network

All services communicate on the `monitoring` bridge network.

```
┌─────────────────────────────────────────────────────────────┐
│                    Docker Network: monitoring               │
│                                                             │
│  ┌─────────┐     ┌─────────┐     ┌────────────┐            │
│  │   app   │────▶│   db    │     │ prometheus │            │
│  │  :8000  │     │  :5432  │◀────│   :9090    │            │
│  └────┬────┘     └─────────┘     └─────┬──────┘            │
│       │                                │                    │
│       │ /metrics                       │                    │
│       └────────────────────────────────┘                    │
│                                        │                    │
│  ┌──────────┐     ┌──────────┐        │                    │
│  │ cadvisor │────▶│ grafana  │◀───────┘                    │
│  │  :8080   │     │  :3000   │                             │
│  └──────────┘     └──────────┘                             │
└─────────────────────────────────────────────────────────────┘
```

### Health Checks

**Database:**
```yaml
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
  interval: 10s
  timeout: 5s
  retries: 5
```

**Application:**
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 10s
```

---

## Observability Stack

### Prometheus

**Access:** http://localhost:9090

**Configuration:** `prometheus/prometheus.yml`

Prometheus scrapes metrics from:
- FastAPI app at `app:8000/metrics` (every 15s)
- cAdvisor at `cadvisor:8080` (every 15s)

**Available Metrics:**

| Metric | Type | Description |
|--------|------|-------------|
| `http_requests_total` | Counter | Total HTTP requests |
| `http_request_duration_seconds` | Histogram | Request latency |
| `llm_inference_duration_seconds` | Histogram | LLM call latency |
| `llm_stream_duration_seconds` | Histogram | Streaming LLM latency |
| `db_connections` | Gauge | Active DB connections |

**Example Queries:**

```promql
# Request rate per endpoint
rate(http_requests_total[5m])

# 95th percentile latency
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# LLM inference latency by model
histogram_quantile(0.95, rate(llm_inference_duration_seconds_bucket[5m]))

# Error rate
sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m]))
```

### Grafana

**Access:** http://localhost:3000

**Credentials:**
- Username: `admin`
- Password: `admin`

**Pre-configured Dashboards:**

Dashboards are auto-provisioned from `grafana/dashboards/json/`:
- `llm_latency.json` - LLM inference metrics

**Adding Prometheus Data Source:**

1. Go to Configuration → Data Sources
2. Add data source → Prometheus
3. URL: `http://prometheus:9090`
4. Click "Save & Test"

**Creating Custom Dashboards:**

1. Click + → Dashboard
2. Add visualization
3. Select Prometheus data source
4. Enter PromQL query
5. Save dashboard

### cAdvisor

**Access:** http://localhost:8080

Provides container-level metrics:
- CPU usage per container
- Memory usage per container
- Network I/O
- Filesystem usage

---

## Testing

### Health Check

```bash
# Check API health
curl http://localhost:8000/health

# Expected response
{"status": "healthy", "database": "connected"}
```

### API Endpoints

```bash
# View API documentation
open http://localhost:8000/docs

# Register a user
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "testpass123"}'

# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "testpass123"}'

# Chat (with token)
curl -X POST http://localhost:8000/api/chatbot/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your-token>" \
  -d '{"message": "Hello!", "session_id": "test-session"}'
```

### Metrics Endpoint

```bash
# View raw Prometheus metrics
curl http://localhost:8000/metrics
```

### Container Status

```bash
# Check all containers
docker ps

# Check container health
docker inspect --format='{{.State.Health.Status}}' production-grade-agentic-system-app-1

# View container resource usage
docker stats
```

### Database Connection

```bash
# Connect to PostgreSQL
docker exec -it production-grade-agentic-system-db-1 psql -U myuser -d mydb

# List tables
\dt

# Check checkpoint tables
SELECT * FROM checkpoints LIMIT 5;
```

### Running Evaluations

```bash
# Interactive evaluation
make eval

# Quick evaluation
make eval-quick

# Evaluation without report
make eval-no-report
```

---

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker logs production-grade-agentic-system-app-1

# Check if port is in use
lsof -i :8000

# Rebuild from scratch
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```

### Database Connection Issues

```bash
# Verify database is running
docker logs production-grade-agentic-system-db-1

# Check database health
docker exec production-grade-agentic-system-db-1 pg_isready -U myuser -d mydb

# Verify network connectivity
docker exec production-grade-agentic-system-app-1 ping db
```

### Missing Environment Variables

```bash
# Error: "required environment variables are missing"
# Solution: Ensure .env.development has:
#   - OPENAI_API_KEY
#   - JWT_SECRET_KEY

# Check what's loaded
docker exec production-grade-agentic-system-app-1 env | grep -E "(OPENAI|JWT)"
```

### Prometheus Not Scraping Metrics

```bash
# Check Prometheus targets
open http://localhost:9090/targets

# Verify app metrics endpoint
curl http://localhost:8000/metrics

# Check Prometheus logs
docker logs production-grade-agentic-system-prometheus-1
```

### Grafana Dashboard Not Loading

```bash
# Check Grafana logs
docker logs production-grade-agentic-system-grafana-1

# Verify dashboard files exist
ls -la grafana/dashboards/json/

# Restart Grafana
docker restart production-grade-agentic-system-grafana-1
```

### Out of Memory

```bash
# Check container memory usage
docker stats

# Increase Docker memory limit in Docker Desktop settings
# Or reduce pool sizes in .env:
POSTGRES_POOL_SIZE=3
POSTGRES_MAX_OVERFLOW=5
```

### Clean Restart

```bash
# Nuclear option: remove everything and start fresh
docker-compose down -v
docker system prune -af
make docker-compose-up ENV=development
```

---

## Command Reference

### Make Commands

| Command | Description |
|---------|-------------|
| `make docker-build-env ENV=<env>` | Build Docker image |
| `make docker-run-env ENV=<env>` | Run app + database |
| `make docker-logs ENV=<env>` | View app/db logs |
| `make docker-stop ENV=<env>` | Stop app + database |
| `make docker-compose-up ENV=<env>` | Start full stack |
| `make docker-compose-down ENV=<env>` | Stop full stack |
| `make docker-compose-logs ENV=<env>` | View all logs |

### Docker Commands

```bash
# List running containers
docker ps

# List all containers (including stopped)
docker ps -a

# View logs (follow)
docker logs -f <container-name>

# Execute command in container
docker exec -it <container-name> bash

# View container stats
docker stats

# Remove all stopped containers
docker container prune

# Remove unused images
docker image prune

# Remove unused volumes
docker volume prune

# Remove everything unused
docker system prune -af
```

### Docker Compose Commands

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Restart a service
docker-compose restart <service>

# Scale a service
docker-compose up -d --scale app=3

# View service logs
docker-compose logs -f <service>

# Execute command in service
docker-compose exec <service> <command>
```

---

## Volumes and Data Persistence

### Persistent Volumes

| Volume | Mount Point | Purpose |
|--------|-------------|---------|
| `postgres-data` | `/var/lib/postgresql/data` | Database storage |
| `grafana-storage` | `/var/lib/grafana` | Grafana dashboards/settings |

### Backup Database

```bash
# Create backup
docker exec production-grade-agentic-system-db-1 pg_dump -U myuser mydb > backup.sql

# Restore backup
cat backup.sql | docker exec -i production-grade-agentic-system-db-1 psql -U myuser mydb
```

### Clear Data

```bash
# Remove all data (WARNING: destructive)
docker-compose down -v
```

---

## Production Considerations

1. **Secrets Management**: Use Docker secrets or external vault instead of `.env` files
2. **SSL/TLS**: Add nginx reverse proxy with SSL termination
3. **Scaling**: Use Docker Swarm or Kubernetes for horizontal scaling
4. **Logging**: Forward logs to centralized logging (ELK, Loki)
5. **Backups**: Implement automated database backups
6. **Monitoring Alerts**: Configure Prometheus alertmanager
7. **Resource Limits**: Set memory/CPU limits in docker-compose.yml

```yaml
# Example resource limits
services:
  app:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 512M
```
