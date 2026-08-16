import json

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from app.api.deps import get_current_user, get_rag_service
from app.services.rag_service import RagService
from app.core.rate_limit import limiter
from app.models.user import User

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("")
@limiter.limit("20/minute")           # expensive LLM endpoint
async def chat(
    request: Request,
    query: str,
    user: User = Depends(get_current_user),          # auth-protected
    rag: RagService = Depends(get_rag_service),
):
    async def event_stream():
        async for token in rag.answer_stream(query):
            # SSE frame: "data: <json>\n\n"
            yield f"data: {json.dumps({'token': token})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
