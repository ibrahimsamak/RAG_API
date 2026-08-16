# AI RAG API

A production-shaped **FastAPI** service that ends in a real **Retrieval-Augmented Generation (RAG)** API with **token streaming over Server-Sent Events**. It combines a fully async data layer, OAuth2/JWT auth with RBAC, structured logging, caching, and containerization — then layers a ChromaDB-backed RAG pipeline and a streaming `/chat` endpoint on top.

---

## Stack

```
FastAPI (async)  ·  Pydantic v2  ·  SQLAlchemy 2.0 (async)  ·  Alembic
PostgreSQL (asyncpg)  ·  JWT / OAuth2  ·  slowapi (rate limiting)
ChromaDB (vector store)  ·  OpenAI (embeddings + streaming chat)  ·  Docker
```

- **App runtime driver:** `postgresql+asyncpg` (async, non-blocking).
- **Migration driver:** `postgresql+psycopg` (sync — Alembic runs synchronously).

---

## Architecture

```
Client
  │  POST /documents            POST /chat  (SSE stream)
  ▼
FastAPI ── auth (JWT) ── DI ── lifespan-loaded Chroma + OpenAI clients
  │                                   │
  ▼                                   ▼
Ingestion (background task)      RAG Service
  ├─ chunk text (overlap)            │  1. embed query
  ├─ embed chunks                    │  2. similarity search (Chroma)
  └─ upsert to Chroma                │  3. build grounded prompt
                                     │  4. stream LLM tokens → SSE
                                     ▼
                             Vector DB (ChromaDB)  +  LLM (OpenAI)
```

**Request lifecycle:** middleware (request-ID + timing) → dependency graph (auth, DB session, services) → route → response. Heavy clients (Chroma collection, async OpenAI client) are created **once** in the app `lifespan`, never per request.

---

## Project layout

```
app/
├── main.py                 # app factory, lifespan (chroma+llm+logging), middleware, handlers, routers
├── core/
│   ├── config.py           # pydantic-settings (env-driven, APP_ prefix)
│   ├── security.py         # bcrypt hashing + JWT access/refresh tokens
│   ├── logging.py          # JSON structured logging
│   └── errors.py           # DomainError hierarchy + uniform error envelope
├── api/
│   ├── deps.py             # DI: get_db, services, get_current_user, require_roles, get_rag_service
│   ├── auth.py             # /auth/login, /auth/refresh
│   ├── users.py            # /users CRUD + /users/me (RBAC-guarded delete)
│   ├── documents.py        # /documents  (ingest via background task)
│   ├── chat.py             # /chat  (SSE token streaming)
│   └── items.py            # dependency/guard demo router
├── models/                 # SQLAlchemy 2.0 typed ORM (base, user, document)
├── schemas/                # Pydantic v2 request/response contracts (user, document)
├── repositories/           # data access (user_repo, document_repo)
├── services/               # business logic (user_service, rag_service)
└── db/
    └── session.py          # async engine + get_db unit-of-work
alembic/                    # migrations (env.py reads the app URL, sync driver)
tests/                      # async tests with dependency overrides
Dockerfile · docker-compose.yml
```

---

## Endpoints

| Method | Path                | Auth       | Description                                   |
| ------ | ------------------- | ---------- | --------------------------------------------- |
| POST   | `/auth/login`       | –          | OAuth2 password login → access + refresh JWT  |
| POST   | `/auth/refresh`     | –          | Exchange a refresh token for a new access one |
| POST   | `/users`            | –          | Register a user (bcrypt-hashed password)      |
| GET    | `/users/me`         | Bearer     | Current authenticated user                    |
| GET    | `/users/{user_id}`  | –          | Fetch a user (404 via domain error)           |
| DELETE | `/users/{user_id}`  | Bearer+RBAC| Admin-only delete                             |
| POST   | `/documents`        | Bearer     | Persist a doc, embed + index in background    |
| POST   | `/chat?query=...`   | Bearer     | Streamed, context-grounded answer (SSE)       |
| GET    | `/health`           | –          | Liveness probe                                |

