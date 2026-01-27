"""
Schema Inspector - Automatically generates data dictionary from database schema
This module inspects a PostgreSQL database and generates a comprehensive data dictionary
that can be used by the NL2SQL agent.
"""

import yaml
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from sqlalchemy import create_engine, inspect, MetaData, Table
from sqlalchemy.engine import Engine
from sqlalchemy.sql import text
from dataclasses import dataclass, field, asdict
import json


@dataclass
class InspectedColumn:
    """Column information from schema inspection"""
    name: str
    data_type: str
    nullable: bool
    primary_key: bool
    foreign_key: Optional[str] = None
    foreign_table: Optional[str] = None
    default: Optional[str] = None
    description: str = ""
    examples: List[str] = field(default_factory=list)


@dataclass
class InspectedTable:
    """Table information from schema inspection"""
    name: str
    description: str
    primary_key: str
    columns: Dict[str, InspectedColumn]
    relationships: Dict[str, str] = field(default_factory=dict)
    row_count: Optional[int] = None
    sample_data: List[Dict[str, Any]] = field(default_factory=list)


class SchemaInspector:
    """
    Inspects a database schema and generates a data dictionary.
    
    Usage:
        inspector = SchemaInspector(engine)
        dictionary = inspector.generate_dictionary()
        inspector.save_to_file('data_dictionary.json')
    """
    
    def __init__(self, engine: Engine, sample_rows: int = 3):
        """
        Initialize the schema inspector.
        
        Args:
            engine: SQLAlchemy engine connected to the database
            sample_rows: Number of sample rows to fetch for each table
        """
        self.engine = engine
        self.inspector = inspect(engine)
        self.metadata = MetaData()
        self.metadata.reflect(bind=engine)
        self.sample_rows = sample_rows
        self.dialect = engine.dialect.name
        
    def inspect_table(self, table_name: str) -> InspectedTable:
        """
        Inspect a single table and return its structure.
        
        Args:
            table_name: Name of the table to inspect
            
        Returns:
            InspectedTable with all column and relationship information
        """
        # Get table columns
        columns_info = self.inspector.get_columns(table_name)
        pk_constraint = self.inspector.get_pk_constraint(table_name)
        foreign_keys = self.inspector.get_foreign_keys(table_name)
        
        # Get primary key
        primary_key = pk_constraint['constrained_columns'][0] if pk_constraint['constrained_columns'] else None
        
        # Build column dictionary
        columns = {}
        relationships = {}
        
        for col_info in columns_info:
            col_name = col_info['name']
            col_type = str(col_info['type'])
            
            foreign_key = None
            foreign_table = None
            for fk in foreign_keys:
                if col_name in fk['constrained_columns']:
                    foreign_key = fk['name']
                    foreign_table = fk['referred_table']
                    relationships[col_name] = foreign_table
                    break
            
            is_pk = col_name == primary_key if primary_key else False
            
            columns[col_name] = InspectedColumn(
                name=col_name,
                data_type=col_type,
                nullable=col_info.get('nullable', True),
                primary_key=is_pk,
                foreign_key=foreign_key,
                foreign_table=foreign_table,
                default=str(col_info.get('default', '')),
                description=self._generate_column_description(col_name, col_type, foreign_table)
            )
        
        sample_data = self._get_sample_data(table_name)
        
        # Get row count
        row_count = self._get_row_count(table_name)
        
        # Extract examples from sample data
        for col_name, col_def in columns.items():
            if sample_data:
                examples = [str(row.get(col_name, '')) for row in sample_data[:3] if row.get(col_name) is not None]
                col_def.examples = list(set(examples))[:3]  # Unique examples, max 3
        
        return InspectedTable(
            name=table_name,
            description=self._generate_table_description(table_name, columns, relationships),
            primary_key=primary_key or "id",
            columns=columns,
            relationships=relationships,
            row_count=row_count,
            sample_data=sample_data
        )
    
    def _generate_table_description(self, table_name: str, columns: Dict[str, InspectedColumn], 
                                   relationships: Dict[str, str]) -> str:
        """Generate a description for the table based on its structure."""
        # Try to infer table purpose from name and columns
        name_lower = table_name.lower()
        
        if 'player' in name_lower and 'stat' not in name_lower:
            return f"Core player information - master list of all players in the database"
        elif 'team' in name_lower and 'stat' not in name_lower:
            return f"Team information - all teams in the database"
        elif 'game' in name_lower and 'stat' not in name_lower and 'lineup' not in name_lower:
            return f"Game information - comprehensive details about each game played"
        elif 'batting' in name_lower:
            return f"Batting statistics per game for each player - one row per player per game"
        elif 'pitching' in name_lower:
            return f"Pitching statistics per game for each pitcher - one row per pitcher per game"
        elif 'fielding' in name_lower:
            return f"Fielding statistics per game for each player at each position"
        elif 'roster' in name_lower:
            return f"Player-team-season roster relationships"
        elif 'season' in name_lower:
            return f"Aggregated player statistics by season - pre-computed season totals"
        else:
            return f"Table containing {table_name.replace('_', ' ')} data"
    
    def _generate_column_description(self, col_name: str, col_type: str, foreign_table: Optional[str]) -> str:
        """Generate a description for a column based on its name and type."""
        name_lower = col_name.lower()
        
        # Foreign key descriptions
        if foreign_table:
            return f"References {foreign_table}.{col_name.replace('_id', '')}"
        
        # Common patterns
        if col_name.endswith('_id'):
            entity = col_name.replace('_id', '').replace('_', ' ')
            return f"{entity.title()} identifier, references {entity}s table"
        
        if 'date' in name_lower:
            return f"Date in YYYY-MM-DD format"
        
        if 'season' in name_lower or 'year' in name_lower:
            return f"Year/season (e.g., 2020)"
        
        if 'score' in name_lower:
            return f"Score or points"
        
        if 'count' in name_lower or col_name.endswith('s'):
            return f"Count or total number"
        
        if 'average' in name_lower or 'avg' in name_lower:
            return f"Average value (calculated)"
        
        if 'percentage' in name_lower or 'pct' in name_lower:
            return f"Percentage value (calculated)"
        
        # Default description
        return f"{col_name.replace('_', ' ').title()}"
    
    def _get_sample_data(self, table_name: str) -> List[Dict[str, Any]]:
        """Get sample rows from a table."""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(f"SELECT * FROM {table_name} LIMIT {self.sample_rows}"))
                columns = result.keys()
                rows = result.fetchall()
                return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            print(f"Warning: Could not fetch sample data for {table_name}: {e}")
            return []
    
    def _get_row_count(self, table_name: str) -> Optional[int]:
        """Get the number of rows in a table."""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                return result.scalar()
        except Exception:
            return None
    
    def generate_dictionary(self, table_names: Optional[List[str]] = None) -> Dict[str, InspectedTable]:
        """
        Generate a complete data dictionary for the database.
        
        Args:
            table_names: Optional list of table names to inspect. If None, inspects all tables.
            
        Returns:
            Dictionary mapping table names to InspectedTable objects
        """
        if table_names is None:
            table_names = self.inspector.get_table_names()
        
        dictionary = {}
        for table_name in table_names:
            try:
                print(f"Inspecting table: {table_name}")
                dictionary[table_name] = self.inspect_table(table_name)
            except Exception as e:
                print(f"Error inspecting table {table_name}: {e}")
                continue
        
        return dictionary
    
    def to_data_dictionary_format(self, dictionary: Dict[str, InspectedTable]) -> Dict[str, Any]:
        """
        Convert inspected tables to the format used by data_dictionary.py.
        
        Args:
            dictionary: Dictionary of InspectedTable objects
            
        Returns:
            Dictionary in the format compatible with DATA_DICTIONARY
        """
        formatted = {}
        
        for table_name, table in dictionary.items():
            columns_dict = {}
            for col_name, col in table.columns.items():
                columns_dict[col_name] = {
                    "name": col.name,
                    "data_type": col.data_type,
                    "description": col.description,
                    "examples": col.examples,
                    "nullable": col.nullable,
                    "foreign_key": col.foreign_key,
                    "foreign_table": col.foreign_table,
                    "primary_key": col.primary_key
                }
            
            formatted[table_name] = {
                "name": table.name,
                "description": table.description,
                "primary_key": table.primary_key,
                "columns": columns_dict,
                "relationships": table.relationships,
                "row_count": table.row_count
            }
        
        return formatted
    
    def save(self, dictionary: Dict[str, InspectedTable], filepath: str):
    def save_to_json(self, dictionary: Dict[str, InspectedTable], filepath: str):
        """Save the dictionary to a JSON file."""
        formatted = self.to_data_dictionary_format(dictionary)
        
        # Convert to JSON-serializable format
        json_dict = {}
        for table_name, table_data in formatted.items():
            json_dict[table_name] = {
                "name": table_data["name"],
                "description": table_data["description"],
                "primary_key": table_data["primary_key"],
                "columns": {
                    col_name: {
                        "name": col["name"],
                        "data_type": col["data_type"],
                        "description": col["description"],
                        "examples": col["examples"],
                        "nullable": col["nullable"],
                        "foreign_key": col["foreign_key"],
                        "foreign_table": col["foreign_table"]
                    }
                    for col_name, col in table_data["columns"].items()
                },
                "relationships": table_data["relationships"],
                "row_count": table_data["row_count"]
            }
        
        with open(filepath, 'w') as f:
            json.dump(json_dict, f, indent=2, default=str)
        
        print(f"Dictionary saved to {filepath}")
    
    def save_to_yaml(self, dictionary: Dict[str, InspectedTable], filepath: str):
        """Save the dictionary to a YAML file."""
        formatted = self.to_data_dictionary_format(dictionary)
        
        with open(filepath, 'w') as f:
            yaml.dump(formatted, f, default_flow_style=False, sort_keys=False)
        
        print(f"Dictionary saved to {filepath}")
    
    def generate_python_code(self, dictionary: Dict[str, InspectedTable], filepath: str):
        """
        Generate Python code that can be imported as DATA_DICTIONARY.
        
        Args:
            dictionary: Dictionary of InspectedTable objects
            filepath: Path to save the Python file
        """
        formatted = self.to_data_dictionary_format(dictionary)
        
        code = '''"""
Auto-generated data dictionary from database schema inspection.
Generated by SchemaInspector.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

@dataclass
class ColumnDefinition:
    """Definition of a database column"""
    name: str
    data_type: str
    description: str
    examples: List[str] = field(default_factory=list)
    nullable: bool = True
    foreign_key: Optional[str] = None
    foreign_table: Optional[str] = None
    calculated: bool = False
    formula: Optional[str] = None

@dataclass
class TableDefinition:
    """Definition of a database table"""
    name: str
    description: str
    primary_key: str
    columns: Dict[str, ColumnDefinition]
    relationships: Dict[str, str] = field(default_factory=dict)
    common_queries: List[str] = field(default_factory=list)
    notes: str = ""

DATA_DICTIONARY: Dict[str, TableDefinition] = {
'''
        
        for table_name, table_data in formatted.items():
            code += f'    "{table_name}": TableDefinition(\n'
            code += f'        name="{table_data["name"]}",\n'
            code += f'        description="""{table_data["description"]}""",\n'
            code += f'        primary_key="{table_data["primary_key"]}",\n'
            code += '        columns={\n'
            
            for col_name, col_data in table_data["columns"].items():
                code += f'            "{col_name}": ColumnDefinition(\n'
                code += f'                name="{col_data["name"]}",\n'
                code += f'                data_type="{col_data["data_type"]}",\n'
                code += f'                description="""{col_data["description"]}""",\n'
                if col_data["examples"]:
                    examples_str = ', '.join([f'"{ex}"' for ex in col_data["examples"]])
                    code += f'                examples=[{examples_str}],\n'
                code += f'                nullable={col_data["nullable"]},\n'
                if col_data["foreign_key"]:
                    code += f'                foreign_key="{col_data["foreign_key"]}",\n'
                if col_data["foreign_table"]:
                    code += f'                foreign_table="{col_data["foreign_table"]}",\n'
                code += '            ),\n'
            
            code += '        },\n'
            
            if table_data["relationships"]:
                code += '        relationships={\n'
                for col, foreign_table in table_data["relationships"].items():
                    code += f'            "{col}": "{foreign_table}",\n'
                code += '        },\n'
            
            code += '    ),\n'
        
        code += '}\n'
        
        with open(filepath, 'w') as f:
            f.write(code)
        
        print(f"Python code generated at {filepath}")
    
    def print_summary(self, dictionary: Dict[str, InspectedTable]):
        """Print a summary of the inspected schema."""
        print("\n" + "=" * 60)
        print("SCHEMA INSPECTION SUMMARY")
        print("=" * 60)
        print(f"Total tables inspected: {len(dictionary)}")
        print(f"Database dialect: {self.dialect}")
        print("\nTables:")
        
        for table_name, table in dictionary.items():
            print(f"\n  {table_name}")
            print(f"    Description: {table.description}")
            print(f"    Primary Key: {table.primary_key}")
            print(f"    Columns: {len(table.columns)}")
            print(f"    Relationships: {len(table.relationships)}")
            if table.row_count is not None:
                print(f"    Row Count: {table.row_count:,}")
        
        print("\n" + "=" * 60)


# Example usage function (not meant to be called directly, but shows how to use it)
def inspect_schema_from_connection_string(connection_string: str, output_format: str = "python"):
    """
    Inspect schema from a connection string and generate data dictionary.
    
    Args:
        connection_string: SQLAlchemy connection string (e.g., "postgresql://user:pass@host:port/db")
        output_format: Output format - "python", "json", or "yaml"
    
    This function would be called like:
        inspect_schema_from_connection_string(
            "postgresql://baseball:baseball@localhost:5433/retrosheet",
            output_format="python"
        )
    """
    engine = create_engine(connection_string)
    inspector = SchemaInspector(engine, sample_rows=3)
    
    # Generate dictionary
    dictionary = inspector.generate_dictionary()
    
    # Print summary
    inspector.print_summary(dictionary)
    
    # Save in requested format
    if output_format == "python":
        inspector.generate_python_code(dictionary, "backend/knowledge/generated_data_dictionary.py")
    elif output_format == "json":
        inspector.save_to_json(dictionary, "backend/knowledge/generated_data_dictionary.json")
    elif output_format == "yaml":
        inspector.save_to_yaml(dictionary, "backend/knowledge/generated_data_dictionary.yaml")
    
    return dictionary
