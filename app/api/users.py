from fastapi import APIRouter, Depends, status
from app.api.deps import get_user_service, get_current_user, require_roles
from app.schemas.user import UserCreate, UserOut
from app.services.user_service import UserService
from app.models.user import User

router = APIRouter(prefix="/users", tags=["users"])


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
