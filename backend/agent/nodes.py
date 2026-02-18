from pathlib import Path
import json
import re
from backend.agent.state import State
from backend.knowledge.vector_store import VectorStore
from backend.agent.tools import Tools
from backend.knowledge.few_shot_examples import SQLExample
from backend.knowledge.data_dictionary import DataDictionary
from langchain_core.tools import StructuredTool
from langchain.agents import create_agent
# from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.types import interrupt
from langchain.chat_models import init_chat_model
from backend.config import load_chat_prompt_template
from backend.database.db_connect import DBConnector
from backend.agent import util

db_connector = DBConnector()
# intent_classifier_prompt = load_chat_prompt_template(target_prompt="intent_classifier")
sql_generator_prompt = load_chat_prompt_template(target_prompt="sql_generator")

# llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
sql_examples_path = Path("config/sql_examples.yml")

# Create data dictionary from DBConnector (automatically extracts schema)
data_dictionary = DataDictionary.load(Path("backend/config/db_dict.yml"))
sql_examples = SQLExample.from_yaml(sql_examples_path) if sql_examples_path.exists() else {}
# vector_store = VectorStore()

def chat_agent(state:State, vector_store:VectorStore):
    messages = state.messages
    last_user_message = messages[-1]
    # chat_history = messages[-1:]
    tools_obj = Tools(vector_store)
    tools = [
        StructuredTool.from_function(
            func=tools_obj.get_similar_queries,
            name="get_similar_queries",
            description="Get similar queries from the vector store"
        ),
        StructuredTool.from_function(
            func=tools_obj.explain_query,
            name="explain_query",
            description="Explain the query"
        ),
        StructuredTool.from_function(
            func=tools_obj.get_table_info,
            name="get_table_info",
            description="Get information about the table"
        )
    ]
    prompt = ChatPromptTemplate.from_messages([
        MessagesPlaceholder(variable_name="chat_history"),
        HumanMessage(content=last_user_message.content)
    ])
        # Get the system prompt
    chat_system_prompt = """You are a helpful NL2SQL assistant that can help users with database queries and data analysis.

You have access to tools that can:
1. Find similar SQL query examples from the knowledge base
2. Explain SQL queries in simple terms
3. Provide database schema information

For general questions about capabilities, explain what you can do.
For questions about the database or SQL, use the appropriate tools to provide helpful information.
Be conversational and helpful, and guide users toward useful database queries.

IMPORTANT: You have access to the full conversation history. Use it to understand 
context and follow-up questions. For example, if a user asks "what were his numbers the next year?"
after asking about Cody Bellingers 2020 season, you should understand they are asking about Cody Bellingers 2021 season.
"""  # noqa: E501

    # # Create the prompt
    # prompt = ChatPromptTemplate.from_messages(
    #     [
    #         ("system", chat_system_prompt),
    #         MessagesPlaceholder(variable_name="chat_history"),
    #         ("user", "{input}"),
    #         MessagesPlaceholder(variable_name="agent_scratchpad"),
    #     ]
    # )



    # llm = init_chat_model(model="gpt-4o-mini", temperature=0)

    agent = create_agent(
        model="gpt-4o-mini",
        # temperature=0,
        tools=tools,
        system_prompt=chat_system_prompt
    )
    # agent_executor = AgentExecutor(agent=agent, tools=tools)
    try:
        response = agent.invoke(
            {"input": state.user_query, "chat_history": state.messages}
        )
        # print("hello")
        response_content = response["messages"][-1].content
        # print("response", response)
    except Exception as e:
        # logger.error(f"Chat agent error: {e}")
        response_content = (
            "I'm here to help you with database queries and data analysis. "
            "What would you like to explore in your database?"
        )
        print("error", e)

    # logger.debug(f"✅ Chat Agent response: {response_content[:50]}...")
    # return {"messages": [AIMessage(content=response)]}
    return {"messages": [AIMessage(content=response_content)]}

def determine_relevance(state:State):
    pass



