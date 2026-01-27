import os

from dotenv import load_dotenv

load_dotenv()

openai_api_key = os.getenv("OPENAI_API_KEY")
langchain_api_key = os.getenv("LANGCHAIN_API_KEY")

from langchain_openai import ChatOpenAI
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain.agents import create_agent

from langchain_community.utilities.sql_database import SQLDatabase

# Database connection
# db = SQLDatabase.from_uri("postgresql://baseball:baseball@localhost:5433/retrosheet")

# LLM
# llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

# Toolkit & tools
# toolkit = SQLDatabaseToolkit(db=db, llm=llm)
# tools = toolkit.get_tools()
class PGDatabaseConfig:
    def __init__(self, db_url: str):
# Agent system prompt
        self.db_url = db_url
        self.db = SQLDatabase.from_uri(db_url)
        self.llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
        self.toolkit = SQLDatabaseToolkit(db=self.db, llm=self.llm)
        self.tools = self.toolkit.get_tools()
    def create_agent(self):
        agent = create_agent(self.llm, self.tools, system_prompt=self.system_prompt)
        return agent

    def get_system_prompt(self):
        return """
        You are an agent designed to interact with a SQL database.
        Given an input question, create a syntactically correct {dialect} query to run,
        then look at the results of the query and return the answer.
        Limit queries to {top_k} results and never perform DML operations.
        """.format(dialect=self.db.dialect, top_k=5)

    def prompt_agent(self, question: str):
        agent = self.create_agent()
        result = agent.invoke({"messages": [{"role": "user", "content": question}]})
        return result

    # # Create agent (tracing V2 happens automatically)
    # agent = create_agent(llm, tools, system_prompt=system_prompt)

    # # Test query
    # question = "Show me the top 10 Home run leaders for the 2020 season?"
    # result = agent.invoke({"messages": [{"role": "user", "content": question}]})
    # # print(result["output"])
    # print(result)
