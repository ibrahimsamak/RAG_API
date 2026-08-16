from fastapi import APIRouter, BackgroundTasks, Depends, status

from app.api.deps import get_current_user, get_rag_service, get_user_service
from app.services.rag_service import RagService
from app.services.user_service import UserService
from app.schemas.document import DocumentCreate, DocumentOut
from app.models.user import User

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
async def upload_document(
    payload: DocumentCreate,
    background: BackgroundTasks,
    rag: RagService = Depends(get_rag_service),
    svc: UserService = Depends(get_user_service),
    user: User = Depends(get_current_user),
):
    doc = await svc.create_document(user.id, payload)      # persist metadata (Day 4)
    # embedding is slow -> do it AFTER the response (Day 3 background task).
    # For large corpora or guaranteed processing, swap for a Celery/RQ worker.
    background.add_task(rag.ingest, doc.id, doc.title, doc.content)
    return doc
