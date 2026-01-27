"""
Comprehensive Data Dictionary for Baseball Statistics Database
This dictionary provides detailed information about all tables, columns, relationships,
and domain-specific knowledge to help the NL2SQL agent generate accurate queries.
"""

from typing import Dict, List, Any
from dataclasses import dataclass, field


@dataclass
class ColumnDefinition:
    """Definition of a database column"""
    name: str
    data_type: str
    description: str
    examples: List[str] = field(default_factory=list)
    nullable: bool = True
    foreign_key: str = None
    calculated: bool = False
    formula: str = None


@dataclass
class TableDefinition:
    """Definition of a database table"""
    name: str
    description: str
    primary_key: str
    columns: Dict[str, ColumnDefinition]
    relationships: Dict[str, str] = field(default_factory=dict)  # column -> foreign_table
    common_queries: List[str] = field(default_factory=list)
    notes: str = ""


# Comprehensive data dictionary
DATA_DICTIONARY: Dict[str, TableDefinition] = {
    "players": TableDefinition(
        name="players",
        description="Core player information - master list of all players in the database",
        primary_key="player_id",
        columns={
            "player_id": ColumnDefinition(
                name="player_id",
                data_type="VARCHAR(10)",
                description="Unique player identifier in Retrosheet format (e.g., 'troutm001' = Mike Trout)",
                examples=["troutm001", "judgaa01", "bettsmo01"],
                nullable=False
            ),
            "first_name": ColumnDefinition(
                name="first_name",
                data_type="VARCHAR(50)",
                description="Player's first name",
                examples=["Mike", "Aaron", "Mookie"],
                nullable=True
            ),
            "last_name": ColumnDefinition(
                name="last_name",
                data_type="VARCHAR(50)",
                description="Player's last name",
                examples=["Trout", "Judge", "Betts"],
                nullable=True
            ),
            "batting_hand": ColumnDefinition(
                name="batting_hand",
                data_type="CHAR(1)",
                description="Batting hand: L (left), R (right), S (switch hitter)",
                examples=["L", "R", "S"],
                nullable=True
            ),
            "throwing_hand": ColumnDefinition(
                name="throwing_hand",
                data_type="CHAR(1)",
                description="Throwing hand: L (left), R (right)",
                examples=["L", "R"],
                nullable=True
            ),
        },
        relationships={},
        common_queries=[
            "Find player by name: WHERE LOWER(last_name) = 'trout' AND LOWER(first_name) = 'mike'",
            "Get all switch hitters: WHERE batting_hand = 'S'"
        ],
        notes="Always join this table when you need player names in results"
    ),
    
    "teams": TableDefinition(
        name="teams",
        description="Team information - all teams in the database",
        primary_key="team_id",
        columns={
            "team_id": ColumnDefinition(
                name="team_id",
                data_type="VARCHAR(5)",
                description="Unique team identifier (e.g., 'ANA' = Angels, 'BOS' = Red Sox, 'NYY' = Yankees)",
                examples=["ANA", "BOS", "NYY", "LAD", "HOU"],
                nullable=False
            ),
            "league": ColumnDefinition(
                name="league",
                data_type="CHAR(1)",
                description="League: A (American League), N (National League)",
                examples=["A", "N"],
                nullable=True
            ),
            "city": ColumnDefinition(
                name="city",
                data_type="VARCHAR(50)",
                description="Team's city",
                examples=["Los Angeles", "Boston", "New York"],
                nullable=True
            ),
            "name": ColumnDefinition(
                name="name",
                data_type="VARCHAR(50)",
                description="Team name",
                examples=["Angels", "Red Sox", "Yankees"],
                nullable=True
            ),
            "full_name": ColumnDefinition(
                name="full_name",
                data_type="VARCHAR(100)",
                description="Full team name",
                examples=["Los Angeles Angels", "Boston Red Sox"],
                nullable=True
            ),
        },
        relationships={},
        common_queries=[
            "Find team by city: WHERE city = 'Boston'",
            "Get all AL teams: WHERE league = 'A'"
        ]
    ),
    
    "games": TableDefinition(
        name="games",
        description="Game information - comprehensive details about each game played",
        primary_key="game_id",
        columns={
            "game_id": ColumnDefinition(
                name="game_id",
                data_type="VARCHAR(20)",
                description="Unique game identifier in format TEAMYYYYMMDD (e.g., 'ANA202004050' = Angels game on April 5, 2020)",
                examples=["ANA202004050", "BOS202007150"],
                nullable=False
            ),
            "game_date": ColumnDefinition(
                name="game_date",
                data_type="DATE",
                description="Date of the game in YYYY-MM-DD format",
                examples=["2020-04-05", "2020-07-15"],
                nullable=False
            ),
            "season": ColumnDefinition(
                name="season",
                data_type="INTEGER",
                description="Year/season of the game",
                examples=[2020, 2021, 2019],
                nullable=True
            ),
            "home_team_id": ColumnDefinition(
                name="home_team_id",
                data_type="VARCHAR(5)",
                description="Home team identifier, references teams.team_id",
                examples=["ANA", "BOS"],
                nullable=True,
                foreign_key="teams.team_id"
            ),
            "away_team_id": ColumnDefinition(
                name="away_team_id",
                data_type="VARCHAR(5)",
                description="Away team identifier, references teams.team_id",
                examples=["NYY", "LAD"],
                nullable=True,
                foreign_key="teams.team_id"
            ),
            "home_score": ColumnDefinition(
                name="home_score",
                data_type="INTEGER",
                description="Final score for home team",
                examples=[5, 7, 3],
                nullable=True
            ),
            "away_score": ColumnDefinition(
                name="away_score",
                data_type="INTEGER",
                description="Final score for away team",
                examples=[3, 2, 8],
                nullable=True
            ),
            "park_id": ColumnDefinition(
                name="park_id",
                data_type="VARCHAR(10)",
                description="Ballpark identifier, references parks.park_id",
                examples=["ANA01", "BOS07"],
                nullable=True,
                foreign_key="parks.park_id"
            ),
        },
        relationships={
            "home_team_id": "teams",
            "away_team_id": "teams",
            "park_id": "parks"
        },
        common_queries=[
            "Games in a season: WHERE season = 2020",
            "Games on a date: WHERE game_date = '2020-07-15'",
            "Games in date range: WHERE game_date BETWEEN '2020-04-01' AND '2020-10-31'",
            "Home team wins: WHERE home_score > away_score"
        ]
    ),
    
    "batting_stats": TableDefinition(
        name="batting_stats",
        description="Batting statistics per game for each player - one row per player per game",
        primary_key="id",
        columns={
            "game_id": ColumnDefinition(
                name="game_id",
                data_type="VARCHAR(20)",
                description="Game identifier, references games.game_id",
                examples=["ANA202004050"],
                nullable=True,
                foreign_key="games.game_id"
            ),
            "player_id": ColumnDefinition(
                name="player_id",
                data_type="VARCHAR(10)",
                description="Player identifier, references players.player_id",
                examples=["troutm001"],
                nullable=True,
                foreign_key="players.player_id"
            ),
            "team_id": ColumnDefinition(
                name="team_id",
                data_type="VARCHAR(5)",
                description="Team identifier, references teams.team_id",
                examples=["ANA"],
                nullable=True,
                foreign_key="teams.team_id"
            ),
            "season": ColumnDefinition(
                name="season",
                data_type="INTEGER",
                description="Year/season",
                examples=[2020, 2021],
                nullable=True
            ),
            "game_date": ColumnDefinition(
                name="game_date",
                data_type="DATE",
                description="Date of the game",
                examples=["2020-04-05"],
                nullable=True
            ),
            "at_bats": ColumnDefinition(
                name="at_bats",
                data_type="INTEGER",
                description="Number of at-bats (AB) - official at-bats, excludes walks, HBP, sacrifices",
                examples=[4, 5, 3],
                nullable=True
            ),
            "hits": ColumnDefinition(
                name="hits",
                data_type="INTEGER",
                description="Total hits (H) - sum of singles + doubles + triples + home_runs",
                examples=[2, 3, 1],
                nullable=True
            ),
            "singles": ColumnDefinition(
                name="singles",
                data_type="INTEGER",
                description="Single base hits (1B)",
                examples=[1, 2, 0],
                nullable=True
            ),
            "doubles": ColumnDefinition(
                name="doubles",
                data_type="INTEGER",
                description="Double base hits (2B)",
                examples=[1, 0, 2],
                nullable=True
            ),
            "triples": ColumnDefinition(
                name="triples",
                data_type="INTEGER",
                description="Triple base hits (3B)",
                examples=[0, 1, 0],
                nullable=True
            ),
            "home_runs": ColumnDefinition(
                name="home_runs",
                data_type="INTEGER",
                description="Home runs (HR) - also called 'homeruns' or 'homers'",
                examples=[1, 2, 0],
                nullable=True
            ),
            "rbis": ColumnDefinition(
                name="rbis",
                data_type="INTEGER",
                description="Runs batted in (RBI) - runs driven in by this player",
                examples=[2, 3, 1],
                nullable=True
            ),
            "runs": ColumnDefinition(
                name="runs",
                data_type="INTEGER",
                description="Runs scored (R) - runs scored by this player",
                examples=[1, 2, 0],
                nullable=True
            ),
            "walks": ColumnDefinition(
                name="walks",
                data_type="INTEGER",
                description="Base on balls (BB) - also called 'walks'",
                examples=[1, 2, 0],
                nullable=True
            ),
            "strikeouts": ColumnDefinition(
                name="strikeouts",
                data_type="INTEGER",
                description="Strikeouts (K or SO) - times struck out",
                examples=[1, 0, 2],
                nullable=True
            ),
            "batting_average": ColumnDefinition(
                name="batting_average",
                data_type="DECIMAL(5,3)",
                description="Batting average (AVG) - calculated as hits / at_bats, displayed as .XXX (e.g., .300)",
                examples=["0.300", "0.275", "0.333"],
                nullable=True,
                calculated=True,
                formula="hits / at_bats"
            ),
            "on_base_percentage": ColumnDefinition(
                name="on_base_percentage",
                data_type="DECIMAL(5,3)",
                description="On-base percentage (OBP) - (hits + walks + hit_by_pitch) / (at_bats + walks + hit_by_pitch + sacrifice_flies)",
                examples=["0.400", "0.350"],
                nullable=True,
                calculated=True,
                formula="(hits + walks + hit_by_pitch) / (at_bats + walks + hit_by_pitch + sacrifice_flies)"
            ),
            "slugging_percentage": ColumnDefinition(
                name="slugging_percentage",
                data_type="DECIMAL(5,3)",
                description="Slugging percentage (SLG) - (singles + 2*doubles + 3*triples + 4*home_runs) / at_bats",
                examples=["0.500", "0.600"],
                nullable=True,
                calculated=True,
                formula="(singles + 2*doubles + 3*triples + 4*home_runs) / at_bats"
            ),
            "ops": ColumnDefinition(
                name="ops",
                data_type="DECIMAL(5,3)",
                description="On-base plus slugging (OPS) - on_base_percentage + slugging_percentage",
                examples=["0.900", "1.000"],
                nullable=True,
                calculated=True,
                formula="on_base_percentage + slugging_percentage"
            ),
        },
        relationships={
            "game_id": "games",
            "player_id": "players",
            "team_id": "teams"
        },
        common_queries=[
            "Season totals: GROUP BY player_id, season",
            "Career totals: GROUP BY player_id",
            "Single game: WHERE game_id = '...'",
            "Date range: WHERE game_date BETWEEN ... AND ...",
            "Top performers: ORDER BY SUM(stat) DESC LIMIT 10"
        ],
        notes="Always join with players table to get player names. Use SUM() for aggregations."
    ),
    
    "pitching_stats": TableDefinition(
        name="pitching_stats",
        description="Pitching statistics per game for each pitcher - one row per pitcher per game",
        primary_key="id",
        columns={
            "game_id": ColumnDefinition(
                name="game_id",
                data_type="VARCHAR(20)",
                description="Game identifier, references games.game_id",
                examples=["ANA202004050"],
                nullable=True,
                foreign_key="games.game_id"
            ),
            "player_id": ColumnDefinition(
                name="player_id",
                data_type="VARCHAR(10)",
                description="Pitcher identifier, references players.player_id",
                examples=["kershcl01"],
                nullable=True,
                foreign_key="players.player_id"
            ),
            "team_id": ColumnDefinition(
                name="team_id",
                data_type="VARCHAR(5)",
                description="Team identifier, references teams.team_id",
                examples=["LAD"],
                nullable=True,
                foreign_key="teams.team_id"
            ),
            "season": ColumnDefinition(
                name="season",
                data_type="INTEGER",
                description="Year/season",
                examples=[2020],
                nullable=True
            ),
            "game_date": ColumnDefinition(
                name="game_date",
                data_type="DATE",
                description="Date of the game",
                examples=["2020-04-05"],
                nullable=True
            ),
            "innings_pitched": ColumnDefinition(
                name="innings_pitched",
                data_type="DECIMAL(4,1)",
                description="Innings pitched (IP) - decimal format where 6.1 = 6.1 innings (6 innings, 1 out)",
                examples=["6.0", "7.1", "5.2"],
                nullable=True
            ),
            "strikeouts": ColumnDefinition(
                name="strikeouts",
                data_type="INTEGER",
                description="Strikeouts (K or SO) - strikeouts recorded by pitcher",
                examples=[8, 10, 5],
                nullable=True
            ),
            "hits_allowed": ColumnDefinition(
                name="hits_allowed",
                data_type="INTEGER",
                description="Hits allowed (H) - hits given up by pitcher",
                examples=[5, 3, 7],
                nullable=True
            ),
            "runs_allowed": ColumnDefinition(
                name="runs_allowed",
                data_type="INTEGER",
                description="Total runs allowed (R)",
                examples=[3, 1, 5],
                nullable=True
            ),
            "earned_runs": ColumnDefinition(
                name="earned_runs",
                data_type="INTEGER",
                description="Earned runs allowed (ER) - runs that count toward ERA",
                examples=[2, 1, 4],
                nullable=True
            ),
            "walks_allowed": ColumnDefinition(
                name="walks_allowed",
                data_type="INTEGER",
                description="Walks allowed (BB) - base on balls issued",
                examples=[2, 1, 3],
                nullable=True
            ),
            "win": ColumnDefinition(
                name="win",
                data_type="BOOLEAN",
                description="Win (W) - did pitcher get the win (TRUE/FALSE)",
                examples=[True, False],
                nullable=True
            ),
            "loss": ColumnDefinition(
                name="loss",
                data_type="BOOLEAN",
                description="Loss (L) - did pitcher get the loss (TRUE/FALSE)",
                examples=[False, True],
                nullable=True
            ),
            "save": ColumnDefinition(
                name="save",
                data_type="BOOLEAN",
                description="Save (SV) - did pitcher get the save (TRUE/FALSE)",
                examples=[True, False],
                nullable=True
            ),
            "era": ColumnDefinition(
                name="era",
                data_type="DECIMAL(5,2)",
                description="Earned run average (ERA) - calculated as (earned_runs * 9) / innings_pitched, lower is better",
                examples=["3.50", "2.75", "4.20"],
                nullable=True,
                calculated=True,
                formula="(earned_runs * 9) / innings_pitched"
            ),
            "whip": ColumnDefinition(
                name="whip",
                data_type="DECIMAL(4,2)",
                description="Walks + Hits per Inning Pitched (WHIP) - calculated as (walks_allowed + hits_allowed) / innings_pitched, lower is better",
                examples=["1.20", "1.00", "1.50"],
                nullable=True,
                calculated=True,
                formula="(walks_allowed + hits_allowed) / innings_pitched"
            ),
        },
        relationships={
            "game_id": "games",
            "player_id": "players",
            "team_id": "teams"
        },
        common_queries=[
            "Season totals: GROUP BY player_id, season",
            "Career totals: GROUP BY player_id",
            "Wins: WHERE win = TRUE",
            "Lowest ERA: ORDER BY AVG(era) ASC"
        ],
        notes="Always join with players table to get pitcher names. Use SUM() for counting wins/losses (convert boolean to integer)."
    ),
    
    "fielding_stats": TableDefinition(
        name="fielding_stats",
        description="Fielding statistics per game for each player at each position",
        primary_key="id",
        columns={
            "game_id": ColumnDefinition(
                name="game_id",
                data_type="VARCHAR(20)",
                description="Game identifier",
                nullable=True,
                foreign_key="games.game_id"
            ),
            "player_id": ColumnDefinition(
                name="player_id",
                data_type="VARCHAR(10)",
                description="Player identifier",
                nullable=True,
                foreign_key="players.player_id"
            ),
            "position": ColumnDefinition(
                name="position",
                data_type="INTEGER",
                description="Fielding position: 1=P, 2=C, 3=1B, 4=2B, 5=3B, 6=SS, 7=LF, 8=CF, 9=RF",
                examples=[1, 2, 3, 4, 5, 6, 7, 8, 9],
                nullable=True
            ),
            "putouts": ColumnDefinition(
                name="putouts",
                data_type="INTEGER",
                description="Putouts (PO) - defensive outs recorded",
                examples=[5, 3, 2],
                nullable=True
            ),
            "assists": ColumnDefinition(
                name="assists",
                data_type="INTEGER",
                description="Assists (A) - defensive assists",
                examples=[2, 1, 0],
                nullable=True
            ),
            "errors": ColumnDefinition(
                name="errors",
                data_type="INTEGER",
                description="Errors (E) - fielding errors committed",
                examples=[0, 1, 2],
                nullable=True
            ),
        },
        relationships={
            "game_id": "games",
            "player_id": "players"
        }
    ),
    
    "rosters": TableDefinition(
        name="rosters",
        description="Player-team-season roster relationships",
        primary_key="id",
        columns={
            "player_id": ColumnDefinition(
                name="player_id",
                data_type="VARCHAR(10)",
                description="Player identifier",
                nullable=True,
                foreign_key="players.player_id"
            ),
            "team_id": ColumnDefinition(
                name="team_id",
                data_type="VARCHAR(5)",
                description="Team identifier",
                nullable=True,
                foreign_key="teams.team_id"
            ),
            "season": ColumnDefinition(
                name="season",
                data_type="INTEGER",
                description="Year/season",
                examples=[2020],
                nullable=False
            ),
            "position": ColumnDefinition(
                name="position",
                data_type="VARCHAR(10)",
                description="Primary position",
                examples=["OF", "P", "C", "1B"],
                nullable=True
            ),
        },
        relationships={
            "player_id": "players",
            "team_id": "teams"
        }
    ),
    
    "player_seasons": TableDefinition(
        name="player_seasons",
        description="Aggregated player statistics by season - pre-computed season totals",
        primary_key="id",
        columns={
            "player_id": ColumnDefinition(
                name="player_id",
                data_type="VARCHAR(10)",
                description="Player identifier",
                nullable=True,
                foreign_key="players.player_id"
            ),
            "season": ColumnDefinition(
                name="season",
                data_type="INTEGER",
                description="Year/season",
                examples=[2020],
                nullable=False
            ),
            "team_id": ColumnDefinition(
                name="team_id",
                data_type="VARCHAR(5)",
                description="Team identifier",
                nullable=True,
                foreign_key="teams.team_id"
            ),
            "games": ColumnDefinition(
                name="games",
                data_type="INTEGER",
                description="Games played in season",
                examples=[150, 162],
                nullable=True
            ),
        },
        relationships={
            "player_id": "players",
            "team_id": "teams"
        },
        notes="Use this table for faster season-level queries instead of aggregating batting_stats/pitching_stats"
    ),
    
    "team_game_stats": TableDefinition(
        name="team_game_stats",
        description="Team-level statistics per game - aggregated team stats",
        primary_key="id",
        columns={
            "game_id": ColumnDefinition(
                name="game_id",
                data_type="VARCHAR(20)",
                description="Game identifier",
                nullable=True,
                foreign_key="games.game_id"
            ),
            "team_id": ColumnDefinition(
                name="team_id",
                data_type="VARCHAR(5)",
                description="Team identifier",
                nullable=True,
                foreign_key="teams.team_id"
            ),
            "season": ColumnDefinition(
                name="season",
                data_type="INTEGER",
                description="Year/season",
                examples=[2020],
                nullable=True
            ),
            "team_hr": ColumnDefinition(
                name="team_hr",
                data_type="INTEGER",
                description="Team home runs in game",
                examples=[3, 2, 5],
                nullable=True
            ),
            "team_r": ColumnDefinition(
                name="team_r",
                data_type="INTEGER",
                description="Team runs scored in game",
                examples=[5, 7, 3],
                nullable=True
            ),
        },
        relationships={
            "game_id": "games",
            "team_id": "teams"
        }
    ),
}


