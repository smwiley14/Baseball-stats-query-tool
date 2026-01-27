import os

from dotenv import load_dotenv

load_dotenv(override=True)
os.environ.pop("LANGCHAIN_TRACING", None)
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = "My-Project"

openai_api_key = os.getenv("OPENAI_API_KEY")
langchain_api_key = os.getenv("LANGCHAIN_API_KEY")

from langchain_openai import ChatOpenAI
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain.agents import create_agent

from langchain_community.utilities.sql_database import SQLDatabase

# Database connection
db = SQLDatabase.from_uri("postgresql://baseball:baseball@localhost:5433/retrosheet")

# LLM
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

# Toolkit & tools
toolkit = SQLDatabaseToolkit(db=db, llm=llm)
tools = toolkit.get_tools()

# Agent system prompt
system_prompt = """
You are an agent designed to interact with a SQL database.
Given an input question, create a syntactically correct {dialect} query to run,
then look at the results of the query and return the answer.
Limit queries to {top_k} results and never perform DML operations.
""".format(dialect=db.dialect, top_k=5)

# Create agent (tracing V2 happens automatically)
agent = create_agent(llm, tools, system_prompt=system_prompt)

# Test query
question = "How many players are in the database?"
result = agent.invoke({"messages": [{"role": "user", "content": question}]})
# print(result["output"])
print(result)
