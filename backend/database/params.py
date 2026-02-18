import os
from abc import ABC, abstractmethod
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from sqlalchemy import Engine, inspect

load_dotenv()

class DBParams(BaseModel):
    host: str
    port: int
    user: str
    password: str
    database: str


