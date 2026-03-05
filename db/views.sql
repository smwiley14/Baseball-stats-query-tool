CREATE VIEW all_batting_seasons AS
    WITH team_games AS (
        SELECT
            season,
            team,
            COUNT(*) AS games
        FROM (
            SELECT season, home_team_id AS team
            FROM games
            WHERE LOWER(game_type) = 'regular'

            UNION ALL

            SELECT season, away_team_id AS team
            FROM games
            WHERE LOWER(game_type) = 'regular'
        ) g
        GROUP BY season, team
    ),

    season_team_games AS (
        SELECT
            season,
            MAX(games) AS team_games
        FROM team_games
        GROUP BY season
    ),

    player_season_stats AS (
        SELECT
            bs.player_id,
            bs.team_id,
            bs.season,
            MIN(g.game_date) AS game_date,

            SUM(bs.plate_appearances) AS plate_appearances,
            SUM(bs.at_bats) AS at_bats,
            SUM(bs.hits) AS hits,
            SUM(bs.singles) AS singles,
            SUM(bs.doubles) AS doubles,
            SUM(bs.triples) AS triples,
            SUM(bs.home_runs) AS home_runs,
            SUM(bs.runs) AS runs,
            SUM(bs.rbis) AS rbis,
            SUM(bs.walks) AS walks,
            SUM(bs.intentional_walks) AS intentional_walks,
            SUM(bs.strikeouts) AS strikeouts,
            SUM(bs.hit_by_pitch) AS hit_by_pitch,
            SUM(bs.sacrifice_hits) AS sacrifice_hits,
            SUM(bs.sacrifice_flies) AS sacrifice_flies,
            SUM(bs.stolen_bases) AS stolen_bases,
            SUM(bs.caught_stealing) AS caught_stealing,
            SUM(bs.grounded_into_double_play) AS grounded_into_double_play,
            SUM(bs.reached_on_error) AS reached_on_error

        FROM batting_stats bs
        JOIN games g
            ON bs.game_id = g.game_id
        JOIN teams th
            ON g.home_team_id = th.team_id
        JOIN teams ta
            ON g.away_team_id = ta.team_id

        WHERE LOWER(g.game_type) = 'regular'
        AND th.league IN ('AL','NL')
        AND ta.league IN ('AL','NL')

        GROUP BY
            bs.player_id,
            bs.team_id,
            bs.season
    )

    SELECT
        ps.*,

        ROUND(
            ps.hits::DECIMAL / NULLIF(ps.at_bats,0),
            3
        ) AS batting_average,

        ROUND(
            (ps.hits + ps.walks + ps.hit_by_pitch)::DECIMAL /
            NULLIF(ps.at_bats + ps.walks + ps.hit_by_pitch + ps.sacrifice_flies,0),
            3
        ) AS on_base_percentage,

        ROUND(
            (ps.singles + 2*ps.doubles + 3*ps.triples + 4*ps.home_runs)::DECIMAL /
            NULLIF(ps.at_bats,0),
            3
        ) AS slugging_percentage,

        ROUND(
            (
                (ps.hits + ps.walks + ps.hit_by_pitch)::DECIMAL /
                NULLIF(ps.at_bats + ps.walks + ps.hit_by_pitch + ps.sacrifice_flies,0)
            )
            +
            (
                (ps.singles + 2*ps.doubles + 3*ps.triples + 4*ps.home_runs)::DECIMAL /
                NULLIF(ps.at_bats,0)
            ),
            3
        ) AS ops

    FROM player_season_stats ps
    JOIN season_team_games sg
        ON ps.season = sg.season;

-------------------------------------------------------

