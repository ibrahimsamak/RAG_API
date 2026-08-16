from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.document import Document


class DocumentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, doc_id: int) -> Document | None:
        return await self.session.get(Document, doc_id)

    async def list_for_owner(self, owner_id: int, offset: int = 0, limit: int = 10) -> list[Document]:
        result = await self.session.execute(
            select(Document).where(Document.owner_id == owner_id).offset(offset).limit(limit)
        )
        return list(result.scalars().all())

    async def add(self, doc: Document) -> Document:
        self.session.add(doc)
        await self.session.flush()          # assigns PK without committing
        return doc
