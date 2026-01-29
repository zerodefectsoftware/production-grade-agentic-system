# Hairstyle Recommendations API - Design Document

## Overview

A production-grade API for AI-powered hairstyle recommendations, built as a parallel application within the existing agentic system repository.

**Status:** Design Complete
**Target:** MVP1 (Recommendations)
**Date:** January 2026

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [MVP Roadmap](#mvp-roadmap)
3. [Technical Stack](#technical-stack)
4. [Folder Structure](#folder-structure)
5. [Database Design](#database-design)
6. [API Endpoints](#api-endpoints)
7. [LangGraph Workflow](#langgraph-workflow)
8. [Delivery Methods](#delivery-methods)
9. [Image Lifecycle](#image-lifecycle)
10. [Resilience Patterns](#resilience-patterns)
11. [LLM Integration](#llm-integration)
12. [Configuration](#configuration)
13. [Client Implementation](#client-implementation)
14. [Future Considerations](#future-considerations)

---

## Architecture Overview

### Deployment Model

```
/production-grade-agentic-system
├── /src                    ← Chatbot API (port 8000) - reference only
├── /hairstyle              ← Hairstyle API (port 8001) - new production app
```

- **Separate FastAPI applications** on different ports
- **Separate databases** (chatbot_db, hairstyle_db)
- **Shared JWT secret** for single sign-on (Hairstyle owns users)
- **Independent deployment** - both can run simultaneously

### High-Level Flow

```
┌─────────────────────┐
│  Chatbot Playground │──────┐
│  (Web UI - testing) │      │
└─────────────────────┘      │
                             ▼
                    ┌─────────────────┐
                    │  Hairstyle API  │  ← Port 8001
                    │  /hairstyle     │
                    └─────────────────┘
                             ▲
┌─────────────────────┐      │
│  Mobile App         │──────┘
│  (iOS/Android)      │
└─────────────────────┘
```

---

## MVP Roadmap

| MVP | Scope | Features |
|-----|-------|----------|
| **MVP1** | Recommendations | Photo upload → AI analysis → N hairstyle images |
| **MVP2** | Customization | Select recommendation → modify (color, parting, etc.) |
| **MVP3** | Chat | Conversational AI stylist for refinement |

---

## Technical Stack

| Component | Technology |
|-----------|------------|
| Framework | FastAPI |
| Agent Orchestration | LangGraph |
| Database | PostgreSQL |
| Primary LLM | Gemini 2.5/3 (Gemini SDK) - lower cost |
| Fallback LLMs | Grok (OpenAI SDK), OpenAI (native SDK) |
| LLM SDK Strategy | OpenAI SDK when compatible, provider SDK when not |
| Checkpointing | AsyncPostgresSaver (LangGraph) |
| Tracing | Langfuse |
| Observability | Prometheus + Grafana |
| Auth | JWT (shared secret with chatbot) |

---

## Folder Structure

```
/hairstyle
├── main.py                    # FastAPI app entry point (port 8001)
│
├── /agent
│   ├── workflow.py            # LangGraph workflow definition
│   ├── state.py               # HairstyleState TypedDict
│   ├── /nodes
│   │   ├── validate.py        # Input validation, job creation
│   │   ├── generate_prompts.py # LLM: photo → hairstyle prompts
│   │   ├── generate_images.py  # LLM: parallel image generation
│   │   └── finalize.py        # Update job status, emit completion
│   └── /prompts
│       └── hairstyle_system.md # System prompt for hairstyle generation
│
├── /interface
│   ├── router.py              # Main router aggregating all routes
│   ├── auth.py                # Register, login endpoints
│   ├── recommend.py           # POST /recommend
│   ├── jobs.py                # GET /jobs/{id}, GET /jobs/{id}/stream
│   ├── images.py              # GET/POST/DELETE /images
│   └── albums.py              # Album management endpoints
│
├── /services
│   ├── llm_service.py         # LLM orchestration, fallback chain
│   ├── /providers             # Provider-specific implementations
│   │   ├── __init__.py
│   │   ├── base.py            # HairstyleProvider protocol
│   │   ├── gemini.py          # Gemini SDK implementation
│   │   ├── grok.py            # Grok (OpenAI SDK) implementation
│   │   └── openai.py          # OpenAI implementation
│   ├── image_service.py       # Image storage/retrieval
│   └── job_service.py         # Job management, SSE event publishing
│
├── /data
│   ├── db_manager.py          # Database connection, pooling
│   ├── /models
│   │   ├── user.py
│   │   ├── session.py
│   │   ├── job.py
│   │   ├── image.py
│   │   └── album.py
│   └── /schemas
│       ├── auth.py            # RegisterRequest, LoginRequest, TokenResponse
│       ├── recommend.py       # RecommendRequest, RecommendSyncResponse, RecommendAsyncResponse
│       └── job.py             # JobStatusResponse, ImageResult
│
├── /system
│   ├── logs.py                # Structured logging (structlog)
│   ├── middleware.py          # Logging context, metrics middleware
│   ├── rate_limit.py          # Rate limiting configuration
│   └── telemetry.py           # Prometheus metrics
│
├── /utils
│   ├── auth.py                # JWT utilities, password hashing
│   └── image.py               # Base64 encode/decode utilities
│
└── /config
    └── settings.py            # Environment-specific settings
```

---

## Database Design

### Schema: `hairstyle_db`

```
┌──────────────┐       ┌──────────────┐
│    users     │       │ device_tokens│
├──────────────┤       ├──────────────┤
│ id (PK)      │──┐    │ id (PK)      │
│ email        │  │    │ user_id (FK) │
│ password_hash│  │    │ token        │
│ created_at   │  │    │ platform     │
└──────────────┘  │    │ created_at   │
                  │    └──────────────┘
       ┌──────────┴──────────┐
       │                     │
       ▼                     ▼
┌──────────────┐      ┌──────────────┐
│   sessions   │      │   albums     │
├──────────────┤      ├──────────────┤
│ id (PK)      │      │ id (PK)      │
│ user_id (FK) │      │ user_id (FK) │
│ name         │      │ name         │
│ context      │      │ created_at   │
│ created_at   │      └──────────────┘
│ updated_at   │             │
└──────────────┘             │
       │                     │
       ▼                     │
┌──────────────┐             │
│    jobs      │             │
├──────────────┤             │
│ id (PK)      │             │
│ session_id   │             │
│ type         │ ← "recommend" | "customize"
│ status       │ ← "pending" | "processing" | "completed" | "partial" | "failed"
│ preferences  │ ← JSON: {count, occasion}
│ input_photo  │ ← binary (user's selfie)
│ analysis     │ ← "Oval face, wavy hair..."
│ created_at   │             │
│ completed_at │             │
└──────────────┘             │
       │                     │
       ▼                     │
┌──────────────┐             │
│   images     │ <───────────┘
├──────────────┤
│ id (PK)      │
│ job_id (FK)  │
│ album_id (FK)│ ← nullable
│ image_data   │ ← binary (PostgreSQL for MVP, S3 later)
│ image_url    │ ← for S3 migration
│ prompt       │ ← prompt that generated this image
│ type         │ ← "selfie" | "generated" | "customized"
│ is_saved     │ ← false until user explicitly saves
│ expires_at   │ ← now + 24h (NULL when saved)
│ created_at   │
└──────────────┘
```

### Table Purposes

| Table | Purpose |
|-------|---------|
| **users** | Authentication (Hairstyle owns users for now) |
| **sessions** | Long-lived context, LangGraph checkpointing |
| **jobs** | Individual async tasks (recommend/customize) |
| **images** | Generated hairstyles with lifecycle management |
| **albums** | User collections (default "My Styles" per user) |
| **device_tokens** | Push notification registration (MVP2+) |

### Image Types

```python
class ImageType(str, Enum):
    SELFIE = "selfie"           # User uploaded photo
    GENERATED = "generated"     # AI generated hairstyle
    CUSTOMIZED = "customized"   # User customized hairstyle
```

---

## API Endpoints

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | Create account |
| POST | `/auth/login` | Get JWT token |

### Sessions

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/sessions` | Create new session |
| GET | `/sessions` | List user's sessions |
| GET | `/sessions/{id}` | Get session details |
| DELETE | `/sessions/{id}` | Delete session |

### Recommendations (MVP1)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/recommend` | Submit recommendation job |
| GET | `/jobs/{id}` | Poll job status |
| GET | `/jobs/{id}/stream` | SSE stream for real-time delivery |

### Images

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/images/{id}` | Get image (serves binary) |
| POST | `/images` | Save image to album |
| DELETE | `/images/{id}` | Delete image |

### Albums

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/albums` | List user's albums |
| POST | `/albums/{id}/images` | Add image to album |
| DELETE | `/albums/{id}/images/{img_id}` | Remove from album |

### Request/Response Schemas

#### Recommend Request

```json
POST /recommend
{
  "session_id": "uuid",           // optional, creates new if not provided
  "photo": "base64...",
  "preferences": {
    "count": 3,                   // default: 3, max: 5
    "occasion": "wedding"         // optional
  },
  "delivery": "sse"               // "sse" | "sync" | "polling"
}
```

#### Async Response (SSE/Polling)

```json
HTTP 202 Accepted
{
  "job_id": "uuid",
  "session_id": "uuid",
  "status": "pending",
  "stream_url": "/jobs/{job_id}/stream",
  "poll_url": "/jobs/{job_id}"
}
```

#### Sync Response

```json
HTTP 200 OK
{
  "job_id": "uuid",
  "session_id": "uuid",
  "status": "completed",
  "analysis": "Oval face, wavy dark hair...",
  "results": [
    { "id": "uuid", "url": "/images/uuid", "prompt": "..." },
    { "id": "uuid", "url": "/images/uuid", "prompt": "..." },
    { "id": "uuid", "url": "/images/uuid", "prompt": "..." }
  ],
  "errors": []
}
```

#### SSE Events

```
event: analysis
data: {"text": "Oval face, wavy dark hair..."}

event: progress
data: {"completed": 1, "total": 3}

event: image
data: {"id": "uuid", "url": "/images/uuid", "prompt": "..."}

event: complete
data: {"job_id": "uuid", "status": "completed", "total": 3}

event: error
data: {"message": "1 of 3 images failed", "completed": 2}
```

---

## LangGraph Workflow

### MVP1: Recommend Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                MVP1: RECOMMEND WORKFLOW                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   START                                                         │
│     │                                                           │
│     ▼                                                           │
│  ┌──────────────┐                                               │
│  │ validate     │  → Check photo, preferences, create job       │
│  └──────────────┘                                               │
│     │                                                           │
│     ▼                                                           │
│  ┌──────────────┐                                               │
│  │ generate     │  → 1 LLM call: photo + prompt → N prompts     │
│  │ _prompts     │    (also returns analysis, stored in job)     │
│  └──────────────┘                                               │
│     │                                                           │
│     ▼                                                           │
│  ┌──────────────┐                                               │
│  │ generate     │  → Fan-out: N parallel image generations      │
│  │ _images      │  → Each image saved to DB, SSE event emitted  │
│  └──────────────┘                                               │
│     │                                                           │
│     ▼                                                           │
│  ┌──────────────┐                                               │
│  │ finalize     │  → Update job status, emit complete event     │
│  └──────────────┘                                               │
│     │                                                           │
│     ▼                                                           │
│   END                                                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### LLM Calls

| Call | Purpose | Model | Input | Output |
|------|---------|-------|-------|--------|
| 1 | Generate prompts + analysis | Gemini Flash 2.5 | Photo + system prompt + preferences | N hairstyle prompts + analysis |
| 2 to N+1 | Generate images (parallel) | Gemini Flash 2.5 | Original photo + prompt | Edited image |

**Total: 1 + N calls per request**

### State Schema

```python
class HairstyleState(TypedDict):
    # Identity
    user_id: str
    job_id: str
    session_id: str

    # Input
    photo: str              # Base64 encoded
    preferences: dict       # {count: 3, occasion: "wedding"}

    # Processing
    analysis: str           # "Oval face, wavy hair..."
    prompts: list[str]      # Generated hairstyle prompts

    # Output
    images: list[dict]      # [{id, url, prompt}, ...]

    # Delivery
    delivery_method: str    # "sse" | "sync" | "polling"

    # Status
    status: str             # "pending" | "processing" | "completed" | "partial" | "failed"
    errors: list[str]       # Track failures for partial results
```

---

## Delivery Methods

### Comparison

| Mode | Use Case | Behavior | Response Time |
|------|----------|----------|---------------|
| `sse` | Web UI, real-time progress | Return 202, stream via SSE | Immediate + stream |
| `sync` | Simple clients, testing | Wait for all images | 30-90 seconds |
| `polling` | Mobile apps, unreliable connections | Return 202, client polls | Immediate + poll |

### Flow Diagrams

#### SSE Mode

```
Client                              Server
  │                                   │
  │─── POST /recommend ──────────────>│
  │<── 202 {job_id, stream_url} ──────│
  │                                   │
  │─── GET /jobs/{id}/stream ────────>│
  │<── SSE: analysis ─────────────────│
  │<── SSE: image (1) ────────────────│
  │<── SSE: progress ─────────────────│
  │<── SSE: image (2) ────────────────│
  │<── SSE: image (3) ────────────────│
  │<── SSE: complete ─────────────────│
```

#### Sync Mode

```
Client                              Server
  │                                   │
  │─── POST /recommend ──────────────>│
  │         (waits 30-90s)            │
  │<── 200 {results: [...]} ──────────│
```

#### Polling Mode

```
Client                              Server
  │                                   │
  │─── POST /recommend ──────────────>│
  │<── 202 {job_id, poll_url} ────────│
  │                                   │
  │─── GET /jobs/{id} ───────────────>│
  │<── {status: "processing"} ────────│
  │                                   │
  │─── GET /jobs/{id} ───────────────>│
  │<── {status: "completed", ...} ────│
```

---

## Image Lifecycle

### Hybrid Approach: Temp + Permanent Storage

```
┌─────────────────────────────────────────────────────────────────┐
│                    IMAGE LIFECYCLE                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Generate image                                                 │
│       │                                                         │
│       ▼                                                         │
│  Save to DB:                                                    │
│    - is_saved = false                                           │
│    - expires_at = now + 24 hours                                │
│       │                                                         │
│       ▼                                                         │
│  Return via SSE/response:                                       │
│    { "id": "uuid", "url": "/images/uuid", "prompt": "..." }     │
│       │                                                         │
│       ├──► User saves to album:                                 │
│       │      - is_saved = true                                  │
│       │      - expires_at = NULL                                │
│       │      - album_id = assigned                              │
│       │                                                         │
│       └──► User doesn't save:                                   │
│              - Cleanup job deletes after 24h                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Cleanup Job

```sql
-- Run daily
DELETE FROM images
WHERE is_saved = FALSE
AND expires_at < NOW();
```

### Benefits

- User can "go back" to previous recommendations (within 24h)
- Small SSE payloads (URLs, not base64)
- Multi-device access
- No wasted permanent storage for unwanted images
- Analytics possible on temporary data

---

## Resilience Patterns

### Stack

```
┌─────────────┐
│   Retry     │  Exponential backoff (from chatbot)
│  (tenacity) │
└─────────────┘
       │
       ▼
┌─────────────┐
│  Circuit    │  Prevent cascading failures (from chatbot)
│  Breaker    │
└─────────────┘
       │
       ▼
┌─────────────┐
│  Fallback   │  Gemini 2.5 → Gemini 3.0 → Others
│   Model     │
└─────────────┘
       │
       ▼
┌─────────────┐
│  Timeout    │  Prompt: 30s, Image: 60s
└─────────────┘
```

### Partial Failure Handling

```python
# N parallel image generations
results = []
errors = []

for coro in asyncio.as_completed(image_tasks):
    try:
        image = await coro
        await save_to_db(image)       # Must succeed before emit
        await emit_sse("image", image)
        results.append(image)
    except Exception as e:
        errors.append(str(e))
        await emit_sse("error", {"message": f"1 image failed"})

# Final status
status = "completed" if not errors else "partial" if results else "failed"
```

### SSE Disconnection

- Server detects disconnect
- Job continues processing (images saved to DB)
- Client reconnects → polls `/jobs/{id}` → gets results
- No work is lost - DB is source of truth

---

## LLM Integration

### Design Principle

```
┌─────────────────────────────────────────────────────────────────┐
│                    SDK SELECTION PRINCIPLE                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   1. USE OpenAI SDK (standard) when provider supports it        │
│      └── Grok, OpenAI, others with compatible endpoints         │
│                                                                 │
│   2. USE Provider SDK when OpenAI compatibility falls short     │
│      └── Gemini (for full multi-modal + image editing)          │
│                                                                 │
│   3. WRAP all in provider-agnostic abstraction                  │
│      └── Your code calls abstraction, not SDK directly          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Why Multiple Providers?

- **Lower cost to users** - Gemini 2.5 is cost-effective, use premium models only when needed
- **Decent fallback** - If primary fails, seamlessly switch to alternative
- **Provider flexibility** - Not locked to single vendor

### Supported Providers

| Provider | Priority | Why |
|----------|----------|-----|
| **Gemini 2.5/3** | Primary | Validated in prototype, lower cost, strong image capabilities |
| **Grok (xAI)** | Secondary | OpenAI SDK compatible, strong image editing |
| **OpenAI** | Tertiary | Reliable fallback, DALL-E for images |

### Provider Capability Matrix

| Capability | Gemini | Grok | OpenAI |
|------------|--------|------|--------|
| Text Generation | Yes | Yes | Yes |
| Vision (Image → Text) | Yes | Yes | Yes |
| Image Editing | Yes | Yes | Yes (DALL-E) |
| Multi-modal Input | Yes | Yes | Yes |
| Base64 Response | Yes | Yes | Yes |
| Thinking/Reasoning | Yes (Gemini 3) | Yes | Yes |

### SDK Compatibility Matrix

| Provider | Text/Vision | Image Editing | SDK Used |
|----------|-------------|---------------|----------|
| **Gemini** | Gemini SDK | Gemini SDK | `google-generativeai` |
| **Grok** | OpenAI SDK | OpenAI SDK | `openai` (base_url: api.x.ai) |
| **OpenAI** | OpenAI SDK | OpenAI SDK | `openai` |

### Gemini 2.5 vs 3.0 Compatibility

| Aspect | Gemini 2.5 | Gemini 3 |
|--------|------------|----------|
| Thinking | Supported | Enhanced |
| Thought Signatures | Optional | Mandatory (strict) |
| `thinking_budget` | Supported | Backward compatible |
| `thinking_level` | N/A | New (recommended) |
| Image Editing | Yes | Yes (strict signature validation) |
| SDK Handles Signatures | Yes | Yes (automatic) |

**Migration path:** Change model string + add `thinking_level` config. SDK handles complexity.

### Provider Abstraction

```python
# services/providers/base.py

from typing import Protocol

class HairstyleProvider(Protocol):
    """Provider-agnostic interface for Hairstyle API."""

    async def analyze_and_generate_prompts(
        self,
        image: bytes,
        preferences: dict
    ) -> tuple[str, list[str]]:
        """
        Multi-modal: Image + Text → Text

        Input: User photo + preferences
        Output: (analysis, list of hairstyle prompts)
        """
        ...

    async def edit_image(
        self,
        image: bytes,
        prompt: str
    ) -> bytes:
        """
        Image editing: Image + Text → Image

        Input: User photo + hairstyle prompt
        Output: Edited image with new hairstyle
        """
        ...
```

### Provider Implementations

#### Gemini Provider (Native SDK)

```python
# services/providers/gemini.py
from google import generativeai as genai

class GeminiProvider:
    """Gemini SDK - provider-specific (OpenAI SDK insufficient for images)."""

    def __init__(self, api_key: str, model: str = "gemini-2.5-flash"):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)

    async def analyze_and_generate_prompts(self, image: bytes, preferences: dict):
        response = await self.model.generate_content_async([
            {"mime_type": "image/jpeg", "data": image},
            f"Analyze this face and suggest {preferences['count']} hairstyles..."
        ])
        return self._parse_response(response.text)

    async def edit_image(self, image: bytes, prompt: str):
        response = await self.model.generate_content_async([
            {"mime_type": "image/jpeg", "data": image},
            f"Edit this photo to show: {prompt}"
        ])
        return response.parts[0].inline_data.data
```

#### Grok Provider (OpenAI SDK Compatible)

```python
# services/providers/grok.py
from openai import AsyncOpenAI

class GrokProvider:
    """Grok via OpenAI SDK - fully compatible."""

    def __init__(self, api_key: str):
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url="https://api.x.ai/v1"
        )

    async def analyze_and_generate_prompts(self, image: bytes, preferences: dict):
        response = await self.client.chat.completions.create(
            model="grok-2-vision",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{...}"}},
                    {"type": "text", "text": f"Analyze and suggest {preferences['count']} hairstyles..."}
                ]
            }]
        )
        return self._parse_response(response.choices[0].message.content)

    async def edit_image(self, image: bytes, prompt: str):
        response = await self.client.images.edit(
            model="grok-imagine-image",
            image=image,
            prompt=prompt,
            response_format="b64_json"
        )
        return base64.b64decode(response.data[0].b64_json)
```

#### OpenAI Provider (Native SDK)

```python
# services/providers/openai.py
from openai import AsyncOpenAI

class OpenAIProvider:
    """OpenAI native SDK."""

    def __init__(self, api_key: str, text_model: str = "gpt-4o", image_model: str = "dall-e-3"):
        self.client = AsyncOpenAI(api_key=api_key)
        self.text_model = text_model
        self.image_model = image_model

    async def analyze_and_generate_prompts(self, image: bytes, preferences: dict):
        response = await self.client.chat.completions.create(
            model=self.text_model,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{...}"}},
                    {"type": "text", "text": f"Analyze and suggest {preferences['count']} hairstyles..."}
                ]
            }]
        )
        return self._parse_response(response.choices[0].message.content)

    async def edit_image(self, image: bytes, prompt: str):
        response = await self.client.images.edit(
            model=self.image_model,
            image=image,
            prompt=prompt
        )
        return await self._download_image(response.data[0].url)
```

### LLM Service (Orchestration with Fallback)

```python
# services/llm_service.py

class LLMService:
    """Orchestrates providers with fallback chain."""

    def __init__(self, settings):
        self.providers: list[HairstyleProvider] = []

        # Priority order: primary → fallback
        if settings.GEMINI_API_KEY:
            self.providers.append(GeminiProvider(
                api_key=settings.GEMINI_API_KEY,
                model=settings.GEMINI_MODEL  # gemini-2.5-flash or gemini-3-pro
            ))

        if settings.GROK_API_KEY:
            self.providers.append(GrokProvider(
                api_key=settings.GROK_API_KEY
            ))

        if settings.OPENAI_API_KEY:
            self.providers.append(OpenAIProvider(
                api_key=settings.OPENAI_API_KEY
            ))

    @with_retry
    @with_circuit_breaker
    async def analyze_and_generate_prompts(self, image: bytes, preferences: dict):
        return await self._call_with_fallback(
            "analyze_and_generate_prompts",
            image=image,
            preferences=preferences
        )

    @with_retry
    @with_circuit_breaker
    async def edit_image(self, image: bytes, prompt: str):
        return await self._call_with_fallback(
            "edit_image",
            image=image,
            prompt=prompt
        )

    async def _call_with_fallback(self, method: str, **kwargs):
        last_error = None
        for provider in self.providers:
            try:
                fn = getattr(provider, method)
                return await fn(**kwargs)
            except Exception as e:
                logger.warning(f"{provider.__class__.__name__} failed: {e}")
                last_error = e
                continue
        raise AllProvidersFailedError(last_error)
```

### Folder Structure for Providers

```
/hairstyle
└── /services
    ├── llm_service.py          # Orchestration, fallback logic
    └── /providers
        ├── __init__.py
        ├── base.py             # HairstyleProvider protocol
        ├── gemini.py           # Gemini SDK implementation
        ├── grok.py             # Grok (OpenAI SDK) implementation
        └── openai.py           # OpenAI implementation
```

### Environment Variables for Providers

```bash
# Primary - Gemini (lower cost)
GEMINI_API_KEY=your-gemini-key
GEMINI_MODEL=gemini-2.5-flash          # or gemini-3-pro
GEMINI_THINKING_LEVEL=medium           # for Gemini 3

# Secondary - Grok
GROK_API_KEY=your-xai-key

# Tertiary - OpenAI
OPENAI_API_KEY=your-openai-key
OPENAI_TEXT_MODEL=gpt-4o
OPENAI_IMAGE_MODEL=dall-e-3
```

### LLM Integration Summary

| Aspect | Decision |
|--------|----------|
| **Primary Provider** | Gemini 2.5/3 (Gemini SDK) - lower cost |
| **Secondary Provider** | Grok (OpenAI SDK compatible) |
| **Tertiary Provider** | OpenAI (native SDK) |
| **SDK Principle** | OpenAI SDK when compatible, provider SDK when not |
| **Abstraction** | `HairstyleProvider` protocol |
| **Operations** | `analyze_and_generate_prompts`, `edit_image` |
| **Resilience** | Retry + Circuit breaker + Fallback chain |
| **Gemini Migration** | 2.5 → 3: Change model string, SDK handles signatures |

---

## Configuration

### Environment File: `.env.hairstyle.development`

```bash
# App
APP_ENV=development
HAIRSTYLE_PORT=8001
HAIRSTYLE_HOST=0.0.0.0
API_V1_STR=/api/v1

# Database
HAIRSTYLE_DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/hairstyle_db
POSTGRES_POOL_SIZE=5
POSTGRES_MAX_OVERFLOW=10

# Auth (shared with chatbot)
JWT_SECRET_KEY=your-secret-key
JWT_ACCESS_TOKEN_EXPIRE_DAYS=7

# LLM - Primary (Gemini - lower cost)
GEMINI_API_KEY=your-gemini-key
GEMINI_MODEL=gemini-2.5-flash
GEMINI_THINKING_LEVEL=medium
GEMINI_TIMEOUT=60

# LLM - Secondary (Grok - OpenAI SDK compatible)
GROK_API_KEY=your-xai-key
GROK_TIMEOUT=60

# LLM - Tertiary (OpenAI - fallback)
OPENAI_API_KEY=your-openai-key
OPENAI_TEXT_MODEL=gpt-4o
OPENAI_IMAGE_MODEL=dall-e-3
OPENAI_TIMEOUT=90

# Resilience (copy from chatbot)
LLM_MAX_RETRIES=3
LLM_RETRY_BACKOFF=1
CIRCUIT_BREAKER_THRESHOLD=5
CIRCUIT_BREAKER_TIMEOUT=30

# Image Settings
MAX_IMAGE_SIZE_MB=10
IMAGE_EXPIRY_HOURS=24
DEFAULT_RECOMMENDATION_COUNT=3
MAX_RECOMMENDATION_COUNT=5

# Rate Limiting
RATE_LIMIT_RECOMMEND="10 per minute"
RATE_LIMIT_SAVE="30 per minute"

# Observability
LANGFUSE_PUBLIC_KEY=your-key
LANGFUSE_SECRET_KEY=your-secret
LANGFUSE_HOST=https://cloud.langfuse.com
LOG_LEVEL=DEBUG
```

### Makefile Commands

```makefile
# Hairstyle API
dev-hairstyle:
	APP_ENV=development uvicorn hairstyle.main:app --port 8001 --reload

# Chatbot (reference)
dev-chatbot:
	APP_ENV=development uvicorn src.main:app --port 8000 --reload

# Both
dev-all:
	make dev-chatbot & make dev-hairstyle
```

---

## Client Implementation

### JavaScript (Web)

```javascript
async function getRecommendations(photo, preferences) {
  // 1. Submit request
  const response = await fetch('/api/v1/recommend', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({
      photo: photo,
      preferences: preferences,
      delivery: 'sse'
    })
  });

  const { job_id, stream_url } = await response.json();

  // 2. Connect to SSE
  const eventSource = new EventSource(stream_url);

  eventSource.addEventListener('image', (event) => {
    const data = JSON.parse(event.data);
    addImageToUI(data.url, data.prompt);
  });

  eventSource.addEventListener('complete', () => {
    eventSource.close();
  });
}
```

### React Hook

```javascript
function useHairstyleRecommendation() {
  const [images, setImages] = useState([]);
  const [status, setStatus] = useState('idle');

  const recommend = async (photo, preferences) => {
    setStatus('streaming');
    const res = await api.post('/recommend', { photo, preferences, delivery: 'sse' });
    const es = new EventSource(res.data.stream_url);

    es.addEventListener('image', (e) => {
      setImages(prev => [...prev, JSON.parse(e.data)]);
    });

    es.addEventListener('complete', () => {
      setStatus('completed');
      es.close();
    });
  };

  return { recommend, images, status };
}
```

---

## Future Considerations

### Auth Service (Future MVP)

When adding more services (Virtual Tryon, etc.):

```
┌─────────────┐
│ Auth Service│ ← Owns users, issues tokens
└─────────────┘
       │
       ├──► Hairstyle API
       ├──► Virtual Tryon API
       └──► Service N
```

### S3 Migration

When ready to scale image storage:

1. Add S3 client configuration
2. Upload images to S3
3. Populate `image_url` field
4. Optionally clear `image_data` (binary)
5. Client always uses URL - no changes needed

### Push Notifications (MVP2+)

1. Set up Firebase project
2. Add Firebase Admin SDK
3. Implement device token registration
4. Send notifications when jobs complete

---

## Summary

| Aspect | Decision |
|--------|----------|
| Location | `/hairstyle` folder, port 8001 |
| Database | Separate `hairstyle_db` |
| Auth | Shared JWT, Hairstyle owns users |
| Orchestration | LangGraph (4 nodes for MVP1) |
| Delivery | SSE (primary), Sync, Polling |
| Image Storage | PostgreSQL (MVP), S3 (later) |
| Image Lifecycle | 24h expiry for unsaved, permanent when saved |
| Resilience | Retry + Circuit Breaker + Fallback chain |
| LLM Primary | Gemini 2.5/3 (Gemini SDK) - lower cost |
| LLM Secondary | Grok (OpenAI SDK compatible) |
| LLM Tertiary | OpenAI (native SDK) |
| SDK Strategy | OpenAI SDK when compatible, provider SDK when not |
| Multi-Provider Reason | Lower cost to users + reliable fallback |