CREATE OR REPLACE VIEW all_pitching_seasons AS
    WITH season_games AS (
        SELECT 
            season,
            COUNT(DISTINCT game_id) / COUNT(DISTINCT home_team_id) AS team_games
        FROM games
        WHERE LOWER(game_type) = 'regular'
        GROUP BY season
    )

    SELECT
        ps.player_id,
        ps.team_id,
        ps.season,

        MIN(ps.game_date) AS first_game,
        MAX(ps.game_date) AS last_game,

        SUM(ps.outs_pitched) AS outs_pitched,
        ROUND(SUM(ps.outs_pitched) / 3.0, 1) AS innings_pitched,

        SUM(ps.batters_faced) AS batters_faced,
        SUM(ps.hits_allowed) AS hits_allowed,
        SUM(ps.doubles_allowed) AS doubles_allowed,
        SUM(ps.triples_allowed) AS triples_allowed,
        SUM(ps.home_runs_allowed) AS home_runs_allowed,
        SUM(ps.runs_allowed) AS runs_allowed,
        SUM(ps.earned_runs) AS earned_runs,
        SUM(ps.walks_allowed) AS walks_allowed,
        SUM(ps.intentional_walks) AS intentional_walks,
        SUM(ps.strikeouts) AS strikeouts,
        SUM(ps.hit_batters) AS hit_batters,

        SUM(ps.wild_pitches) AS wild_pitches,
        SUM(ps.balks) AS balks,

        SUM(ps.sacrifice_hits_allowed) AS sacrifice_hits_allowed,
        SUM(ps.sacrifice_flies_allowed) AS sacrifice_flies_allowed,

        SUM(ps.stolen_bases_allowed) AS stolen_bases_allowed,
        SUM(ps.caught_stealing) AS caught_stealing,

        SUM(ps.passed_balls) AS passed_balls,

        SUM(CASE WHEN ps.win THEN 1 ELSE 0 END) AS wins,
        SUM(CASE WHEN ps.loss THEN 1 ELSE 0 END) AS losses,
        SUM(CASE WHEN ps.save THEN 1 ELSE 0 END) AS saves,

        SUM(CASE WHEN ps.game_started THEN 1 ELSE 0 END) AS games_started,
        SUM(CASE WHEN ps.complete_game THEN 1 ELSE 0 END) AS complete_games,

        -- ERA
        ROUND(
            (SUM(ps.earned_runs) * 9.0) /
            NULLIF(SUM(ps.outs_pitched) / 3.0, 0),
            2
        ) AS era,

        -- WHIP
        ROUND(
            (SUM(ps.walks_allowed) + SUM(ps.hits_allowed))::decimal /
            NULLIF(SUM(ps.outs_pitched) / 3.0, 0),
            3
        ) AS whip,

        -- Opponent Batting Average
        ROUND(
            SUM(ps.hits_allowed)::decimal /
            NULLIF(
                SUM(ps.batters_faced)
                - SUM(ps.walks_allowed)
                - SUM(ps.hit_batters)
                - SUM(ps.sacrifice_hits_allowed)
                - SUM(ps.sacrifice_flies_allowed),
            0),
            3
        ) AS opponent_batting_avg,

        -- K/9
        ROUND(
            (SUM(ps.strikeouts) * 9.0) /
            NULLIF(SUM(ps.outs_pitched) / 3.0, 0),
            2
        ) AS k_per_9,

        -- BB/9
        ROUND(
            (SUM(ps.walks_allowed) * 9.0) /
            NULLIF(SUM(ps.outs_pitched) / 3.0, 0),
            2
        ) AS bb_per_9

    FROM pitching_stats ps
    JOIN games g ON ps.game_id = g.game_id
    JOIN teams t ON g.home_team_id = t.team_id
    JOIN season_games sg ON sg.season = ps.season

    WHERE
        LOWER(g.game_type) = 'regular'
        AND t.league IN ('AL', 'NL')

    GROUP BY
        ps.player_id,
        ps.team_id,
        ps.season,
        sg.team_games;

-------------------------------------------------------

CREATE VIEW qualified_batting_seasons AS
    WITH team_games AS (
        SELECT
            season,
            team,
            COUNT(*) AS games
        FROM (
            SELECT season, home_team_id AS team
            FROM games
            WHERE LOWER(game_type) = 'regular'

            UNION ALL

            SELECT season, away_team_id AS team
            FROM games
            WHERE LOWER(game_type) = 'regular'
        ) g
        GROUP BY season, team
    ),

    season_team_games AS (
        SELECT
            season,
            MAX(games) AS team_games
        FROM team_games
        GROUP BY season
    ),

    player_season_stats AS (
        SELECT
            bs.player_id,
            bs.team_id,
            bs.season,
            MIN(g.game_date) AS game_date,

            SUM(bs.plate_appearances) AS plate_appearances,
            SUM(bs.at_bats) AS at_bats,
            SUM(bs.hits) AS hits,
            SUM(bs.singles) AS singles,
            SUM(bs.doubles) AS doubles,
            SUM(bs.triples) AS triples,
            SUM(bs.home_runs) AS home_runs,
            SUM(bs.runs) AS runs,
            SUM(bs.rbis) AS rbis,
            SUM(bs.walks) AS walks,
            SUM(bs.intentional_walks) AS intentional_walks,
            SUM(bs.strikeouts) AS strikeouts,
            SUM(bs.hit_by_pitch) AS hit_by_pitch,
            SUM(bs.sacrifice_hits) AS sacrifice_hits,
            SUM(bs.sacrifice_flies) AS sacrifice_flies,
            SUM(bs.stolen_bases) AS stolen_bases,
            SUM(bs.caught_stealing) AS caught_stealing,
            SUM(bs.grounded_into_double_play) AS grounded_into_double_play,
            SUM(bs.reached_on_error) AS reached_on_error

        FROM batting_stats bs
        JOIN games g
            ON bs.game_id = g.game_id
        JOIN teams th
            ON g.home_team_id = th.team_id
        JOIN teams ta
            ON g.away_team_id = ta.team_id

        WHERE LOWER(g.game_type) = 'regular'
        AND th.league IN ('AL','NL')
        AND ta.league IN ('AL','NL')

        GROUP BY
            bs.player_id,
            bs.team_id,
            bs.season
    )

    SELECT
        ps.*,

        ROUND(
            ps.hits::DECIMAL / NULLIF(ps.at_bats,0),
            3
        ) AS batting_average,

        ROUND(
            (ps.hits + ps.walks + ps.hit_by_pitch)::DECIMAL /
            NULLIF(ps.at_bats + ps.walks + ps.hit_by_pitch + ps.sacrifice_flies,0),
            3
        ) AS on_base_percentage,

        ROUND(
            (ps.singles + 2*ps.doubles + 3*ps.triples + 4*ps.home_runs)::DECIMAL /
            NULLIF(ps.at_bats,0),
            3
        ) AS slugging_percentage,

        ROUND(
            (
                (ps.hits + ps.walks + ps.hit_by_pitch)::DECIMAL /
                NULLIF(ps.at_bats + ps.walks + ps.hit_by_pitch + ps.sacrifice_flies,0)
            )
            +
            (
                (ps.singles + 2*ps.doubles + 3*ps.triples + 4*ps.home_runs)::DECIMAL /
                NULLIF(ps.at_bats,0)
            ),
            3
        ) AS ops

    FROM player_season_stats ps
    JOIN season_team_games sg
        ON ps.season = sg.season
    WHERE
        ps.plate_appearances >= ROUND(3.1 * sg.team_games);

