# Data Dictionary for NL2SQL Agent

This directory contains comprehensive knowledge about the baseball statistics database to help the NL2SQL agent generate accurate queries.

## Files

- **`data_dictionary.py`**: Complete data dictionary with table definitions, column descriptions, relationships, and terminology mappings
- **`dictionary.py`**: Original dictionary class (legacy)
- **`vector_store.py`**: Vector store for semantic search (if needed)

## Usage

### In Agent Creation

```python
from backend.knowledge.data_dictionary import (
    DATA_DICTIONARY,
    TERMINOLOGY_MAP,
    get_full_dictionary_text
)

# Use in system prompt
dictionary_text = get_full_dictionary_text()
system_prompt = f"""
You are a SQL assistant. Here's the database schema:

{dictionary_text}
...
"""
```

### Get Table Information

```python
from backend.knowledge.data_dictionary import get_table_info

# Get detailed info about a table
info = get_table_info("batting_stats")
print(info)
```

### Terminology Mapping

```python
from backend.knowledge.data_dictionary import TERMINOLOGY_MAP

# Map user terms to database columns
user_term = "home runs"
db_column = TERMINOLOGY_MAP.get(user_term.lower(), user_term)
# Returns: "home_runs"
```

## Data Dictionary Structure

Each table definition includes:
- **Description**: What the table contains
- **Primary Key**: Unique identifier
- **Columns**: Detailed column definitions with:
  - Data type
  - Description
  - Examples
  - Foreign key relationships
  - Calculated field formulas
- **Relationships**: Foreign key mappings
- **Common Queries**: Example query patterns
- **Notes**: Additional context

## Terminology Mapping

The dictionary includes mappings from common baseball terms to database columns:
- "HR" / "home runs" → `home_runs`
- "RBI" / "rbis" → `rbis`
- "ERA" → `era`
- "AVG" / "batting average" → `batting_average`
- etc.

## Benefits

1. **Better Query Accuracy**: Agent understands column meanings and relationships
2. **Terminology Handling**: Maps user-friendly terms to database columns
3. **Relationship Awareness**: Knows how to join tables correctly
4. **Example Values**: Understands data formats and ranges
5. **Calculated Fields**: Knows which fields are computed and how

## Updating the Dictionary

To add or modify definitions:

1. Edit `data_dictionary.py`
2. Add new `ColumnDefinition` entries
3. Update `TERMINOLOGY_MAP` for new terms
4. Test with agent queries

The dictionary is automatically used by `create_agent_improved.py` when creating enhanced agents.
