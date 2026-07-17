import logging
import os

from fastapi import APIRouter, Depends, HTTPException, FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from api.routes.main import chat_router
from knowledge.init.init_vector_store import init_knowledge_base

logger = logging.getLogger(__name__)
router = APIRouter()

app = FastAPI(
    title="Baseball NL2SQL",
    redirect_slashes=False,  # Prevent 307 redirects on trailing-slash mismatches
)

# Allowed CORS origins come entirely from the ALLOWED_ORIGINS env var
# (comma-separated) — nothing is hardcoded. Example:
#   ALLOWED_ORIGINS=https://app.example.com,https://www.example.com,http://localhost:3000
# If unset, no cross-origin browser requests are allowed. (The app is normally
# served same-origin behind the frontend proxy, where CORS isn't triggered, so
# this only matters for direct cross-origin API callers.)
allowed_origins = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", "").split(",")
    if origin.strip()
]
if not allowed_origins:
    logger.warning(
        "ALLOWED_ORIGINS is not set; no cross-origin browser requests will be "
        "allowed. Set ALLOWED_ORIGINS (comma-separated) to permit specific origins."
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


app.include_router(chat_router, prefix="/chat")


@app.get("/health")
def health() -> dict:
    """Liveness/readiness probe for Docker healthchecks and load balancers."""
    return {"status": "ok"}


@app.on_event("startup")
def init_kb_on_startup() -> None:
    """Initialize vector store documents when backend starts."""
    init_knowledge_base()

# def get_app():
#     return app

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