-------------------------------------------------------

CREATE OR REPLACE VIEW qualified_pitching_seasons AS

    WITH season_games AS (
        SELECT 
            season,
            COUNT(DISTINCT game_id) / COUNT(DISTINCT home_team_id) AS team_games
        FROM games
        WHERE LOWER(game_type) = 'regular'
        GROUP BY season
    )

    SELECT
        ps.player_id,
        ps.team_id,
        ps.season,

        MIN(ps.game_date) AS first_game,
        MAX(ps.game_date) AS last_game,

        SUM(ps.outs_pitched) AS outs_pitched,
        ROUND(SUM(ps.outs_pitched) / 3.0, 1) AS innings_pitched,

        SUM(ps.batters_faced) AS batters_faced,
        SUM(ps.hits_allowed) AS hits_allowed,
        SUM(ps.doubles_allowed) AS doubles_allowed,
        SUM(ps.triples_allowed) AS triples_allowed,
        SUM(ps.home_runs_allowed) AS home_runs_allowed,
        SUM(ps.runs_allowed) AS runs_allowed,
        SUM(ps.earned_runs) AS earned_runs,
        SUM(ps.walks_allowed) AS walks_allowed,
        SUM(ps.intentional_walks) AS intentional_walks,
        SUM(ps.strikeouts) AS strikeouts,
        SUM(ps.hit_batters) AS hit_batters,

        SUM(ps.wild_pitches) AS wild_pitches,
        SUM(ps.balks) AS balks,

        SUM(ps.sacrifice_hits_allowed) AS sacrifice_hits_allowed,
        SUM(ps.sacrifice_flies_allowed) AS sacrifice_flies_allowed,

        SUM(ps.stolen_bases_allowed) AS stolen_bases_allowed,
        SUM(ps.caught_stealing) AS caught_stealing,

        SUM(ps.passed_balls) AS passed_balls,

        SUM(CASE WHEN ps.win THEN 1 ELSE 0 END) AS wins,
        SUM(CASE WHEN ps.loss THEN 1 ELSE 0 END) AS losses,
        SUM(CASE WHEN ps.save THEN 1 ELSE 0 END) AS saves,

        SUM(CASE WHEN ps.game_started THEN 1 ELSE 0 END) AS games_started,
        SUM(CASE WHEN ps.complete_game THEN 1 ELSE 0 END) AS complete_games,

        -- ERA
        ROUND(
            (SUM(ps.earned_runs) * 9.0) /
            NULLIF(SUM(ps.outs_pitched) / 3.0, 0),
            2
        ) AS era,

        -- WHIP
        ROUND(
            (SUM(ps.walks_allowed) + SUM(ps.hits_allowed))::decimal /
            NULLIF(SUM(ps.outs_pitched) / 3.0, 0),
            3
        ) AS whip,

        -- Opponent Batting Average
        ROUND(
            SUM(ps.hits_allowed)::decimal /
            NULLIF(
                SUM(ps.batters_faced)
                - SUM(ps.walks_allowed)
                - SUM(ps.hit_batters)
                - SUM(ps.sacrifice_hits_allowed)
                - SUM(ps.sacrifice_flies_allowed),
            0),
            3
        ) AS opponent_batting_avg,

        -- K/9
        ROUND(
            (SUM(ps.strikeouts) * 9.0) /
            NULLIF(SUM(ps.outs_pitched) / 3.0, 0),
            2
        ) AS k_per_9,

        -- BB/9
        ROUND(
            (SUM(ps.walks_allowed) * 9.0) /
            NULLIF(SUM(ps.outs_pitched) / 3.0, 0),
            2
        ) AS bb_per_9

    FROM pitching_stats ps
    JOIN games g ON ps.game_id = g.game_id
    JOIN teams t ON g.home_team_id = t.team_id
    JOIN season_games sg ON sg.season = ps.season

    WHERE
        LOWER(g.game_type) = 'regular'
        AND t.league IN ('AL', 'NL')

    GROUP BY
        ps.player_id,
        ps.team_id,
        ps.season,
        sg.team_games

    HAVING
        -- MLB qualification rule
        SUM(ps.outs_pitched) >= 3 * sg.team_games;

