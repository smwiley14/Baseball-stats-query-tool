"""
Few-shot examples for NL2SQL agent tuning.
These examples help the agent understand common query patterns.
"""

FEW_SHOT_EXAMPLES = [
    {
        "question": "Who hit the most home runs in 2020?",
        "sql": """
        SELECT 
            p.first_name,
            p.last_name,
            SUM(bs.home_runs) as total_home_runs
        FROM batting_stats bs
        JOIN players p ON bs.player_id = p.player_id
        WHERE bs.season = 2020
        GROUP BY p.player_id, p.first_name, p.last_name
        ORDER BY total_home_runs DESC
        LIMIT 10;
        """,
        "explanation": "Aggregate home runs by player for the 2020 season, join with players table for names"
    },
    {
        "question": "What was the highest batting average in a single season?",
        "sql": """
        SELECT 
            p.first_name,
            p.last_name,
            bs.season,
            ROUND(SUM(bs.hits)::DECIMAL / NULLIF(SUM(bs.at_bats), 0), 3) as batting_avg
        FROM batting_stats bs
        JOIN players p ON bs.player_id = p.player_id
        WHERE bs.at_bats > 0
        GROUP BY p.player_id, p.first_name, p.last_name, bs.season
        HAVING SUM(bs.at_bats) >= 502
        ORDER BY batting_avg DESC
        LIMIT 10;
        """,
        "explanation": "Calculate batting average (hits/at_bats) per season, filter for qualified players (502+ AB)"
    },
    {
        "question": "Who had the most strikeouts as a pitcher in 2020?",
        "sql": """
        SELECT 
            p.first_name,
            p.last_name,
            SUM(ps.strikeouts) as total_strikeouts
        FROM pitching_stats ps
        JOIN players p ON ps.player_id = p.player_id
        WHERE ps.season = 2020
        GROUP BY p.player_id, p.first_name, p.last_name
        ORDER BY total_strikeouts DESC
        LIMIT 10;
        """,
        "explanation": "Sum strikeouts from pitching_stats, join with players for names"
    },
    {
        "question": "What was the average ERA for all pitchers in 2020?",
        "sql": """
        SELECT 
            ROUND(AVG(ps.era), 2) as avg_era
        FROM pitching_stats ps
        WHERE ps.season = 2020 
          AND ps.innings_pitched > 0
          AND ps.era IS NOT NULL;
        """,
        "explanation": "Calculate average ERA, filter for pitchers who actually pitched"
    },
    {
        "question": "Who had the most hits in a 10-game span?",
        "sql": """
        WITH rolling_hits AS (
            SELECT 
                bs.player_id,
                bs.game_date,
                SUM(bs.hits) OVER (
                    PARTITION BY bs.player_id 
                    ORDER BY bs.game_date 
                    ROWS BETWEEN 9 PRECEDING AND CURRENT ROW
                ) as hits_10_game,
                ROW_NUMBER() OVER (
                    PARTITION BY bs.player_id 
                    ORDER BY bs.game_date
                ) as game_num
            FROM batting_stats bs
            WHERE bs.game_date IS NOT NULL
        )
        SELECT 
            p.first_name,
            p.last_name,
            rh.season,
            rh.game_date,
            rh.hits_10_game
        FROM rolling_hits rh
        JOIN batting_stats bs ON rh.player_id = bs.player_id AND rh.game_date = bs.game_date
        JOIN players p ON rh.player_id = p.player_id
        WHERE rh.game_num >= 10
        ORDER BY rh.hits_10_game DESC
        LIMIT 10;
        """,
        "explanation": "Use window function to calculate rolling 10-game totals, filter for complete spans"
    },
    {
        "question": "How many games did each team win in 2020?",
        "sql": """
        SELECT 
            t.team_id,
            t.city,
            t.name,
            COUNT(*) as wins
        FROM games g
        JOIN teams t ON g.home_team_id = t.team_id
        WHERE g.season = 2020 
          AND g.home_score > g.away_score
        GROUP BY t.team_id, t.city, t.name
        ORDER BY wins DESC;
        """,
        "explanation": "Count games where home team scored more than away team"
    },
    {
        "question": "What players had the most RBIs in a single game?",
        "sql": """
        SELECT 
            p.first_name,
            p.last_name,
            bs.game_date,
            bs.season,
            bs.rbis
        FROM batting_stats bs
        JOIN players p ON bs.player_id = p.player_id
        WHERE bs.rbis > 0
        ORDER BY bs.rbis DESC
        LIMIT 10;
        """,
        "explanation": "Query individual game stats, order by RBIs descending"
    },
    {
        "question": "What was Mike Trout's batting average in 2020?",
        "sql": """
        SELECT 
            p.first_name,
            p.last_name,
            bs.season,
            ROUND(SUM(bs.hits)::DECIMAL / NULLIF(SUM(bs.at_bats), 0), 3) as batting_avg,
            SUM(bs.at_bats) as total_at_bats
        FROM batting_stats bs
        JOIN players p ON bs.player_id = p.player_id
        WHERE LOWER(p.last_name) = 'trout'
          AND LOWER(p.first_name) = 'mike'
          AND bs.season = 2020
        GROUP BY p.player_id, p.first_name, p.last_name, bs.season;
        """,
        "explanation": "Filter by player name (case-insensitive) and season, calculate season batting average"
    }
]


def get_few_shot_prompt() -> str:
    """
    Format few-shot examples into a prompt string.
    """
    examples_text = "\n\n".join([
        f"Question: {ex['question']}\n"
        f"SQL Query:\n{ex['sql']}\n"
        f"Explanation: {ex['explanation']}"
        for ex in FEW_SHOT_EXAMPLES
    ])
    
    return f"""
Here are some example questions and their corresponding SQL queries:

{examples_text}

When answering questions, follow these patterns and adapt them to the specific question asked.
"""
