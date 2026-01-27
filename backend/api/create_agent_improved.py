"""
Improved NL2SQL Agent with Tuning Strategies
This module provides an optimized SQL agent with better prompt engineering,
few-shot examples, and domain-specific knowledge.
"""

import sys
import os
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import database connection - adjust path based on your structure
try:
    from backend.db.db_connect import get_db
except ImportError:
    # Fallback: try relative import
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from db.db_connect import get_db
from langchain_openai import ChatOpenAI
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain.agents import create_agent
from langchain_community.utilities.sql_database import SQLDatabase
from backend.knowledge.data_dictionary import (
    DATA_DICTIONARY,
    TERMINOLOGY_MAP,
    get_full_dictionary_text
)
import dotenv

dotenv.load_dotenv()

openai_api_key = os.getenv("OPENAI_API_KEY")
langchain_api_key = os.getenv("LANGCHAIN_API_KEY")
langchain_project = os.getenv("LANGCHAIN_PROJECT")
langchain_tracing_v2 = os.getenv("LANGCHAIN_TRACING_V2")
langsmith_endpoint = os.getenv("LANGSMITH_ENDPOINT")


def get_enhanced_db():
    """
    Create an enhanced SQLDatabase with better configuration for NL2SQL.
    Key improvements:
    - sample_rows_in_table_info: Shows example data to help understand schema
    - custom_table_info: Provides domain-specific descriptions
    """
    db = get_db()
    
    # Build custom table info from data dictionary
    custom_table_info = {}
    for table_name, table_def in DATA_DICTIONARY.items():
        col_descriptions = []
        for col_name, col_def in table_def.columns.items():
            desc = f"- {col_name} ({col_def.data_type}): {col_def.description}"
            if col_def.examples:
                desc += f" Examples: {', '.join(map(str, col_def.examples[:3]))}"
            if col_def.foreign_key:
                desc += f" [References: {col_def.foreign_key}]"
            if col_def.calculated:
                desc += f" [Calculated: {col_def.formula}]"
            col_descriptions.append(desc)
        
        table_info = f"{table_def.description}\n\nColumns:\n" + "\n".join(col_descriptions)
        
        if table_def.relationships:
            table_info += "\n\nRelationships:\n"
            for col, foreign_table in table_def.relationships.items():
                table_info += f"- {col} -> {foreign_table}\n"
        
        if table_def.common_queries:
            table_info += "\nCommon Query Patterns:\n"
            for query in table_def.common_queries:
                table_info += f"- {query}\n"
        
        custom_table_info[table_name] = table_info
    
    # Create enhanced database with sample rows
    enhanced_db = SQLDatabase(
        engine=db.engine,
        sample_rows_in_table_info=3,  # Show 3 example rows per table
        custom_table_info=custom_table_info,
        include_tables=[
            "players", "teams", "games", 
            "batting_stats", "pitching_stats", "fielding_stats",
            "rosters", "player_seasons", "team_game_stats"
        ],
        ignore_tables=[]  # Explicitly include only what we want
    )
    
    return enhanced_db


