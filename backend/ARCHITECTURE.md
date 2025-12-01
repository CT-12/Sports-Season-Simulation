# Code Architecture & Design Overview

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        HTTP Request                              │
│   POST /api/ranking/ with JSON body                              │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
         ┌───────────────────────────────┐
         │   api/views.py                │
         │   team_ranking() endpoint     │
         │                               │
         │  - Validates input           │
         │  - Calls service layer       │
         │  - Returns JSON response     │
         └────────────┬──────────────────┘
                      │
                      ▼
         ┌───────────────────────────────┐
         │   api/services/               │
         │   team_ranking.py             │
         │                               │
         │  Main Functions:              │
         │  • rank_teams_by_metrics()   │
         │  • get_ranking_with_details()│
         │  • aggregate_team_*_stats()  │
         │  • calculate_z_score()       │
         │  • normalize_z_score_*()     │
         └────────────┬──────────────────┘
                      │
                      ▼
         ┌───────────────────────────────┐
         │   PostgreSQL Database         │
         │                               │
         │   ├─ teams table             │
         │   ├─ players table           │
         │   ├─ player_hitting_stats   │
         │   └─ player_pitching_stats  │
         └───────────────────────────────┘
```

## Module Dependencies

```
api/views.py
    └─→ api/services/team_ranking.py
            └─→ django.db.connection
            └─→ statistics (built-in)
            └─→ typing (built-in)
```

## Data Flow

### 1. Request Reception & Validation

```python
# api/views.py - team_ranking()
POST /api/ranking/ HTTP/1.1
{
  "hitter_metric": "ops",
  "pitcher_metric": "era",
  "season": 2025,
  "details": false
}
    ↓
# Validate required parameters
# Validate metric names
# Call service layer
```

### 2. Service Layer Processing

```python
# api/services/team_ranking.py

rank_teams_by_metrics()
    ├─ validate metrics
    ├─ get_latest_season() if needed
    ├─ aggregate_team_hitting_stats(metric)
    │   └─ SQL: SELECT team_name, AVG(metric) FROM...
    ├─ aggregate_team_pitching_stats(metric)
    │   └─ SQL: SELECT team_name, AVG(metric) FROM...
    ├─ Calculate league statistics
    │   ├─ mean(hitter_values)
    │   ├─ stdev(hitter_values)
    │   ├─ mean(pitcher_values)
    │   └─ stdev(pitcher_values)
    ├─ For each team:
    │   ├─ calculate_z_score(hitter_value, mean, std)
    │   ├─ calculate_z_score(pitcher_value, mean, std)
    │   ├─ normalize_z_score_by_direction(z, metric)
    │   └─ final_score = hitter_z + pitcher_z
    ├─ Sort teams by final_score
    └─ Split by league (AL/NL) using TEAM_LEAGUE_MAP
```

### 3. Response Generation

```python
# Basic Response
{
  "AL": [
    ["Team A", 2.345],
    ["Team B", 1.789],
    ...
  ],
  "NL": [
    ["Team C", 2.567],
    ...
  ]
}

# Detailed Response (with details=true)
{
  "season": 2025,
  "hitter_metric": "ops",
  "pitcher_metric": "era",
  "AL": [
    {
      "rank": 1,
      "team_name": "Team A",
      "score": 2.345,
      "hitter_value": 0.832,
      "pitcher_value": 3.42,
      "hitter_z_score": 1.234,
      "pitcher_z_score": 1.111
    },
    ...
  ],
  "NL": [...]
}
```

## Class & Function Definitions

### Core Functions

#### 1. `rank_teams_by_metrics(hitter_metric, pitcher_metric, season=None)`

**Purpose:** Main ranking algorithm that produces basic output

**Parameters:**
- `hitter_metric: str` - Hitting metric name
- `pitcher_metric: str` - Pitching metric name
- `season: Optional[int]` - Season year

**Returns:**
```python
{
  "AL": [("Team Name", score), ...],
  "NL": [("Team Name", score), ...]
}
```

**Algorithm:**
1. Validate metrics against METRIC_DIRECTION
2. Get latest season if not provided
3. Aggregate hitting stats → dict[team_name: float]
4. Aggregate pitching stats → dict[team_name: float]
5. Calculate Z-scores with normalization
6. Combine and sort
7. Split by league

#### 2. `get_ranking_with_details(hitter_metric, pitcher_metric, season=None)`

**Purpose:** Extended ranking with Z-score breakdown

**Parameters:** Same as above

**Returns:**
```python
{
  "season": int,
  "hitter_metric": str,
  "pitcher_metric": str,
  "AL": [
    {
      "rank": int,
      "team_name": str,
      "score": float,
      "hitter_value": float,
      "pitcher_value": float,
      "hitter_z_score": float,
      "pitcher_z_score": float
    },
    ...
  ],
  "NL": [...]
}
```

#### 3. `aggregate_team_hitting_stats(metric, season=None)`

**Purpose:** Query and aggregate hitting stats for all teams

**SQL Query:**
```sql
SELECT 
    t.team_name,
    AVG(CAST(phs.{metric} AS FLOAT)) as avg_metric
