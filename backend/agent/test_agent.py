"""
Test script for the LangGraph NL2SQL agent.

This script provides a simple way to test your agent flow with various queries.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

load_dotenv()

# Enable LangSmith tracing
os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")
os.environ.setdefault("LANGCHAIN_PROJECT", "Baseball-Stats-Agent")
# LangSmith API key should be in .env as LANGCHAIN_API_KEY

from backend.database.db_connect import DBConnector
from backend.knowledge.vector_store import VectorStore
from backend.agent.agent import create_graph
from backend.agent.state import State


def create_test_state(user_query: str) -> State:
    """Create a test state with a user query."""
    return State(
        user_query=user_query,
        messages=[HumanMessage(content=user_query)]
    )


def test_agent(query: str, verbose: bool = True):
    """
    Test the agent with a given query.
    
    Args:
        query: The natural language query to test
        verbose: Whether to print detailed output
    """
    print(f"\n{'='*60}")
    print(f"Testing Query: {query}")
    print(f"{'='*60}\n")
    
    try:
        # Initialize dependencies
        print("Initializing database connection...")
        db_connector = DBConnector()
        print("✓ Database connection initialized")
        
        print("Initializing vector store...")
        vector_store = VectorStore(db_connector)
        print("✓ Vector store initialized")
        
        # Create the graph
        print("Creating agent graph...")
        graph = create_graph(db_connector, vector_store)
        print("✓ Graph created")
        
        # Compile the graph
        print("Compiling graph...")
        app = graph.compile()
        print("✓ Graph compiled\n")
        
        # Create initial state
        initial_state = create_test_state(query)
        
        if verbose:
            print(f"Initial State:")
            print(f"  User Query: {initial_state.user_query}")
            print(f"  Messages: {len(initial_state.messages)} message(s)\n")
        
        # Run the agent
        print("Running agent...")
        print("-" * 60)
        
        result = app.invoke(initial_state)
        
        print("-" * 60)
        print("\n✓ Agent execution completed\n")
        
        # Display results
        if verbose:
            print("Final State:")
            print(f"  User Query: {result.get('user_query', 'N/A')}")
            print(f"  Messages: {len(result.get('messages', []))} message(s)")
            
            # Print last message if available
            if result.get('messages'):
                last_message = result['messages'][-1]
                print(f"\nLast Message:")
                print(f"  Type: {type(last_message).__name__}")
                if hasattr(last_message, 'content'):
                    print(f"  Content: {last_message.content[:200]}..." if len(str(last_message.content)) > 200 else f"  Content: {last_message.content}")
            
            # Print any additional state fields
            for key, value in result.items():
                if key not in ['user_query', 'messages']:
                    print(f"  {key}: {value}")
        
        return result
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        if verbose:
            print("\nFull traceback:")
            traceback.print_exc()
        return None


def interactive_mode():
    """Run the agent in interactive mode."""
    print("\n" + "="*60)
    print("LangGraph Agent - Interactive Mode")
    print("="*60)
    print("Type your queries (or 'quit' to exit)\n")
    
    # Initialize once
    try:
        db_connector = DBConnector()
        vector_store = VectorStore(db_connector)
        graph = create_graph(db_connector, vector_store)
        app = graph.compile()
        print("✓ Agent initialized and ready!\n")
    except Exception as e:
        print(f"❌ Failed to initialize agent: {e}")
        return
    
    while True:
        try:
            query = input("Query: ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
            
            if not query:
                continue
            
            initial_state = create_test_state(query)
            result = app.invoke(initial_state)
            
            # Print the response
            if result.get('messages'):
                last_message = result['messages'][-1]
                if hasattr(last_message, 'content'):
                    print(f"\nResponse: {last_message.content}\n")
                else:
                    print(f"\nResponse: {last_message}\n")
            else:
                print(f"\nResult: {result}\n")
                
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}\n")


def run_test_suite():
    """Run a suite of test queries."""
    test_queries = [
        "How many players are in the database?",
        "How many games were played in 2020?",
        "Who are the top 5 home run hitters in 2020?",
        "What is the batting average for Aaron Judge in 2020?",
    ]
    
    print("\n" + "="*60)
    print("Running Test Suite")
    print("="*60)
    
    results = []
    for i, query in enumerate(test_queries, 1):
        print(f"\n[{i}/{len(test_queries)}]")
        result = test_agent(query, verbose=False)
        results.append((query, result))
    
    print("\n" + "="*60)
    print("Test Suite Summary")
    print("="*60)
    
    for query, result in results:
        status = "✓" if result else "❌"
        print(f"{status} {query}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test the LangGraph NL2SQL agent")
    parser.add_argument(
        "--query",
        type=str,
        help="Single query to test"
    )
    parser.add_argument(
        "--interactive",
        "-i",
        action="store_true",
        help="Run in interactive mode"
    )
    parser.add_argument(
        "--suite",
        action="store_true",
        help="Run test suite"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        default=True,
        help="Verbose output"
    )
    
    args = parser.parse_args()
    
    if args.interactive:
        interactive_mode()
    elif args.suite:
        run_test_suite()
    elif args.query:
        test_agent(args.query, verbose=args.verbose)
    else:
        # Default: run a simple test
        print("No query specified. Running default test...")
        test_agent("How many players are in the database?", verbose=True)
