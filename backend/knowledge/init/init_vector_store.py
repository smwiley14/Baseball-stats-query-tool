"""Initialize the vector store with schema documents and SQL examples."""

from pathlib import Path

from database.db_connect import DBConnector
from knowledge.vector_store import VectorStore
from knowledge.data_dictionary import DataDictionary
from knowledge.few_shot_examples import SQLExample

project_root = Path(__file__).parent.parent.parent

def init_knowledge_base():
    """Initialize vector store with schema and examples."""
    print("Initializing vector store...")
    
    try:
        print("1. Connecting to database...")
        db_connector = DBConnector()
        print("   ✓ Database connected")
        print(db_connector.get_engine().url)

        # Initialize vector store
        print("2. Initializing vector store...")
        vector_store = VectorStore(db_connector)
        print("   ✓ Vector store initialized")

        # Clear existing collection to remove stale/obsolete embeddings.
        # NOTE: After delete_collection(), the PGVector object caches the old UUID.
        # Reinitializing VectorStore forces a fresh collection UUID so add_documents()
        # inserts into the correct (new) collection.
        print("3. Clearing existing vector collection...")
        try:
            vector_store.vectorstore.delete_collection()
            vector_store = VectorStore(db_connector)
            print("   ✓ Collection reset (stale docs removed)")
        except Exception as e:
            print(f"   ⚠ Could not reset collection cleanly: {e}")
            print("   Continuing with best-effort reseed...")
        
        # Get data dictionary from database
        print("4. Loading database schema...")
        data_dictionary = DataDictionary.load(project_root / "configs" / "db_dict.yml")
        print(f"   ✓ Found {len(data_dictionary.databases)} database(s)")
        
        # Get schema documents
        print("5. Creating schema documents...")
        schema_docs = vector_store.get_documents_from_data_dictionary(data_dictionary)
        print(f"   ✓ Created {len(schema_docs)} schema documents")
        
        # Add schema documents to vector store
        print("6. Adding schema documents to vector store...")
        vector_store.add_documents(schema_docs)
        print("   ✓ Schema documents added")
        
        # Load SQL examples
        print("7. Loading SQL examples...")
        sql_examples_path = project_root / "configs" / "sql_examples.yml"
        if sql_examples_path.exists():
            sql_examples = SQLExample.from_yaml(sql_examples_path)
            print(f"   ✓ Loaded {len(sql_examples)} SQL examples")
            
            # Get example documents
            example_docs = vector_store.get_documents_from_sql_examples(sql_examples)
            print(f"   ✓ Created {len(example_docs)} example documents")
            
            # Add example documents to vector store
            print("8. Adding SQL examples to vector store...")
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
        raise


def initialize_vector_store():
    """Backward-compatible alias."""
    return init_knowledge_base()

if __name__ == "__main__":
    init_knowledge_base()