FROM teams t
JOIN players p ON t.team_id = p.current_team_id 
    AND t.season = p.season
JOIN player_hitting_stats phs ON p.player_id = phs.player_id 
    AND p.season = phs.season
WHERE t.season = %s
    AND p.position_type IN ('OF', 'C', 'SS', 'DH', '2B', '3B', '1B')
    AND phs.{metric} IS NOT NULL
GROUP BY t.team_name
```

**Returns:** `dict[team_name: float]`

#### 4. `aggregate_team_pitching_stats(metric, season=None)`

**Purpose:** Query and aggregate pitching stats for all teams

**SQL Query:**
```sql
SELECT 
    t.team_name,
    AVG(CAST(pps.{metric} AS FLOAT)) as avg_metric
FROM teams t
JOIN players p ON t.team_id = p.current_team_id 
    AND t.season = p.season
JOIN player_pitching_stats pps ON p.player_id = pps.player_id 
    AND p.season = pps.season
WHERE t.season = %s
    AND p.position_type = 'P'
    AND pps.{metric} IS NOT NULL
GROUP BY t.team_name
```

**Returns:** `dict[team_name: float]`

#### 5. `calculate_z_score(value, mean, std_dev)`

**Purpose:** Normalize a value using Z-score formula

**Formula:**
```
Z = (value - mean) / std_dev
```

**Returns:** `float` (can be negative, zero, or positive)

#### 6. `normalize_z_score_by_direction(z_score, metric)`

**Purpose:** Adjust Z-score based on metric direction

**Logic:**
```python
if metric in ["era", "whip", "l", "bb"]:
    return -z_score  # Flip for "lower is better"
else:
    return z_score   # Keep as-is for "higher is better"
```

**Returns:** `float` (adjusted Z-score)

### Constants & Mappings

#### `TEAM_LEAGUE_MAP`
```python
{
    "Baltimore Orioles": "AL",
    "Boston Red Sox": "AL",
    ...  # 30 teams total
    "Atlanta Braves": "NL",
    ...
}
```

#### `METRIC_DIRECTION`
```python
{
    # Hitting (higher is better)
    "avg": True,
    "ops": True,
    "hr": True,
    "rbi": True,
    "r": True,
    "h": True,
    "obp": True,
    "slg": True,
    
    # Pitching (lower is better)
    "era": False,
    "whip": False,
    "l": False,
    "bb": False,
    
    # Pitching (higher is better)
    "so": True,
    "w": True,
}
```

## SQL Query Strategy

### Aggregation Approach

**Why aggregation in SQL vs. Python?**
1. **Efficiency** - Database does filtering and grouping
2. **Scalability** - Doesn't load all player rows into memory
3. **Network** - Transfers only aggregated results
4. **Consistency** - Single source of truth

**Join Pattern:**
```
teams → players → stats
  ↓       ↓         ↓
Filter  Filter    Filter
by      by        by
season  season    metric
        & pos     & NULL
```

### Position Type Filtering

**For Hitting Stats:**
```
Included: 'OF', 'C', 'SS', 'DH', '2B', '3B', '1B'
Excluded: 'P' (pitchers)
```

**For Pitching Stats:**
```
Included: 'P' (pitchers only)
Excluded: All position players
```

## Error Handling Strategy

### Validation Layers

```
1. Parameter Validation
   ├─ Check required fields present
   ├─ Check metric names valid
   └─ Check season is integer

