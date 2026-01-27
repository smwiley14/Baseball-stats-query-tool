"""
Example usage of the data dictionary in agent creation
"""

from backend.knowledge.data_dictionary import (
    DATA_DICTIONARY,
    TERMINOLOGY_MAP,
    get_table_info,
    get_full_dictionary_text,
    get_table_summary
)

# Example 1: Get information about a specific table
print("=" * 60)
print("Example 1: Table Information")
print("=" * 60)
print(get_table_info("batting_stats"))

# Example 2: Get terminology mapping
print("\n" + "=" * 60)
print("Example 2: Terminology Mapping")
print("=" * 60)
user_terms = ["home runs", "rbi", "era", "batting average"]
for term in user_terms:
    db_column = TERMINOLOGY_MAP.get(term.lower(), "Not found")
    print(f"'{term}' -> {db_column}")

# Example 3: Get table summary
print("\n" + "=" * 60)
print("Example 3: Table Summary")
print("=" * 60)
summary = get_table_summary()
for table_name, description in summary.items():
    print(f"{table_name}: {description[:60]}...")

# Example 4: Use in agent prompt
print("\n" + "=" * 60)
print("Example 4: Full Dictionary for Agent Prompt")
print("=" * 60)
dictionary_text = get_full_dictionary_text()
print(dictionary_text[:500] + "...")  # First 500 chars

# Example 5: Access specific column information
print("\n" + "=" * 60)
print("Example 5: Column Details")
print("=" * 60)
batting_table = DATA_DICTIONARY["batting_stats"]
home_runs_col = batting_table.columns["home_runs"]
print(f"Column: {home_runs_col.name}")
print(f"Type: {home_runs_col.data_type}")
print(f"Description: {home_runs_col.description}")
print(f"Examples: {home_runs_col.examples}")
