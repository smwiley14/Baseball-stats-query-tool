from db_connect import get_db
from langchain_openai import ChatOpenAI
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain.agents import create_agent
import os
import dotenv

dotenv.load_dotenv()

openai_api_key = os.getenv("OPENAI_API_KEY")
langchain_api_key = os.getenv("LANGCHAIN_API_KEY")
langchain_project = os.getenv("LANGCHAIN_PROJECT")
langchain_tracing_v2 = os.getenv("LANGCHAIN_TRACING_V2")
langsmith_endpoint = os.getenv("LANGSMITH_ENDPOINT")

def create_agent():
    db = get_db()
    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0, api_key=openai_api_key)
    toolkit = SQLDatabaseToolkit(db=db, llm=llm)
    tools = toolkit.get_tools()
    agent = create_agent(llm, tools)
    return agent