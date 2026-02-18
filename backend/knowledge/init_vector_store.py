"""
Initialize the vector store with schema documents and SQL examples.

Run this script once to populate the vector store with:
1. Database schema information (tables, columns, relationships)
2. SQL query examples

This enables RAG-based retrieval of relevant schema parts during query generation.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

load_dotenv()

from backend.database.db_connect import DBConnector
from backend.knowledge.vector_store import VectorStore
from backend.knowledge.data_dictionary import DataDictionary
from backend.knowledge.few_shot_examples import SQLExample

def initialize_vector_store():
    """Initialize vector store with schema and examples."""
    print("Initializing vector store...")
    
    try:
        # Initialize database connector
        print("1. Connecting to database...")
        db_connector = DBConnector()
        print("   ✓ Database connected")
        print(db_connector.get_engine().url)

        # Initialize vector store
        print("2. Initializing vector store...")
        vector_store = VectorStore(db_connector)
        print("   ✓ Vector store initialized")
        
        # Get data dictionary from database
        print("3. Loading database schema...")
        data_dictionary = DataDictionary.from_db_connector(db_connector)
        print(f"   ✓ Found {len(data_dictionary.databases)} database(s)")
        
        # Get schema documents
        print("4. Creating schema documents...")
        schema_docs = vector_store.get_documents_from_data_dictionary(data_dictionary)
        print(f"   ✓ Created {len(schema_docs)} schema documents")
        
        # Add schema documents to vector store
        print("5. Adding schema documents to vector store...")
        vector_store.add_documents(schema_docs)
        print("   ✓ Schema documents added")
        
        # Load SQL examples
        print("6. Loading SQL examples...")
        sql_examples_path = project_root / "backend" / "config" / "sql_examples.yml"
        if sql_examples_path.exists():
            sql_examples = SQLExample.from_yaml(sql_examples_path)
            print(f"   ✓ Loaded {len(sql_examples)} SQL examples")
            
            # Get example documents
            example_docs = vector_store.get_documents_from_sql_examples(sql_examples)
            print(f"   ✓ Created {len(example_docs)} example documents")
            
            # Add example documents to vector store
            print("7. Adding SQL examples to vector store...")
            vector_store.add_documents(example_docs)
            print("   ✓ SQL examples added")
        else:
            print(f"   ⚠ SQL examples file not found: {sql_examples_path}")
            print("   Continuing without examples...")
        
        print("\n" + "="*60)
        print("✓ Vector store initialization complete!")
        print("="*60)
        print(f"\nTotal documents in vector store:")
        print(f"  - Schema documents: {len(schema_docs)}")
        if sql_examples_path.exists():
            print(f"  - SQL examples: {len(example_docs)}")
        print(f"  - Total: {len(schema_docs) + (len(example_docs) if sql_examples_path.exists() else 0)}")
        
    except Exception as e:
        print(f"\n❌ Error initializing vector store: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    initialize_vector_store()