2. Query Validation
   ├─ Check database connection
   ├─ Handle empty result sets
   └─ Handle NULL values

3. Calculation Validation
   ├─ Check zero variance case
   └─ Handle missing data

4. Response Validation
   ├─ Ensure complete league lists
   └─ Round values appropriately
```

### Exception Handling

```python
try:
    # Validate metrics
    if metric not in METRIC_DIRECTION:
        raise ValueError(f"Unknown metric: {metric}")
    
    # Get data
    stats = aggregate_team_hitting_stats(metric, season)
    if not stats:
        raise Exception("Failed to fetch stats")
    
    # Calculate
    z_score = calculate_z_score(value, mean, std_dev)
    
except ValueError as e:
    # Handle bad input - 400 Bad Request
    return error_response(str(e), 400)

except Exception as e:
    # Handle system errors - 500 Internal Server Error
    return error_response(str(e), 500)
```

## Performance Optimizations

### 1. Query Efficiency
- Single SQL query per metric (not per team)
- GROUP BY in database
- AVG() function in database

### 2. Caching Opportunities
- Season data doesn't change mid-season
- Team names are static
- Metrics are computed once

### 3. Memory Usage
- Store only aggregated values (30 teams × 2 floats)
- Use generators where possible
- Delete intermediate results

### 4. Database Indexes (Recommended)
```sql
CREATE INDEX idx_players_team_season 
ON players(current_team_id, season);

CREATE INDEX idx_players_season_pos 
ON players(season, position_type);

CREATE INDEX idx_hitting_stats_player 
ON player_hitting_stats(player_id);

CREATE INDEX idx_pitching_stats_player 
ON player_pitching_stats(player_id);
```

## Extension Points

### Adding New Metrics

1. Add to `METRIC_DIRECTION`:
   ```python
   "new_metric": True  # or False
   ```

2. Ensure column exists in database:
   ```sql
   ALTER TABLE player_[hitting|pitching]_stats 
   ADD COLUMN new_metric DECIMAL(...)
   ```

3. Use the same functions (no code changes needed)

### Implementing Caching

```python
from django.core.cache import cache

def rank_teams_by_metrics(hitter_metric, pitcher_metric, season=None):
    cache_key = f"ranking:{season}:{hitter_metric}:{pitcher_metric}"
    
    result = cache.get(cache_key)
    if result:
        return result
    
    # ... calculate result ...
    
    cache.set(cache_key, result, timeout=3600)  # 1 hour
    return result
```

### Adding Weighted Metrics

```python
def rank_teams_with_weights(
    hitter_metric: str, 
    pitcher_metric: str,
    hitter_weight: float = 0.5,
    pitcher_weight: float = 0.5,
    season: Optional[int] = None
) -> Dict:
    # ... existing aggregation code ...
    
    final_score = (hitter_z_norm * hitter_weight) + \
                  (pitcher_z_norm * pitcher_weight)
    
    # ... rest of ranking ...
```

## Testing Strategy

### Unit Tests
- `test_calculate_z_score()` - Z-score formula correctness
- `test_normalize_z_score_by_direction()` - Direction flipping logic
- `test_aggregate_team_hitting_stats()` - SQL query validation
- `test_aggregate_team_pitching_stats()` - SQL query validation

### Integration Tests
- `test_rank_teams_by_metrics()` - Full ranking pipeline
- `test_get_ranking_with_details()` - Detailed output

### Validation Tests
- `test_invalid_metric_error()` - Error handling
- `test_missing_parameters_error()` - Validation

### Edge Case Tests
- `test_zero_variance()` - All teams have same value
- `test_missing_stats()` - Teams with no data
- `test_null_values()` - Database NULLs

## Deployment Considerations

### Pre-Deployment
- [ ] Verify database schema
- [ ] Create recommended indexes
- [ ] Test with production data
- [ ] Benchmark response times
- [ ] Load test with concurrent requests

### Runtime Monitoring
- Log all ranking requests
- Monitor query execution time
- Track error rates
- Watch memory usage

### Configuration
- Make season configurable (env variable)
- Make metric list configurable (could be database-driven)
- Add request logging
- Add performance timing
