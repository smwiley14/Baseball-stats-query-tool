import logging

from fastapi import FastAPI, APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database.db_connect import DBConnector
from knowledge.vector_store import VectorStore
from agent.agent import create_graph
from agent.cancellation import QueryCancelledError, request_cancel, reset_cancel
from langgraph.checkpoint.memory import MemorySaver
from api.auth import require_api_key
from api.chat_types import CancelRequest, CancelResponse, ChatRequest, ChatResponse
import uuid
from langchain_core.messages import AIMessage, HumanMessage
from agent.state import State
from langgraph.types import Command

logger = logging.getLogger(__name__)
chat_router = APIRouter(dependencies=[Depends(require_api_key)])

db_connector = None
vector_store = None
agent_graph = None
memory = None


def init_components() -> None:
    global db_connector, vector_store, agent_graph, memory
    if agent_graph is not None:
        return  # Already initialized
    try:
        db_connector = DBConnector()
        vector_store = VectorStore(db_connector)
        graph = create_graph(db_connector, vector_store)
        memory = MemorySaver()
        agent_graph = graph.compile(checkpointer=memory)  # Compile the graph
    except Exception as e:
        logger.exception("Failed to initialize application components")
        raise HTTPException(
            status_code=500,
            detail="Internal server error during initialization. Check server logs.",
        )

@chat_router.post("")
async def send_message(request: ChatRequest) -> ChatResponse:
    session_id = request.session_id or str(uuid.uuid4())
    try : 
        init_components()
        reset_cancel(session_id)

        user_message = HumanMessage(content=request.message)
        messages = [user_message]

        if request.history:
            messages.extend(request.history)

        graph_config = {
            "configurable": {
                "thread_id": session_id
            }
        }
        
        # Create initial state
        initial_state = {
            "session_id": session_id,
            "messages": [user_message],
            "user_query": request.message
        }
        
        # Invoke the graph
        result = agent_graph.invoke(initial_state, config=graph_config)
        if "__interrupt__" in result:
            interrupt_data = result["__interrupt__"][0].value
            interrupt_message = interrupt_data.get("messages")
            if hasattr(interrupt_message, "content"):
                last_message = interrupt_message.content
            elif isinstance(interrupt_message, str):
                last_message = interrupt_message
            else:
                last_message = (
                    "Waiting for your confirmation. Please respond with 'yes' or 'no'."
                )
        else:
            # Extract the last AI message from the result
            last_message = None
            if result.get("messages"):
                # Get the last message that isn't the user's input
                for msg in reversed(result["messages"]):
                    if hasattr(msg, "type") and msg.type != "human":
                        last_message = msg.content
                        break

            if last_message is None:
                last_message = (
                    "I processed your message but couldn't generate a response."
                )

        # Extract table data and summary from result
        table_data = result.get("table_data")
        supplemental_data = result.get("supplemental_data")
        summary = result.get("summary", last_message)

        return ChatResponse(
            message=summary,
            session_id=session_id,
            table_data=table_data,
            supplemental_data=supplemental_data,
            summary=summary,
            metadata={
                "user_intent": result.get("user_intent"),
                "query_type": result.get("query_type"),
                "selected_stat_profile": result.get("selected_stat_profile"),
                "sql_query": result.get("sql_query"),
                "sql_safety_status": result.get("sql_safety_status"),
                "sql_syntax_status": result.get("sql_syntax_status"),
                "sql_execution_status": result.get("sql_execution_status"),
            },
        )
    except QueryCancelledError:
        return ChatResponse(
            message="Query cancelled.",
            session_id=session_id,
            table_data=None,
            supplemental_data=None,
            summary="Query cancelled.",
            metadata={
                "cancelled": True,
            },
        )
    except Exception as e:
        logger.exception("Unhandled error processing chat request for session %s", session_id)
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred. Please try again later.",
        )
    finally:
        reset_cancel(session_id)


@chat_router.post("/cancel")
async def cancel_query(request: CancelRequest) -> CancelResponse:
    request_cancel(request.session_id)
    return CancelResponse(status="cancel_requested", session_id=request.session_id)
