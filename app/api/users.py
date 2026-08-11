from fastapi import APIRouter, HTTPException, status
from app.schemas.user import UserCreate, UserOut

router = APIRouter(prefix="/users", tags=["users"])

_db: dict[int, dict] = {}
_seq = 0


# app/api/users.py
from fastapi import APIRouter, HTTPException, status
from app.schemas.user import UserCreate, UserOut

router = APIRouter(prefix="/users", tags=["users"])

_db: dict[int, dict] = {}
_seq = 0

@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate):
    global _seq
    _seq += 1
    _db[_seq] = {
        "id": _seq, **payload.model_dump(exclude={"password"}),
        "created_at": __import__("datetime").datetime.utcnow()
    }
    return _db[_seq]

@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: int):
    if user_id not in _db:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "user not found")
    return _db[user_id]