from fastapi import FastAPI, APIRouter, Depends, HTTPException
from sqlalchemy import desc, distinct, func
from sqlalchemy.orm import Session

from backend.database.db_connect import DBConnector
from backend.knowledge.vector_store import VectorStore
from backend.agent.agent import create_graph
from langgraph.checkpoint.memory import MemorySaver
from backend.api.chat_types import ChatRequest, ChatResponse
import uuid
from langchain_core.messages import AIMessage, HumanMessage
from backend.agent.state import State
from langgraph.types import Command
chat_router = APIRouter()

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
        print(f"Error initializing routes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@chat_router.post("/")

async def send_message(request: ChatRequest) -> ChatResponse:
    try : 
        init_components()
        session_id = request.session_id or str(uuid.uuid4())

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

        return ChatResponse(
            message=last_message,
            session_id=session_id,
            metadata={
                "user_intent": result.get("user_intent"),
                "sql_query": result.get("sql_query"),
                "sql_safety_status": result.get("sql_safety_status"),
                "sql_syntax_status": result.get("sql_syntax_status"),
                "sql_execution_status": result.get("sql_execution_status"),
            },
        )
    except Exception as e:
        print(f"Error initializing components: {e}")
        raise HTTPException(status_code=500, detail=str(e))
