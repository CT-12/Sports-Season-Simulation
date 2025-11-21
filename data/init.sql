-- ==========================================
-- 1. CORE ENTITIES (Multi-Season Support)
-- ==========================================

-- Table: Teams
-- Primary Key is (team_id, season) to handle multiple years.
CREATE TABLE IF NOT EXISTS Teams (
    team_id INTEGER,
    season INTEGER,
    team_name VARCHAR(100),
    
    PRIMARY KEY (team_id, season)
);

-- Table: Players
-- Links to Teams via (current_team_id, season).
CREATE TABLE IF NOT EXISTS Players (
    player_id INTEGER,
    season INTEGER,
    player_name VARCHAR(100),
    current_team_id INTEGER,
    
    -- Position Info
    position_code VARCHAR(10),
    position_name VARCHAR(50),
    position_type VARCHAR(50),
    
    PRIMARY KEY (player_id, season),
    FOREIGN KEY (current_team_id, season) REFERENCES Teams(team_id, season)
);

-- ==========================================
-- 2. PLAYER STATISTICS (Restricted Columns)
-- ==========================================

-- Table: Player_Hitting_Stats
-- Metrics: AB, R, H, HR, RBI, AVG, OBP, SLG, OPS
CREATE TABLE IF NOT EXISTS Player_Hitting_Stats (
    id SERIAL PRIMARY KEY,
    player_id INTEGER,
    season INTEGER,
    
    ab INTEGER,           -- At Bats
    r INTEGER,            -- Runs
    h INTEGER,            -- Hits
    hr INTEGER,           -- Home Runs
    rbi INTEGER,          -- Runs Batted In
    avg DECIMAL(5,3),     -- Batting Average
    obp DECIMAL(5,3),     -- On-Base Percentage
    slg DECIMAL(5,3),     -- Slugging Percentage
    ops DECIMAL(5,3),     -- On-Base Plus Slugging
    
    FOREIGN KEY (player_id, season) REFERENCES Players(player_id, season)
);

-- Table: Player_Pitching_Stats
-- Metrics: W, L, ERA, IP, H, R, ER, BB, SO, WHIP, AVG
CREATE TABLE IF NOT EXISTS Player_Pitching_Stats (
    id SERIAL PRIMARY KEY,
    player_id INTEGER,
    season INTEGER,
    
    w INTEGER,            -- Wins
    l INTEGER,            -- Losses
    era DECIMAL(10,2),    -- Earned Run Average
    ip DECIMAL(10,1),     -- Innings Pitched
    h INTEGER,            -- Hits Allowed
    r INTEGER,            -- Runs Allowed
    er INTEGER,           -- Earned Runs
    bb INTEGER,           -- Walks (Base on Balls)
    so INTEGER,           -- Strikeouts
    whip DECIMAL(10,2),   -- Walks + Hits per Inning Pitched
    avg DECIMAL(5,3),     -- Opponent Batting Average
    
    FOREIGN KEY (player_id, season) REFERENCES Players(player_id, season)
);

-- ==========================================
-- 3. TEAM STATISTICS (Restricted Columns)
-- ==========================================

-- Table: Team_Hitting_Stats
CREATE TABLE IF NOT EXISTS Team_Hitting_Stats (
    id SERIAL PRIMARY KEY,
    team_id INTEGER,
    season INTEGER,
    
    ab INTEGER,
    r INTEGER,
    h INTEGER,
    hr INTEGER,
    rbi INTEGER,
    avg DECIMAL(5,3),
    obp DECIMAL(5,3),
    slg DECIMAL(5,3),
    ops DECIMAL(5,3),
    
    FOREIGN KEY (team_id, season) REFERENCES Teams(team_id, season)
);

-- Table: Team_Pitching_Stats
CREATE TABLE IF NOT EXISTS Team_Pitching_Stats (
    id SERIAL PRIMARY KEY,
    team_id INTEGER,
    season INTEGER,
    
    w INTEGER,
    l INTEGER,
    era DECIMAL(10,2),
    ip DECIMAL(10,1),
    h INTEGER,
    r INTEGER,
    er INTEGER,
    bb INTEGER,
    so INTEGER,
    whip DECIMAL(10,2),
    avg DECIMAL(5,3),
    
    FOREIGN KEY (team_id, season) REFERENCES Teams(team_id, season)
);

-- 1. Table for Game-by-Game Results
CREATE TABLE IF NOT EXISTS Team_Game_Logs (
    team_id INT,
    season INT,
    game_id INT,
    game_date DATE,
    game_type VARCHAR(10),
    opponent_id INT,
    opponent_name VARCHAR(100),
    home_away VARCHAR(10),
    team_score INT,
    opponent_score INT,
    result VARCHAR(5),
    score_diff INT,
    -- Composite Primary Key: Allows the same game_id to exist for both teams involved
    PRIMARY KEY (team_id, game_id) 
);

-- 2. Table for Head-to-Head (VS) Records
CREATE TABLE IF NOT EXISTS Team_VS_Records (
    team_id INT,
    season INT,
    opponent_id INT,
    opponent_name VARCHAR(100),
    game_type VARCHAR(10), -- 'R' for Regular, 'S' for Spring, etc.
    wins INT,
    losses INT,
    PRIMARY KEY (team_id, season, opponent_id, game_type)
);