def sql_generator(state:State, vector_store:VectorStore):
    
    relevant_messages = [
        msg for msg in state.messages 
        if hasattr(msg, "type") and msg.type in ["human", "ai"]
    ]

    chat_history = util.get_chat_history(relevant_messages)

    # Use RAG to retrieve relevant schema parts based on the query
    # This is more efficient than sending the entire schema
    schema_docs = vector_store.vectorstore.similarity_search(
        state.user_query,
        k=15,  # Get top 15 most relevant tables/columns
        filter={"type": "schema"}
    )
    
    # If we found relevant schema docs, use them; otherwise fall back to full schema
    if schema_docs:
        schema_context = "\n\n".join([doc.page_content for doc in schema_docs])
        print(f"Retrieved {len(schema_docs)} relevant schema documents via RAG")
    else:
        # Fallback to full schema if RAG doesn't find anything
        schema_context = data_dictionary.format_context()
        print("WARNING: No relevant schema found via RAG, using full schema")
    
    print(f"Schema context length: {len(schema_context)} characters")
    print(f"User query: {state.user_query}")
    
    # Try to find SQL examples, but don't fail if none are found
    example_docs = vector_store.vectorstore.similarity_search(
        state.user_query, 
        k=10, 
        filter={"type": "example"}
    )
    sql_examples_context = "\n\n".join([doc.page_content for doc in example_docs])
    
    print(f"SQL examples found: {len(example_docs)}")
    if len(example_docs) == 0:
        print("WARNING: No SQL examples found in vector store. Proceeding without examples.")

    llm = init_chat_model(model="gpt-4o-mini", temperature=0)
    
    chain = sql_generator_prompt | llm

    result = chain.invoke({
        "user_query": state.user_query,
        "chat_history": chat_history,
        "schema_context": schema_context,
        "sql_examples": sql_examples_context,
    })
    # print(result)
    response_content = result.content if hasattr(result, 'content') else str(result)
    print(response_content)
    try:
        parsed = json.loads(response_content)
        print(parsed)
        sql_query = parsed.get("sql_query", "").strip()
        
        if sql_query:  
            return {
                "sql_query": sql_query,
                "sql_generation_status": "success"
            }
        else: 
            explanation = parsed.get("sql_explanation", "No SQL query could be generated.")
            return {
                "sql_query": None,
                "sql_generation_status": "failure",
                "messages": [AIMessage(content=f"I couldn't generate a SQL query for your question. {explanation}")]
            }
    except (json.JSONDecodeError, AttributeError, KeyError) as e:
        print(f"Error parsing SQL generator response: {e}")
        explanation = f"Error parsing JSON: {str(e)}"
        return {
            "sql_query": None,
            "sql_generation_status": "failure",
            "messages": [AIMessage(content=f"I couldn't generate a SQL query for your question. {explanation}")]
        }
    
def sql_executor(state:State, db_connector: DBConnector):
    if not state.sql_query:
        return {
            "sql_execution_status": "failure",
            "sql_execution_result": {
                "status": "failure",
                "error": "No SQL query generated or query is empty"
            }
        }
    
    res = util.execute_sql(state.sql_query, db_connector)
    print(res)
    return {
        "sql_execution_status": res["status"],
        "sql_execution_result": res
    }

def check_sql_execution(state: State) -> str:
    if state.sql_execution_status == "success":
        return "success"
    else:
        return "failure"

def check_sql_generation(state: State) -> str:
    if state.sql_generation_status == "success":
        return "success"
    else:
        return "failure"

def sql_return_message(state:State, vector_store:VectorStore):
    print(state.sql_execution_result)
    vector_store.add_generated_query(state.user_query, state.sql_query)
    if not state.sql_execution_result:
        return {
            "messages": [AIMessage(content="No execution result available.")]
        }
    
    if state.sql_execution_status == "success":
        data = state.sql_execution_result.get("data")
        if data:
            # Format the data nicely
            if isinstance(data, list) and len(data) > 0:
                # Format as a readable string
                formatted_rows = []
                for row in data:
                    formatted_row = ", ".join([f"{k}: {v}" for k, v in row.items()])
                    formatted_rows.append(formatted_row)
                content = "\n".join(formatted_rows)
            else:
                content = str(data)
        else:
            content = state.sql_execution_result.get("message", "Query executed successfully.")
    else:
        # Handle error case
        error = state.sql_execution_result.get("error", "Unknown error occurred")
        content = f"Error executing query: {error}"
    
    return {
        "messages": [AIMessage(content=content)]
    }
    
    
def sql_analyzer(state:State, db_connector: DBConnector, sql_query: str):
    execution_result = state["sql_execution_result"]
    
    formatted_results = util.format_sql_execution_result(execution_result)

    pass
    return {
        "sql_analysis_status": res["status"],
        "sql_analysis_result": res
    }