-------------------------------------------------------

CREATE OR REPLACE VIEW team_season_stats AS

    WITH batting AS (
        SELECT
            team_id,
            season,

            SUM(plate_appearances) AS plate_appearances,
            SUM(at_bats) AS at_bats,
            SUM(hits) AS hits,
            SUM(singles) AS singles,
            SUM(doubles) AS doubles,
            SUM(triples) AS triples,
            SUM(home_runs) AS home_runs,
            SUM(runs) AS runs,
            SUM(rbis) AS rbis,
            SUM(walks) AS walks,
            SUM(strikeouts) AS strikeouts,
            SUM(hit_by_pitch) AS hit_by_pitch,
            SUM(sacrifice_flies) AS sacrifice_flies,
            SUM(stolen_bases) AS stolen_bases,
            SUM(caught_stealing) AS caught_stealing
        FROM batting_stats
        GROUP BY team_id, season
    ),

    pitching AS (
        SELECT
            team_id,
            season,

            SUM(outs_pitched) AS outs_pitched,
            SUM(hits_allowed) AS hits_allowed,
            SUM(home_runs_allowed) AS home_runs_allowed,
            SUM(runs_allowed) AS runs_allowed,
            SUM(earned_runs) AS earned_runs,
            SUM(walks_allowed) AS walks_allowed,
            SUM(strikeouts) AS strikeouts_pitched
        FROM pitching_stats
        GROUP BY team_id, season
    )

    SELECT
        b.team_id,
        b.season,

        -- batting totals
        b.plate_appearances,
        b.at_bats,
        b.hits,
        b.singles,
        b.doubles,
        b.triples,
        b.home_runs,
        b.runs,
        b.rbis,
        b.walks,
        b.strikeouts,
        b.hit_by_pitch,
        b.sacrifice_flies,
        b.stolen_bases,
        b.caught_stealing,

        -- batting rate stats
        ROUND(b.hits::DECIMAL / NULLIF(b.at_bats,0),3) AS batting_average,

        ROUND(
            (b.hits + b.walks + b.hit_by_pitch)::DECIMAL /
            NULLIF(b.at_bats + b.walks + b.hit_by_pitch + b.sacrifice_flies,0),
        3) AS on_base_percentage,

        ROUND(
            (b.singles + 2*b.doubles + 3*b.triples + 4*b.home_runs)::DECIMAL /
            NULLIF(b.at_bats,0),
        3) AS slugging_percentage,

        ROUND(
            (b.hits + b.walks + b.hit_by_pitch)::DECIMAL /
            NULLIF(b.at_bats + b.walks + b.hit_by_pitch + b.sacrifice_flies,0)
            +
            (b.singles + 2*b.doubles + 3*b.triples + 4*b.home_runs)::DECIMAL /
            NULLIF(b.at_bats,0),
        3) AS ops,

        -- pitching totals
        ROUND(p.outs_pitched / 3.0,1) AS innings_pitched,
        p.hits_allowed,
        p.home_runs_allowed,
        p.runs_allowed,
        p.earned_runs,
        p.walks_allowed,
        p.strikeouts_pitched,

        -- pitching rate stats
        ROUND(
            (p.earned_runs * 9.0) /
            NULLIF(p.outs_pitched / 3.0,0),
        2) AS era,

        ROUND(
            (p.walks_allowed + p.hits_allowed)::DECIMAL /
            NULLIF(p.outs_pitched / 3.0,0),
        3) AS whip

    FROM batting b
    JOIN pitching p
        ON b.team_id = p.team_id
    AND b.season = p.season;

-------------------------------------------------------
