# Team Ranking API Documentation

## Overview

The Team Ranking endpoint ranks all MLB teams based on a user-selected combination of a **Hitter Metric** and a **Pitcher Metric**. The ranking uses Z-score normalization to account for different metric scales and directions, producing a combined score for each team.

## Key Features

✅ **Flexible Metric Selection** - Choose from any hitting or pitching metric
✅ **Z-Score Normalization** - Handles different scales and metric directions
✅ **League Separation** - Results split into AL (American League) and NL (National League)
✅ **Detailed Analytics** - Optional detailed view with component Z-scores
✅ **Automatic Season Detection** - Uses the latest available season by default

## API Endpoint

```
POST /api/ranking/
```

## Request Format

### Basic Request
```json
{
  "hitter_metric": "ops",
  "pitcher_metric": "era"
}
```

### Request with Optional Parameters
```json
{
  "hitter_metric": "avg",
  "pitcher_metric": "whip",
  "season": 2025,
  "details": false
}
```

### Request Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `hitter_metric` | string | ✓ | - | Hitting metric to rank by |
| `pitcher_metric` | string | ✓ | - | Pitching metric to rank by |
| `season` | integer | ✗ | latest | Season year (e.g., 2025) |
| `details` | boolean | ✗ | false | Include detailed Z-score breakdown |

### Available Metrics

**Hitting Metrics** (higher is better):
- `avg` - Batting Average
- `ops` - On-base Plus Slugging
- `hr` - Home Runs
- `rbi` - Runs Batted In
- `r` - Runs Scored
- `h` - Hits
- `obp` - On-Base Percentage
- `slg` - Slugging Percentage

**Pitching Metrics**:
- `era` - Earned Run Average (lower is better)
- `whip` - Walks + Hits per Innings Pitched (lower is better)
- `so` - Strikeouts (higher is better)
- `w` - Wins (higher is better)
- `l` - Losses (lower is better)
- `bb` - Walks (lower is better)

## Response Format

### Basic Response (details: false)
```json
{
  "AL": [
    ["New York Yankees", 2.145],
    ["Houston Astros", 1.892],
    ["Boston Red Sox", 1.234],
    ...
  ],
  "NL": [
    ["Los Angeles Dodgers", 2.567],
    ["San Diego Padres", 2.123],
    ...
  ]
}
```

### Detailed Response (details: true)
```json
{
  "season": 2025,
  "hitter_metric": "ops",
  "pitcher_metric": "era",
  "AL": [
    {
      "rank": 1,
      "team_name": "New York Yankees",
      "score": 2.145,
      "hitter_value": 0.820,
      "pitcher_value": 3.45,
      "hitter_z_score": 1.234,
      "pitcher_z_score": 0.911
    },
    {
      "rank": 2,
      "team_name": "Houston Astros",
      "score": 1.892,
      "hitter_value": 0.805,
      "pitcher_value": 3.62,
      "hitter_z_score": 0.945,
      "pitcher_z_score": 0.947
    }
  ],
  "NL": [...]
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `rank` | integer | Team's rank within their league |
| `team_name` | string | Official MLB team name |
| `score` | float | Combined Z-score (sum of hitter and pitcher Z-scores) |
| `hitter_value` | float | Team's average value for the hitter metric |
| `pitcher_value` | float | Team's average value for the pitcher metric |
| `hitter_z_score` | float | Normalized hitter metric Z-score |
| `pitcher_z_score` | float | Normalized pitcher metric Z-score |

## Algorithm Explanation

### Step 1: Data Aggregation
For each team, calculate the **average** value of the requested metrics across all players:
- For hitting stats: Filter to position players (not pitchers)
- For pitching stats: Filter to pitchers only

### Step 2: Calculate League Statistics
Compute the mean and standard deviation for each metric across all teams:
- `μ = mean(all_team_values)`
- `σ = std_dev(all_team_values)`

### Step 3: Normalize with Z-Scores
Convert each team's metrics to Z-scores:

```
Z = (value - mean) / std_dev
```

This produces a standardized score:
- **Z ≈ 0** : Team is league average
- **Z > 0** : Team is above average
- **Z < 0** : Team is below average

### Step 4: Adjust for Metric Direction
For metrics where "lower is better" (ERA, WHIP, losses), flip the Z-score sign:

```
if metric in ["era", "whip", "l", "bb"]:
    Z_adjusted = -Z
else:
    Z_adjusted = Z
```

This ensures:
- **Higher Z-scores always represent better performance**
- A team with low ERA (good) gets a positive Z-score

### Step 5: Combine Scores
Calculate the team's final score as the sum of both Z-scores:

```
Final_Score = Z_hitter + Z_pitcher
```

### Step 6: Rank and Split by League
1. Sort teams by `Final_Score` descending
2. Separate into AL and NL groups using the team name mapping
3. Assign rank within each league

## Example Usage

### Example 1: OPS vs ERA Ranking
```bash
curl -X POST http://localhost:8000/api/ranking/ \
  -H "Content-Type: application/json" \
  -d '{
    "hitter_metric": "ops",
    "pitcher_metric": "era",
    "details": false
  }'
```

**Interpretation**: Teams that have both strong offensive production (high OPS) and effective pitching (low ERA) will rank highest. The Z-score normalization ensures that both metrics contribute equally to the final score despite their different scales (OPS ≈ 0.6-0.9, ERA ≈ 3.0-5.0).

### Example 2: Power Hitting vs Strikeout Ranking
```bash
curl -X POST http://localhost:8000/api/ranking/ \
  -H "Content-Type: application/json" \
  -d '{
    "hitter_metric": "hr",
    "pitcher_metric": "so",
    "season": 2025,
    "details": true
  }'