# Terminology mapping - common baseball terms to database columns
TERMINOLOGY_MAP = {
    # Batting terms
    "home run": "home_runs",
    "home runs": "home_runs",
    "hr": "home_runs",
    "hrs": "home_runs",
    "homer": "home_runs",
    "homers": "home_runs",
    "homerun": "home_runs",
    "homeruns": "home_runs",
    
    "rbi": "rbis",
    "rbis": "rbis",
    "runs batted in": "rbis",
    "run batted in": "rbis",
    
    "runs": "runs",
    "r": "runs",
    
    "hits": "hits",
    "h": "hits",
    "hit": "hits",
    
    "at bats": "at_bats",
    "at-bats": "at_bats",
    "ab": "at_bats",
    "abs": "at_bats",
    
    "batting average": "batting_average",
    "avg": "batting_average",
    "average": "batting_average",
    "ba": "batting_average",
    
    "on base percentage": "on_base_percentage",
    "obp": "on_base_percentage",
    "on-base percentage": "on_base_percentage",
    
    "slugging percentage": "slugging_percentage",
    "slg": "slugging_percentage",
    "slugging": "slugging_percentage",
    
    "ops": "ops",
    "on-base plus slugging": "ops",
    
    "strikeout": "strikeouts",
    "strikeouts": "strikeouts",
    "k": "strikeouts",
    "ks": "strikeouts",
    "so": "strikeouts",
    
    "walk": "walks",
    "walks": "walks",
    "bb": "walks",
    "base on balls": "walks",
    
    # Pitching terms
    "era": "era",
    "earned run average": "era",
    
    "whip": "whip",
    "walks plus hits per inning": "whip",
    
    "innings pitched": "innings_pitched",
    "ip": "innings_pitched",
    "innings": "innings_pitched",
    
    "strikeouts (pitcher)": "strikeouts",
    "k (pitcher)": "strikeouts",
    
    "wins": "win",
    "win": "win",
    "w": "win",
    
    "losses": "loss",
    "loss": "loss",
    "l": "loss",
    
    "saves": "save",
    "save": "save",
    "sv": "save",
    
    # Position numbers
    "pitcher": 1,
    "catcher": 2,
    "first base": 3,
    "first baseman": 3,
    "1b": 3,
    "second base": 4,
    "second baseman": 4,
    "2b": 4,
    "third base": 5,
    "third baseman": 5,
    "3b": 5,
    "shortstop": 6,
    "ss": 6,
    "left field": 7,
    "left fielder": 7,
    "lf": 7,
    "center field": 8,
    "center fielder": 8,
    "cf": 8,
    "right field": 9,
    "right fielder": 9,
    "rf": 9,
}


