from fastapi import APIRouter, Depends, HTTPException, FastAPI
from sqlalchemy import desc, distinct, func
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
import uvicorn


router = APIRouter()

app = FastAPI(
    title="Baseball NL2SQL",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)




def get_app():
    return app

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)