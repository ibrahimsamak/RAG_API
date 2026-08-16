from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from app.api.deps import get_user_service
from app.services.user_service import UserService
from app.core.security import (
    verify_password, create_access_token, create_refresh_token, decode_token,
)
router = APIRouter(prefix="/auth", tags=["auth"])
@router.post("/login")
async def login(
    form: OAuth2PasswordRequestForm = Depends(),
    svc: UserService = Depends(get_user_service),
):
    user = await svc.repo.get_by_email(form.username)   # OAuth2 form uses "username"
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid credentials")
    return {
        "access_token": create_access_token(str(user.id), user.role),
        "refresh_token": create_refresh_token(str(user.id)),
        "token_type": "bearer",
    }

@router.post("/refresh")
async def refresh(refresh_token: str):
    try:
        payload = decode_token(refresh_token)
    except ValueError:
        raise HTTPException(401, "invalid token")
    if payload.get("type") != "refresh":
        raise HTTPException(401, "wrong token type")
    return {
        "access_token": create_access_token(payload["sub"], payload.get("role", "user")),
        "token_type": "bearer",
    }