def get_baseball_system_prompt(db: SQLDatabase) -> str:
    """
    Create a comprehensive system prompt with domain knowledge and examples.
    """
    # Get data dictionary text
    dictionary_text = get_full_dictionary_text()
    
    # Build terminology mapping text
    terminology_text = "\n".join([
        f"  '{term}' -> {column}"
        for term, column in list(TERMINOLOGY_MAP.items())[:20]  # Show first 20
    ])
    
    return f"""You are an expert baseball statistics SQL assistant with deep knowledge of baseball data.

DATA DICTIONARY:
{dictionary_text}

TERMINOLOGY MAPPING:
When users use these terms, map them to the database columns:
{terminology_text}
(Full mapping available in data dictionary)

DATABASE CONTEXT:

DATABASE CONTEXT:
- You are working with a PostgreSQL database containing comprehensive baseball statistics
- The database uses {db.dialect} SQL syntax
- All dates are stored in DATE format (YYYY-MM-DD)
- Player IDs are strings (e.g., 'troutm001')
- Team IDs are short codes (e.g., 'ANA', 'BOS', 'NYY')

KEY TABLES:
1. **players**: Basic player information (player_id, first_name, last_name, batting_hand, throwing_hand)
2. **batting_stats**: Per-game batting statistics (hits, home_runs, rbis, runs, at_bats, etc.)
3. **pitching_stats**: Per-game pitching statistics (strikeouts, innings_pitched, wins, losses, era, whip)
4. **games**: Game information (game_id, game_date, home_team_id, away_team_id, scores)
5. **teams**: Team information (team_id, league, city, name)

IMPORTANT RULES:
1. **Always JOIN tables properly**: Use player_id to join players with stats, team_id for teams
2. **Date filtering**: Use game_date for date ranges, season for year filtering
3. **Aggregations**: Use SUM() for totals, AVG() for averages, COUNT() for counts
4. **Window functions**: For rolling windows (e.g., 10-game spans), use ROWS BETWEEN 9 PRECEDING AND CURRENT ROW
5. **Player names**: Always JOIN with players table to get first_name and last_name
6. **Limit results**: Default to top 10 unless user specifies otherwise
7. **Never modify data**: Only use SELECT statements, never INSERT/UPDATE/DELETE

COMMON QUERY PATTERNS:

1. **Top performers in a season:**
   SELECT p.first_name, p.last_name, SUM(bs.home_runs) as total_hr
   FROM batting_stats bs
   JOIN players p ON bs.player_id = p.player_id
   WHERE bs.season = 2020
   GROUP BY p.player_id, p.first_name, p.last_name
   ORDER BY total_hr DESC
   LIMIT 10;

2. **Rolling 10-game window:**
   SELECT player_id, game_date,
          SUM(home_runs) OVER (
              PARTITION BY player_id 
              ORDER BY game_date 
              ROWS BETWEEN 9 PRECEDING AND CURRENT ROW
          ) as hr_10_game
   FROM batting_stats
   WHERE game_date IS NOT NULL
   ORDER BY hr_10_game DESC;

3. **Career totals:**
   SELECT p.first_name, p.last_name, 
          SUM(bs.home_runs) as career_hr,
          SUM(bs.at_bats) as career_ab,
          ROUND(SUM(bs.hits)::DECIMAL / NULLIF(SUM(bs.at_bats), 0), 3) as career_avg
   FROM batting_stats bs
   JOIN players p ON bs.player_id = p.player_id
   GROUP BY p.player_id, p.first_name, p.last_name
   HAVING SUM(bs.at_bats) > 0
   ORDER BY career_hr DESC;

4. **Date ranges:**
   WHERE game_date BETWEEN '2020-04-01' AND '2020-10-31'
   OR
   WHERE season = 2020 AND game_date >= '2020-07-01'

BASEBALL TERMINOLOGY MAPPING:
- "HR" or "home runs" → home_runs
- "RBI" or "RBIs" → rbis
- "hits" → hits
- "strikeouts" or "K" → strikeouts (for batters) or strikeouts (for pitchers)
- "ERA" → era (earned run average)
- "WHIP" → whip (walks + hits per inning)
- "AVG" or "batting average" → batting_average
- "OBP" → on_base_percentage
- "SLG" → slugging_percentage
- "OPS" → ops (on-base + slugging)

RESPONSE FORMAT:
- Always provide context: "In the 2020 season..."
- Include player full names when possible
- Format numbers appropriately (batting averages to 3 decimals, ERAs to 2 decimals)
- Explain what the numbers mean when helpful
- If a query fails, explain the error and suggest an alternative approach

Given an input question, create a syntactically correct {db.dialect} query to run,
then look at the results of the query and return the answer in a clear, natural language format.
Limit queries to top 10 results by default unless the user specifies otherwise.
Never perform DML operations (INSERT, UPDATE, DELETE)."""


def create_improved_agent(
    model_name: str = "gpt-4",
    temperature: float = 0,
    use_enhanced_db: bool = True
):
    """
    Create an improved SQL agent with better configuration.
    
    Args:
        model_name: OpenAI model to use (gpt-4 performs better for SQL)
        temperature: LLM temperature (0 for deterministic SQL)
        use_enhanced_db: Whether to use enhanced database with samples
    
    Returns:
        Configured agent
    """
    # Get database (enhanced or standard)
    if use_enhanced_db:
        db = get_enhanced_db()
    else:
        db = get_db()
    
    # Use GPT-4 for better SQL generation (more accurate than GPT-3.5)
    llm = ChatOpenAI(
        model=model_name,
        temperature=temperature,
        api_key=openai_api_key
    )
    
    # Create toolkit with the LLM
    toolkit = SQLDatabaseToolkit(db=db, llm=llm)
    tools = toolkit.get_tools()
    
    # Get enhanced system prompt
    system_prompt = get_baseball_system_prompt(db)
    
    # Create agent with improved prompt
    agent = create_agent(
        llm, 
        tools, 
        system_prompt=system_prompt
    )
    
    return agent, db


# For backward compatibility
def create_agent():
    """Original function signature for backward compatibility."""
    agent, _ = create_improved_agent(model_name="gpt-3.5-turbo")
    return agent
