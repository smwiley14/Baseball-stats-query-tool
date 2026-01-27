import hashlib

from langchain.embeddings.base import Embeddings
from langchain.schema import Document
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_postgres import PGVector, PGVectorStore, PGEngine
from ..db.db_connect import get_db

db = get_db()
engine = PGEngine(db)
store = PGVectorStore(engine, table_name="vector_store", vector_size=1536)



