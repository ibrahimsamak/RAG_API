import uuid, time

from fastapi import FastAPI, Query, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from enum import Enum
from pydantic import BaseModel
from datetime import datetime, timezone

from app.schemas.user import UserCreate, UserOut
from app.api import users
from app.api import items

app = FastAPI(title="AI API")
@app.middleware("http")
async def add_proccess_time_and_request_id(req: Request, call_next):
    request_id = str(uuid.uuid4())
    start = time.perf_counter()
    response = await call_next(req)
    elapsed_ms = (time.perf_counter() - start) * 1000
    # app/main.py
import time, uuid
from fastapi import FastAPI, Request

app = FastAPI()

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

app.include_router(users.router)
app.include_router(items.router)


@app.get("/health")
def health():
    return {"status": "OK"}



#### Old implementation ####

# _fake_db: dict[int, dict] = {}
# _seq = 0
# class SortOrder(str, Enum):
#     asc='asc'
#     desc='desc'


# class ItemUpdate(BaseModel):
#     name: str
#     price: float


# @app.get("/users/{user_id}")
# def get_user(user_id):
#     return {"id": user_id}


# @app.get("/users")
# def list_user(page:int = Query(1, ge=1), 
#               limit:int = Query(10, ge=1, le=1000), 
#               q:str | None = Query(None, min_length=2), 
#               order:SortOrder = SortOrder.desc):

#     return {
#         "page": page,
#         "limit": limit, 
#         "q": q,
#         "order": order
#     }


# @app.post("/users", response_model=UserOut, response_model_exclude={"email"}, status_code=status.HTTP_201_CREATED)
# def create_user(payload: UserCreate):
#     global _seq
#     _seq += 1
#     row = {
#         "id": _seq,
#         "name": payload.name,
#         "email": payload.email,
#         "created_at": datetime.now(timezone.utc),
#         # password intentionally not stored here — hashing comes on Day 5
#     }
#     _fake_db[_seq] = row
#     return row