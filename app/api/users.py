# from fastapi import APIRouter, HTTPException, status
# from app.schemas.user import UserCreate, UserOut

# router = APIRouter(prefix="/users", tags=["users"])

# _db: dict[int, dict] = {}
# _seq = 0


from fastapi import APIRouter, HTTPException, status, Depends
from app.api.deps import get_user_service, get_current_user, require_roles
from app.schemas.user import UserCreate, UserOut
from app.services.user_service import UserService
from app.models.user import User

router = APIRouter(prefix="/users", tags=["users"])

# _db: dict[int, dict] = {}
# _seq = 0

# @router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
# def create_user(payload: UserCreate):
#     global _seq
#     _seq += 1
#     _db[_seq] = {
#         "id": _seq, **payload.model_dump(exclude={"password"}),
#         "created_at": __import__("datetime").datetime.utcnow()
#     }
#     return _db[_seq]

# @router.get("/{user_id}", response_model=UserOut)
# def get_user(user_id: int):
#     if user_id not in _db:
#         raise HTTPException(status.HTTP_404_NOT_FOUND, "user not found")
#     return _db[user_id]




@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate, svc: UserService = Depends(get_user_service)):
    return await svc.register(payload)


# /me must be declared before /{user_id}, otherwise "me" is parsed as user_id
@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)):
    return user


@router.get("/{user_id}", response_model=UserOut)
async def get_user(user_id: int, svc: UserService = Depends(get_user_service)):
    return await svc.get_or_404(user_id)


@router.delete("/{user_id}", status_code=204)
async def delete_user(user_id: int, _: User = Depends(require_roles("admin"))):
    return {"admin": "admin"}