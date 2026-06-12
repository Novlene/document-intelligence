import secrets
from fastapi import HTTPException, Security
from fastapi.security.api_key import APIKeyHeader
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.core.config import settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
limiter = Limiter(key_func=get_remote_address)


async def verify_api_key(api_key: str = Security(api_key_header)):
    if not api_key or not secrets.compare_digest(api_key, settings.api_key):
        raise HTTPException(status_code=403, detail="Invalid or missing API key")
    return api_key