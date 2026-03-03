"""
Database connection module for PostgreSQL.

Provides database connector that can extract schema information
from a connection string for use with DataDictionary.
"""

import os
from urllib.parse import quote_plus
from typing import Optional

from dotenv import load_dotenv
from langchain_community.utilities.sql_database import SQLDatabase
from sqlalchemy import Engine, create_engine, inspect
from sqlalchemy.engine import Inspector

load_dotenv()


class DBConnector:
    """
    Database connector that extracts schema from connection string.
    
    Can be initialized with:
    - Connection string directly
    - Individual connection parameters
    - Environment variables (default)
    """
    
    def __init__(
        self,
        connection_string: Optional[str] = None,
        host: Optional[str] = None,
        port: Optional[int] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        database: Optional[str] = None,
    ):
        """
        Initialize DBConnector.
        
        Args:
            connection_string: Full PostgreSQL connection string
            host: Database host (defaults to POSTGRES_HOST env var)
            port: Database port (defaults to POSTGRES_PORT env var)
            user: Database user (defaults to POSTGRES_USER env var)
            password: Database password (defaults to POSTGRES_PASSWORD env var)
            database: Database name (defaults to POSTGRES_DB env var)
        """
        if connection_string:
            self.connection_string = connection_string
        else:
            # Build from individual parameters or env vars
            self.host = host or os.getenv("POSTGRES_HOST", "localhost")
            self.port = port or int(os.getenv("POSTGRES_PORT", "5433"))
            self.user = user or os.getenv("POSTGRES_USER", "baseball")
            self.password = password or os.getenv("POSTGRES_PASSWORD", "baseball")
            self.database = database or os.getenv("POSTGRES_DB", "retrosheet")
            
            # Build connection string with URL encoding
            self.connection_string = (
                f"postgresql://{quote_plus(self.user)}:"
                f"{quote_plus(self.password)}@{self.host}:{self.port}/{self.database}"
            )
        
        # Lazy initialization
        self._engine: Optional[Engine] = None
        self._inspector: Optional[Inspector] = None
        self._db: Optional[SQLDatabase] = None
        self._database_schema: Optional[dict] = None
    
    def get_engine(self) -> Engine:
        """Get or create SQLAlchemy engine."""
        if self._engine is None:
            self._engine = create_engine(
                self.connection_string,
                pool_pre_ping=True,
                pool_size=5,
                max_overflow=10,
                echo=False,
            )
        return self._engine
    
    def get_inspector(self) -> Inspector:
        """Get or create SQLAlchemy inspector."""
        if self._inspector is None:
            self._inspector = inspect(self.get_engine())
        return self._inspector
    
    def get_schema(self) -> dict[str, dict[str, list[str]]]:
        """
        Get database schema structure.
        
        Returns:
            Dictionary in format: {database_name: {schema_name: [table_names]}}
            Example: {"retrosheet": {"public": ["players", "games", ...]}}
        """
        if self._database_schema is None:
            inspector = self.get_inspector()
            
            # Get database name from connection string
            # Extract from connection string or use the database parameter
            if hasattr(self, 'database'):
                db_name = self.database
            else:
                db_name = self.connection_string.split('/')[-1].split('?')[0]
            
            # Get all schemas
            schemas = inspector.get_schema_names()
            
            schema_dict = {}
            for schema_name in schemas:
                # Skip system schemas
                if schema_name in ['information_schema', 'pg_catalog', 'pg_toast']:
                    continue
                
                tables = inspector.get_table_names(schema=schema_name)
                if tables:  
                    schema_dict[schema_name] = tables
            
            self._database_schema = {db_name: schema_dict}
        
        return self._database_schema
    
    def get_db(self) -> SQLDatabase:
        """Get or create LangChain SQLDatabase instance."""
        if self._db is None:
            self._db = SQLDatabase(self.get_engine())
        return self._db
    
    @property
    def engine(self) -> Engine:
        """Get engine (property access)."""
        return self.get_engine()
    
    @property
    def inspector(self) -> Inspector:
        """Get inspector (property access)."""
        return self.get_inspector()
    
    @property
    def database_schema(self) -> dict[str, dict[str, list[str]]]:
        """Get database schema structure (property access for DataDictionary)."""
        return self.get_schema()
