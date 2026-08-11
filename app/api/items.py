from fastapi import APIRouter, Depends
from app.api.deps import get_api_version, get_pagination, require_api_key, check_header


router = APIRouter(prefix="/items", tags=["items"], dependencies=[Depends(check_header), Depends(require_api_key)])

@router.get("")
def list_items(version: str = Depends(get_api_version), page: dict = Depends(get_pagination)):
    return {"version": version, **page}


class QueryFilters:
    def __init__(self, q: str | None = None, limit: int = 10):
        self.q = q
        self.limit = min(limit, 100)

@router.get("/search")
def search(filters: QueryFilters = Depends()):
    return {"q": filters.q, "limit": filters.limit}

