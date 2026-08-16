from app.repositories.user_repo import UserRepository
from app.repositories.document_repo import DocumentRepository
from app.models.user import User
from app.models.document import Document
from app.schemas.user import UserCreate
from app.schemas.document import DocumentCreate
from app.core.errors import NotFoundError, DomainError
from app.core.security import hash_password       # Day 5

class UserService:
    def __init__(self, repo: UserRepository):
        self.repo = repo

    async def register(self, data: UserCreate) -> User:
        if await self.repo.get_by_email(data.email):
            raise DomainError("email already registered", "email_taken", 409)
        user = User(
            name=data.name,
            email=data.email,
            hashed_password=hash_password(data.password),
        )
        return await self.repo.add(user)

    async def get_or_404(self, user_id: int) -> User:
        user = await self.repo.get(user_id)
        if not user:
            raise NotFoundError("user", user_id)
        return user

    async def create_document(self, owner_id: int, data: DocumentCreate) -> Document:
        # persist document metadata; embedding/ingestion happens off the request path
        doc = Document(title=data.title, content=data.content, owner_id=owner_id)
        # reuse the request-scoped session held by the user repository
        return await DocumentRepository(self.repo.session).add(doc)