Interactive docs at `/docs` (Swagger) and `/redoc`.

---

## Key concepts implemented

**Dependency injection** — routes declare what they need (`Depends`); the container resolves a per-request graph: `route → service → repository → get_db session`. `dependency_overrides` makes auth/DB swappable in tests.

**Async unit-of-work** — `get_db` yields one `AsyncSession` per request that commits on success and rolls back on error. Repositories `flush()` (assign PKs); the commit boundary lives in `get_db`.

**Auth** — OAuth2 password flow, bcrypt hashing, short-lived **access** + long-lived **refresh** JWTs with a `type` claim so a refresh token can't be used as an access token. `require_roles("admin")` is a dependency factory for RBAC (401 = unauthenticated, 403 = forbidden). `slowapi` rate-limits the sensitive endpoints — `/auth/login` (5/min), `/auth/refresh` (10/min), and the expensive `/chat` (20/min) — returning `429` when exceeded.

**Cross-cutting** — request-ID + timing middleware (`X-Request-ID`, `X-Process-Time-ms`), a uniform `{"error": {...}}` envelope for domain and validation errors, and JSON structured logging wired in `lifespan`.

**RAG pipeline** (`services/rag_service.py`)
- `chunk()` — fixed-size windows with overlap to preserve context across cuts.
- `embed()` — async OpenAI embeddings (`text-embedding-3-small`).
- `ingest()` — chunk → embed → upsert vectors + metadata to Chroma.
- `retrieve()` — embed query → top-k similarity search.
- `answer_stream()` — build a grounded prompt (answer *only* from context) → stream `gpt-4o-mini` tokens.

**Streaming** — `/chat` returns a `StreamingResponse` of SSE frames (`data: {"token": "..."}\n\n` … `data: [DONE]\n\n`) so tokens render as they arrive. `X-Accel-Buffering: no` disables proxy buffering.

**Background ingestion** — `/documents` persists metadata, returns immediately, and embeds off the request path via `BackgroundTasks`. (For large corpora or guaranteed processing, swap in a Celery/RQ worker — the documented scaling boundary.)

---

## Getting started

### 1. Environment

Create `.env` (git-ignored):

```env
APP_DATABASE_URL=postgresql+asyncpg://app:app@localhost:5432/appdb
APP_SECRET_KEY=replace_with_a_64_char_random_secret
APP_OPENAI_API_KEY=sk-...        # required for real /chat and ingestion
```

### 2. Run with Docker (API + Postgres)

```bash
docker compose up --build
docker compose exec api alembic upgrade head   # apply migrations in-container
```

### 3. Run locally

```bash
uv sync                          # or: pip install -r requirements.txt
alembic upgrade head             # migrations (uses the sync psycopg driver)
fastapi dev app/main.py          # http://127.0.0.1:8000/docs
```

---

## Database migrations (Alembic)

`alembic/env.py` reads the app's `DATABASE_URL` and swaps the async driver for the sync one, so there is a single source of truth:

```python
config.set_main_option("sqlalchemy.url", DATABASE_URL.replace("+asyncpg", "+psycopg"))
```

```bash
alembic revision --autogenerate -m "message"   # draft a migration (always review it)
alembic upgrade head                            # apply
alembic downgrade -1                            # roll back one step
```

Requires the sync driver: `pip install "psycopg[binary]"`.

---

## Demo the RAG flow

```bash
# 1. register + log in to get a token
# 2. upload a document (indexed in the background)
curl -X POST localhost:8000/documents -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"title":"France","content":"The capital of France is Paris."}'

# 3. stream a grounded answer
curl -N -X POST "localhost:8000/chat?query=What%20is%20the%20capital%20of%20France%3F" \
     -H "Authorization: Bearer $TOKEN"
# data: {"token": "Paris"}
# data: {"token": " is"} ...
# data: [DONE]
```

---

## Testing

```bash
pytest
```

Async tests run the app in-process via `httpx.ASGITransport` (no live server) and use `dependency_overrides` to swap auth/DB — the payoff of the DI design.
