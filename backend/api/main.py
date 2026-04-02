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

# Restrict CORS to explicitly allowed origins.
# Set ALLOWED_ORIGINS as a comma-separated list in your environment, e.g.:
#   ALLOWED_ORIGINS=https://app.example.com,https://www.example.com
_origins_env = os.getenv("ALLOWED_ORIGINS", "")
if _origins_env:
    allowed_origins = [o.strip() for o in _origins_env.split(",") if o.strip()]
else:
    # Fall back to localhost only — safe default for local development.
    allowed_origins = ["http://localhost:3000", "http://localhost:5173"]
    logger.warning(
        "ALLOWED_ORIGINS env var not set; CORS restricted to localhost only. "
        "Set ALLOWED_ORIGINS for production."
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


app.include_router(chat_router, prefix="/chat")


@app.on_event("startup")
def init_kb_on_startup() -> None:
    """Initialize vector store documents when backend starts."""
    init_knowledge_base()

# def get_app():
#     return app

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
