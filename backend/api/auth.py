"""API key authentication dependency.

Usage
-----
Set the ``API_KEY`` environment variable to a strong random secret, then
include the dependency on any route that should be protected:

    from api.auth import require_api_key

    @router.post("/", dependencies=[Depends(require_api_key)])
    async def my_endpoint(...):
        ...

Clients must send the key in the ``X-API-Key`` request header.

If ``API_KEY`` is not set the application will start but log a prominent
warning and **reject all requests** so that a misconfigured production
deployment fails loudly rather than silently accepting unauthenticated
traffic.
"""

import logging
import os
import secrets

from fastapi import Header, HTTPException, Security, status
from fastapi.security.api_key import APIKeyHeader

logger = logging.getLogger(__name__)

_API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

# Read once at import time so the warning fires on startup.
_EXPECTED_KEY: str | None = os.getenv("API_KEY")
if not _EXPECTED_KEY:
    logger.warning(
        "API_KEY environment variable is not set. "
        "All requests to protected endpoints will be rejected. "
        "Set API_KEY to a strong random secret before deploying."
    )


async def require_api_key(api_key: str | None = Security(_API_KEY_HEADER)) -> None:
    """FastAPI dependency that validates the X-API-Key header.

    Raises HTTP 401 if the key is missing or incorrect.
    Raises HTTP 503 if the server is misconfigured (API_KEY env var not set).
    """
    if not _EXPECTED_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service is not properly configured (missing API_KEY).",
        )

    if not api_key or not secrets.compare_digest(api_key, _EXPECTED_KEY):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key.",
            headers={"WWW-Authenticate": "ApiKey"},
        )
