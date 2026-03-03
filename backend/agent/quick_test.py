"""
Quick test script - minimal setup to test your agent flow.
Run this from the backend/agent directory.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

load_dotenv()

# Enable LangSmith tracing
os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")
os.environ.setdefault("LANGCHAIN_PROJECT", "Baseball-Stats-Agent")
# LangSmith API key should be in .env as LANGCHAIN_API_KEY

from langchain_core.messages import HumanMessage
from database.db_connect import DBConnector
from knowledge.vector_store import VectorStore
from agent.agent import create_graph
from agent.state import State

def quick_test(query: str = "How many players are in the database?"):
    """Quick test function."""
    print(f"\n🔍 Testing: {query}\n")
    
    try:
        # Initialize
        print("1. Initializing database...")
        db_connector = DBConnector()
        print("   ✓ Database ready")
        
        print("2. Initializing vector store...")
        vector_store = VectorStore(db_connector)
        print("   ✓ Vector store ready")
        
        print("3. Creating graph...")
        graph = create_graph(db_connector, vector_store)
        app = graph.compile()
        print("   ✓ Graph compiled")
        
        # Create state
        print("4. Creating initial state...")
        initial_state = State(
            user_query=query,
            messages=[HumanMessage(content=query)]
        )
        print("   ✓ State created")
        
        # Run
        print("5. Running agent...\n")
        print("-" * 60)
        result = app.invoke(initial_state)
        print("-" * 60)
        
        # Show results
        print("\n📊 Results:")
        print(f"   Messages: {len(result.get('messages', []))}")
        
        if result.get('messages'):
            last_msg = result['messages'][-1]
            if hasattr(last_msg, 'content'):
                print(f"\n   Response:\n   {last_msg.content}\n")
        
        return result
        
    except Exception as e:
        print(f"\n❌ Error: {e}\n")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    import sys
    
    query = sys.argv[1] if len(sys.argv) > 1 else "How many players are in the database?"
    quick_test(query)