def get_table_info(table_name: str) -> str:
    """Get formatted information about a table for the agent"""
    if table_name not in DATA_DICTIONARY:
        return f"Table '{table_name}' not found in data dictionary"
    
    table = DATA_DICTIONARY[table_name]
    info = f"Table: {table.name}\n"
    info += f"Description: {table.description}\n"
    info += f"Primary Key: {table.primary_key}\n\n"
    info += "Columns:\n"
    
    for col_name, col_def in table.columns.items():
        info += f"  - {col_name} ({col_def.data_type}): {col_def.description}"
        if col_def.examples:
            info += f" Examples: {', '.join(map(str, col_def.examples))}"
        if col_def.foreign_key:
            info += f" [References: {col_def.foreign_key}]"
        if col_def.calculated:
            info += f" [Calculated: {col_def.formula}]"
        info += "\n"
    
    if table.relationships:
        info += "\nRelationships:\n"
        for col, foreign_table in table.relationships.items():
            info += f"  - {col} -> {foreign_table}\n"
    
    if table.common_queries:
        info += "\nCommon Query Patterns:\n"
        for query in table.common_queries:
            info += f"  - {query}\n"
    
    return info


def get_full_dictionary_text() -> str:
    """Get the full data dictionary as formatted text for agent prompts"""
    text = "BASEBALL STATISTICS DATABASE - DATA DICTIONARY\n"
    text += "=" * 60 + "\n\n"
    
    for table_name, table_def in DATA_DICTIONARY.items():
        text += get_table_info(table_name)
        text += "\n" + "-" * 60 + "\n\n"
    
    text += "\nTERMINOLOGY MAPPING:\n"
    text += "Common baseball terms mapped to database columns:\n"
    for term, column in TERMINOLOGY_MAP.items():
        text += f"  '{term}' -> {column}\n"
    
    return text


def get_table_summary() -> Dict[str, str]:
    """Get a quick summary of all tables"""
    return {
        name: table.description
        for name, table in DATA_DICTIONARY.items()
    }
