from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, distinct, func
from sqlalchemy.orm import Session

from ..db.db_connect import get_db

router = APIRouter()

def init_routes(app: FastAPI = Depends(get_app)):
    app.include_router(router)

# @router.post("/")
# async def send_message(message: str):
#     # try : 
#     #     init