-- Simple script to extract and load teams from gameinfo.csv
-- Run this after loading games, or run separately

-- Extract teams from gameinfo
CREATE TEMP TABLE temp_team_extract (
    team_id VARCHAR(5)
);

-- Insert home teams
INSERT INTO temp_team_extract
SELECT DISTINCT hometeam
FROM (
    SELECT hometeam FROM games WHERE hometeam IS NOT NULL AND hometeam != ''
    UNION
    SELECT visteam FROM games WHERE visteam IS NOT NULL AND visteam != ''
) t;

-- Insert into teams table
INSERT INTO teams (team_id, league, city, name)
SELECT DISTINCT team_id, NULL, NULL, team_id
FROM temp_team_extract
WHERE team_id IS NOT NULL AND team_id != ''
ON CONFLICT (team_id) DO NOTHING;

DROP TABLE temp_team_extract;