```

**Interpretation**: This highlights teams with strong power and dominant pitchers. Both metrics favor high values, so there's no direction flip needed.

### Example 3: Contact Hitting vs Pitcher Efficiency
```bash
curl -X POST http://localhost:8000/api/ranking/ \
  -H "Content-Type: application/json" \
  -d '{
    "hitter_metric": "avg",
    "pitcher_metric": "whip",
    "details": true
  }'
```

**Interpretation**: Contact hitters (high AVG) paired with efficient pitchers (low WHIP). The WHIP metric will have its Z-score flipped to properly penalize teams with high values.

## Error Handling

### Invalid Metric
```json
{
  "error": "Unknown hitter metric: invalid_metric",
  "available_metrics": {
    "hitting": ["avg", "ops", "hr", "rbi", "r", "h", "obp", "slg"],
    "pitching": ["era", "whip", "so", "w", "l", "bb"]
  }
}
```
**HTTP Status**: 400 Bad Request

### Missing Required Parameters
```json
{
  "error": "Both hitter_metric and pitcher_metric are required",
  "available_metrics": {
    "hitting": ["avg", "ops", "hr", "rbi", "r", "h", "obp", "slg"],
    "pitching": ["era", "whip", "so", "w", "l", "bb"]
  }
}
```
**HTTP Status**: 400 Bad Request

### Database/Query Failures
```json
{
  "error": "Failed to rank teams: [specific error message]"
}
```
**HTTP Status**: 500 Internal Server Error

## Database Schema

The implementation assumes the following PostgreSQL schema:

```sql
-- Teams table
CREATE TABLE teams (
    team_id INTEGER PRIMARY KEY,
    season INTEGER,
    team_name VARCHAR(255),
    UNIQUE(team_id, season)
);

-- Players table
CREATE TABLE players (
    player_id INTEGER PRIMARY KEY,
    season INTEGER,
    current_team_id INTEGER,
    position_type VARCHAR(10),  -- 'P', 'C', 'SS', '2B', '3B', '1B', 'OF', 'DH'
    FOREIGN KEY (current_team_id) REFERENCES teams(team_id)
);

-- Hitting stats table
CREATE TABLE player_hitting_stats (
    player_id INTEGER,
    season INTEGER,
    avg DECIMAL(4,3),
    ops DECIMAL(4,3),
    hr INTEGER,
    rbi INTEGER,
    r INTEGER,
    h INTEGER,
    obp DECIMAL(4,3),
    slg DECIMAL(4,3),
    FOREIGN KEY (player_id) REFERENCES players(player_id)
);

-- Pitching stats table
CREATE TABLE player_pitching_stats (
    player_id INTEGER,
    season INTEGER,
    era DECIMAL(3,2),
    whip DECIMAL(3,2),
    so INTEGER,
    w INTEGER,
    l INTEGER,
    bb INTEGER,
    FOREIGN KEY (player_id) REFERENCES players(player_id)
);
```

## Implementation Details

### Code Structure

**Service Module**: `api/services/team_ranking.py`
- `rank_teams_by_metrics()` - Main ranking function (basic output)
- `get_ranking_with_details()` - Detailed ranking with Z-scores
- `aggregate_team_hitting_stats()` - Query and aggregate hitting stats
- `aggregate_team_pitching_stats()` - Query and aggregate pitching stats
- `calculate_z_score()` - Z-score normalization
- `normalize_z_score_by_direction()` - Adjust for metric direction

**View**: `api/views.py`
- `team_ranking()` - API endpoint handler

**URL**: `api/urls.py`
- Route: `POST /api/ranking/`

### Edge Cases Handled

1. **Missing Stats**: If a team has no hitting or pitching stats for a metric, it defaults to the league average
2. **Zero Variance**: If all teams have identical metric values, Z-scores become 0 (no differentiation)
3. **Null Values**: Database NULL values are filtered out during aggregation
4. **Unknown Teams**: Teams not in the TEAM_LEAGUE_MAP default to NL

## Testing

Run the test suite:

```bash
cd backend
python manage.py shell < api/tests/test_ranking.py
```

This will:
- ✓ Verify the latest season detection
- ✓ Test team league mapping
- ✓ Validate stat aggregation
- ✓ Check Z-score calculations
- ✓ Test basic ranking
- ✓ Test detailed ranking output
- ✓ Test alternative metric combinations

## Performance Considerations

- **Query Optimization**: Uses direct SQL with aggregation functions for efficiency
- **Caching**: Consider caching results if rankings are requested frequently
- **Database Indexes**: Recommended indexes:
  ```sql
  CREATE INDEX idx_players_team_season ON players(current_team_id, season);
  CREATE INDEX idx_hitting_stats_player ON player_hitting_stats(player_id);
  CREATE INDEX idx_pitching_stats_player ON player_pitching_stats(player_id);
  ```

## Future Enhancements

- Add caching layer for frequently requested rankings
- Support for custom date ranges (not just by season)
- Weighted metric combinations (e.g., 60% hitter, 40% pitcher)
- Historical rankings (track rankings over time)
- Confidence intervals based on sample size
- Export to CSV/PDF formats
