import time
import uuid
import logging
from contextlib import asynccontextmanager

import chromadb
from openai import AsyncOpenAI
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.core.errors import DomainError, domain_error_handler
from app.core.rate_limit import limiter
from app.api import auth, users, documents, chat

log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ---- startup: load heavy clients ONCE ----
    configure_logging()
    settings = get_settings()

    # vector store — persistent client + collection loaded once
    app.state.chroma = chromadb.PersistentClient(path="./chroma_store")
    app.state.collection = app.state.chroma.get_or_create_collection("documents")

    # async LLM client (shares one httpx connection pool). A placeholder key keeps
    # the app bootable without credentials; real calls fail with a 401 until a key
    # is set in APP_OPENAI_API_KEY.
    app.state.llm = AsyncOpenAI(api_key=settings.openai_api_key or "sk-placeholder-not-set")
    if not settings.openai_api_key:
        log.warning("APP_OPENAI_API_KEY is not set — /chat and ingestion will fail until it is.")

    log.info("startup complete")
    yield
    # ---- shutdown ----
    await app.state.llm.close()
    log.info("shutdown complete")


app = FastAPI(lifespan=lifespan, title="AI RAG API", version="1.0.0")

# rate limiting — the limiter instance lives in app.state so the route decorators
# and the exception handler can find it.
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# uniform error envelope for all domain errors
app.add_exception_handler(DomainError, domain_error_handler)


@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"error": {"code": "validation_error", "details": exc.errors()}},
    )


@app.middleware("http")
async def add_process_time_and_request_id(request: Request, call_next):
    request_id = str(uuid.uuid4())
    start = time.perf_counter()

    response = await call_next(request)      # <- the rest of the pipeline + route

    elapsed_ms = (time.perf_counter() - start) * 1000
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time-ms"] = f"{elapsed_ms:.2f}"
    return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(documents.router)
app.include_router(chat.router)


@app.get("/health", tags=["ops"])
def health():
    return {"status": "ok"}
