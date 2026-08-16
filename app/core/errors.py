from fastapi import Request, status
from fastapi.responses import JSONResponse

class DomainError(Exception):
    """Base for business-rule violations."""
    def __init__(self, message: str, code: str, http_status: int = 400):
        self.message = message
        self.code = code
        self.http_status = http_status

class NotFoundError(DomainError):
    def __init__(self, entity: str, id_):
        super().__init__(f"{entity} {id_} not found", "not_found", status.HTTP_404_NOT_FOUND)


# handler produces a uniform JSON envelope for ALL domain errors
async def domain_error_handler(request: Request, exc: DomainError):
    return JSONResponse(
        status_code=exc.http_status,
        content={ "error": {"code": exc.code, "message": exc.message} }
    )
