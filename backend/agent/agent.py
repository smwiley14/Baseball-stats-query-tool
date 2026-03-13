from backend.agent.state import State


from functools import partial
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages, BaseMessage
from langchain_openai import ChatOpenAI
from database.db_connect import DBConnector
from knowledge.vector_store import VectorStore
from pydantic import BaseModel
from typing import Annotated, Literal, Any
from agent import nodes
from agent.state import State
StateGraphMessage = Annotated[BaseMessage, add_messages]


def create_graph(
    db_connector: DBConnector,
    vector_store: VectorStore
) -> StateGraph:
    """
    Create and configure the LangGraph agent workflow.
    Search-engine style: 
    
    query -> 
    relevance check -> 
    SQL generation -> 
    execution -> 
    formatted results
    
    Args:
        db_connector: Database connector instance
        vector_store: Vector store instance for RAG
        
    Returns:
        Compiled StateGraph ready for execution
    """
    # create graph with State schema
    graph = StateGraph[State, None, State, State](State)
    
    # bind dependencies to node functions
    normalize_input_node = nodes.normalize_input
    relevance_check_node = partial(nodes.check_relevance, vector_store=vector_store)
    classify_query_type_node = nodes.classify_query_type
    classify_stat_profile_node = nodes.classify_stat_profile
    sql_generator_node = partial(nodes.sql_generator, vector_store=vector_store)
    sql_executor_node = partial(nodes.sql_executor, db_connector=db_connector)
    sql_return_message_node = partial(nodes.sql_return_message, vector_store=vector_store)
    
    # Add nodes
    graph.add_node("normalize_input", normalize_input_node)
    graph.add_node("relevance_check", relevance_check_node)
    graph.add_node("classify_query_type", classify_query_type_node)
    graph.add_node("classify_stat_profile", classify_stat_profile_node)
    graph.add_node("sql_generator", sql_generator_node)
    graph.add_node("sql_executor", sql_executor_node)
    graph.add_node("sql_return_message", sql_return_message_node)
    
    graph.add_edge(START, "normalize_input")
    graph.add_edge("normalize_input", "relevance_check")
    
    graph.add_conditional_edges(
        "relevance_check",
        nodes.check_relevance_decision,
        {
            True: "classify_query_type",
            False: END,
        },
    )

    graph.add_edge("classify_query_type", "classify_stat_profile")
    graph.add_edge("classify_stat_profile", "sql_generator")
    
    graph.add_conditional_edges(
        "sql_generator",
        nodes.check_sql_generation,
        {
            "success": "sql_executor",
            "failure": END,
        },
    )

    graph.add_conditional_edges(
        "sql_executor",
        nodes.check_sql_execution,
        {
            "success": "sql_return_message",
            "failure": END,
        }
    )
    
    graph.add_edge("sql_return_message", END)
    return graph
