from functools import partial
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages, BaseMessage
from langchain_openai import ChatOpenAI
from backend.database.db_connect import DBConnector
from backend.knowledge.vector_store import VectorStore
from pydantic import BaseModel
from typing import Annotated, Literal, Any
from backend.agent import nodes
from backend.agent.state import State
StateGraphMessage = Annotated[BaseMessage, add_messages]


def create_graph(
    db_connector: DBConnector,
    vector_store: VectorStore
) -> StateGraph:
    """
    Create and configure the LangGraph agent workflow.
    
    Args:
        db_connector: Database connector instance
        vector_store: Vector store instance for RAG
        
    Returns:
        Compiled StateGraph ready for execution
    """
    # Create graph with State schema
    graph = StateGraph(State)
    
    # Bind dependencies to node functions
    chat_agent_node = partial(nodes.chat_agent, vector_store=vector_store)
    sql_generator_node = partial(nodes.sql_generator, vector_store=vector_store)
    sql_executor_node = partial(nodes.sql_executor, db_connector=db_connector)
    sql_return_message_node = partial(nodes.sql_return_message, vector_store=vector_store)
    # sql_execution_status_node = partial(nodes.check_sql_execution)
    # Add nodes
    graph.add_node("chat_agent", chat_agent_node)
    graph.add_node("sql_generator", sql_generator_node)
    graph.add_node("sql_executor", sql_executor_node)
    graph.add_node("sql_return_message", sql_return_message_node)
    # graph.add_node("sql_execution_status", sql_execution_status_node)
    # Define flow
    graph.add_edge(START, "chat_agent")
    graph.add_edge("chat_agent", "sql_generator")
    
    # Conditional edge after SQL generation
    graph.add_conditional_edges(
        "sql_generator",
        nodes.check_sql_generation,
        {
            "success": "sql_executor",
            "failure": END,
        },
    )
    # graph.add_edge("sql_executor", "sql_execution_status")

    graph.add_conditional_edges(
        "sql_executor",
        nodes.check_sql_execution,
        {
            "success": "sql_return_message",
            "failure": END,
        }
    )
    # print("sql_generator", "sql_executor")
    # graph.add_edge("sql_generator", "sql_executor")
    # graph.add_edge("sql_return_message", "chat_agent")
    # graph.add_edge("chat_agent", END)
    graph.add_edge("sql_return_message", END)
    return graph