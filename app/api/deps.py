from fastapi import Depends, Header, HTTPException, status, Request

# --- a trivial dependency: extract & validate a header ---
def get_api_version(x_api_version: str = Header(default="v1"))-> str:
    print(x_api_version)
    if x_api_version not in {"v1", "v2"}:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "unsupported API version")
    return x_api_version

# --- dependencies can depend on other dependencies (a graph) ---
def get_pagination(page:int = 1, limit:int = 10)->dict:
    return {"offset": (page-1) * limit, "limit": limit}


def require_api_key(x_api_key: str = Header(...)):
    if x_api_key != "secret":
        raise HTTPException(401, "bad api key")

def check_header(request:Request):
     if  "x-api-key" not in request.headers:
        raise HTTPException(401, "no api key")
