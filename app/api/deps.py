from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.repositories.user_repo import UserRepository
from app.services.user_service import UserService
from app.services.rag_service import RagService
from app.models.user import User
from app.core.security import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def get_user_service(db: AsyncSession = Depends(get_db))-> UserService:
    return UserService(UserRepository(db))


def get_rag_service(request: Request) -> RagService:
    # pull the singletons loaded once in the app lifespan (Day 3 concept)
    return RagService(request.app.state.collection, request.app.state.llm)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    svc: UserService = Depends(get_user_service),
) -> User:
    creds_error = HTTPException(
        status.HTTP_401_UNAUTHORIZED, "could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
    except ValueError:
        raise creds_error
    if payload.get("type") != "access":
        raise creds_error
    user = await svc.repo.get(int(payload["sub"]))
    if user is None:
        raise creds_error
    return user

def require_roles(*allowed: str):
    async def _guard(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "insufficient permissions")
        return user
    return _guard