"""LangGraph Server entrypoint for Studio/debugging."""

from database.db_connect import DBConnector
from knowledge.vector_store import VectorStore
from knowledge.init.init_vector_store import init_knowledge_base
from agent.agent import create_graph


# Ensure vector store is seeded before serving graph requests.
init_knowledge_base()

_db_connector = DBConnector()
_vector_store = VectorStore(_db_connector)

# Export compiled graph for LangGraph Server.
graph = create_graph(_db_connector, _vector_store).compile()
