from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate

from knowledge.vector_store import VectorStore

class Tools:
    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store
        try:
            self.model = init_chat_model(model="gpt-4o-mini", temperature=0)
            self.schema_context = None

        except Exception as e:
            print(f"Error initializing chat model: {e}")
            raise e

    def get_similar_queries(self, query:str, k:int):
        """get K similar queries from the vector store"""
        try:
            limit = min(k, 10)
            retriever = self.vector_store.store.as_retriever(
                search_kwargs={"k": limit,
                "filter": {"type": "example"}}
                )
            docs = retriever.invoke(query)
            if not docs:
                "No similar queries found"
                return None
            return [doc.page_content for doc in docs]

        except Exception as e:
            print(f"Error getting similar queries: {e}")
            raise e

    def explain_query(self, query:str):
        """explain the query"""
        pass

    def get_table_info(self, table_name:str):
        """get information about the table"""
        try:
            if not table_name:
                return f"Overview of database schema: {self.sch}"
            
            return f"Overview of table {table_name}: {self.data[table_name]}"
        except Exception as e:
            print(f"Error getting table info: {e}")
            raise e
