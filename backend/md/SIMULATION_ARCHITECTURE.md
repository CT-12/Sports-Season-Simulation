# MLB Team Ranking API - Architecture & System Design

## High-Level System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          CLIENT APPLICATIONS                            │
│                (Web UI, Mobile, Analytics Tools, etc.)                  │
└────────────────┬────────────────────────────────────────────────────────┘
                 │
                 │ REST API Requests (JSON)
                 │
┌────────────────▼────────────────────────────────────────────────────────┐
│                         Django REST Framework                            │
│                          (api/views.py)                                 │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────────┐ │
│  │  POST /ranking/  │  │ POST /matchup/   │  │ POST /simulation/    │ │
│  │  (existing)      │  │ (existing)       │  │ ranking/ (NEW)       │ │
│  └────────┬─────────┘  └────────┬─────────┘  └──────────┬──────────┘ │
└───────────┼──────────────────────┼─────────────────────────┼───────────┘
            │                      │                        │
            │                      │         ┌──────────────┘
            │                      │         │
┌───────────▼──────────────────────▼─────────▼──────────────────────────┐
│                      SERVICE LAYER                                     │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │              team_ranking.py (Refactored)                      │  │
│  │                                                                │  │
│  │  • rank_teams_by_metrics()  [DB wrapper]                      │  │
│  │  • get_ranking_with_details()  [DB wrapper]                   │  │
│  │                                                                │  │
│  │  • rank_teams_from_aggregated_stats()  [Core algorithm]       │  │
│  │  • get_ranking_with_details_from_aggregated_stats()  [Core]   │  │
│  │                                                                │  │
│  │  ↑ Works with ANY data source (DB or memory)                  │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                        │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │         cache_manager.py (NEW - "Load Once")                   │  │
│  │                                                                │  │
│  │  1. serialize_player_data_from_db(season)                     │  │
│  │     → Single optimized SQL query                              │  │
│  │     → Teams + Players + Stats (hitting + pitching)            │  │
│  │                                                                │  │
│  │  2. get_base_state(season, force_refresh)                     │  │
│  │     → Check cache first                                       │  │
│  │     → If miss: fetch from DB + cache                          │  │
│  │     → Return Dict[team_name -> List[player_data]]             │  │
│  │                                                                │  │
│  │  3. invalidate_base_state_cache(season)                       │  │
│  │     → Clear cache on data changes                             │  │
│  │                                                                │  │
│  │  4. get_cache_info(season)                                    │  │
│  │     → Debug endpoint                                          │  │
│  │                                                                │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                        │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │           simulation.py (NEW - "Clone Many")                   │  │
│  │                                                                │  │
│  │  1. parse_transactions(data)                                  │  │
│  │     → Validate & create SimulationTransaction objects         │  │
│  │                                                                │  │
│  │  2. clone_base_state(base_state)                              │  │
│  │     → Deep copy of rosters                                    │  │
│  │                                                                │  │
│  │  3. apply_transactions(cloned_state, transactions)            │  │
│  │     → Find player in from_team                                │  │
│  │     → Remove from list                                        │  │
│  │     → Add to to_team                                          │  │
│  │     → Raise ValueError if not found                           │  │
│  │                                                                │  │
│  │  4. aggregate_stats_from_state(state, stat_key)               │  │
│  │     → Calculate team averages from modified rosters           │  │
│  │     → Like DB aggregation but on in-memory data               │  │
│  │                                                                │  │
│  │  5. run_simulation(metrics, transactions, season, details)    │  │
│  │     → Orchestrates: Fetch → Clone → Modify → Calculate        │  │
│  │     → Returns full response with metadata                     │  │
│  │                                                                │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
                          │        │         │
                          │        │         │
          ┌───────────────┘        │         └──────────────┐
          │                        │                       │
┌─────────▼─────────┐  ┌───────────▼──────────┐  ┌─────────▼────────┐
│  Django Cache    │  │   PostgreSQL DB      │  │   Redis Cache    │
│  (LocMem/Redis)  │  │                      │  │   (Production)   │
│                  │  │  • teams table       │  │                  │
│  • Base State    │  │  • players table     │  │  • Base State    │
│    (1-hour TTL) │  │  • player_hitting_   │  │    (1-hour TTL) │
│                  │  │    stats table       │  │  • Session data  │
│  • Gets hit      │  │  • player_pitching_  │  │  • Rate limits   │
│    1000× per     │  │    stats table       │  │                  │
│    hour (with    │  │                      │  │  Shared across   │
│    cache)        │  │  Queried only on:    │  │  multiple        │
│                  │  │  • Cache miss        │  │  application     │
│                  │  │  • First request     │  │  servers         │
│                  │  │  • Cache expiration  │  │                  │
│                  │  │                      │  │                  │
└────────────────┬─┘  └──────────────────────┘  └─────────────────┘
                 │
                 └─────────────────────────────────────┐
                                                       │
                           (3 paths for different     │
                            scenarios: real ranking,   │
                            simulation, or debug)      │
                                                       │
```

---

## Request Flow: Simulation Endpoint

```
┌─────────────────────────────────────────────────────────────────────┐
│  CLIENT REQUEST                                                     │
│  POST /api/simulation/ranking/                                      │
│  {                                                                  │
│    "hitter_metric": "ops",                                         │
│    "pitcher_metric": "era",                                        │
│    "season": 2025,                                                 │
│    "transactions": [                                               │
│      {"player_name": "Ohtani", "from_team": "LAD", "to_team":"NYY"}│
│    ]                                                                │
│  }                                                                  │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│  STEP 1: INPUT VALIDATION (views.py)                               │
│  ✓ Check hitter_metric is provided                                 │
│  ✓ Check pitcher_metric is provided                                │
│  ✓ Check transactions is non-empty list                            │
│  ✓ Validate against known metrics                                  │
│  ─────────────────────────────────────────────────────────────────│
│  On error: Return 400 Bad Request with available metrics           │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│  STEP 2: PARSE TRANSACTIONS (simulation.py)                         │
│  For each transaction:                                              │
│    • Validate required fields (player_name, from_team, to_team)     │
│    • Create SimulationTransaction object                           │
│  ─────────────────────────────────────────────────────────────────│
│  On error: Return 400 Bad Request with field details               │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│  STEP 3: FETCH BASE STATE (cache_manager.py)                        │
│                                                                     │
│  FIRST REQUEST (cache miss):                                        │
│    1. Check cache: NOT FOUND                                        │
│    2. Query DB: Single optimized query                              │
│       SELECT teams, players, hitting_stats, pitching_stats          │
│       WHERE season = 2025 AND is_active = true                      │
│    3. Serialize: Organize by team                                   │
│    4. CACHE: Store with 1-hour TTL                                  │
│    5. Return: base_state dictionary                                 │
│    Time: ~500ms (one-time cost)                                     │
│                                                                     │
│  SUBSEQUENT REQUESTS (cache hit):                                   │
│    1. Check cache: FOUND                                            │
│    2. Return: base_state from cache                                 │
│    Time: ~1-2ms (LocMem) or ~5-10ms (Redis)                        │
│                                                                     │
│  base_state structure:                                              │
│  {                                                                  │
│    "Los Angeles Dodgers": [                                         │
│      {                                                              │
│        "player_id": 123,                                            │
│        "player_name": "Shohei Ohtani",                             │
│        "hitting_stats": {...},                                      │
│        "pitching_stats": {...}                                      │
│      },                                                              │
│      ...                                                             │
│    ],                                                                │
│    ...                                                               │
│  }                                                                  │
│                                                                     │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│  STEP 4: CLONE (simulation.py)                                       │
│                                                                     │
│  Deep copy of base_state to local memory                            │
│  Python: copy.deepcopy(base_state)                                 │
│                                                                     │
│  Why deep copy?                                                     │
│    • Cache contains reference to original data                      │
│    • Modifications affect the cache                                 │
│    • Need independent copy per request                              │
│                                                                     │
│  cloned_state structure: Identical to base_state                    │
│                                                                     │
│  Time: ~30-50ms (scales with ~1200 players)                         │
│                                                                     │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│  STEP 5: APPLY TRANSACTIONS (simulation.py)                          │
│                                                                     │
│  For each transaction:                                              │
│    1. Validate from_team exists: cloned_state[from_team]            │
│    2. Validate to_team exists: cloned_state[to_team]                │
│    3. FIND PLAYER:                                                  │
│       for i, player in enumerate(cloned_state[from_team]):         │
│         if player['player_name'].lower() == 'ohtani':              │
│           player_index = i                                          │
│           player_data = player                                      │
│           break                                                      │
│    4. REMOVE from from_team:                                        │
│       cloned_state[from_team].pop(player_index)                    │
│    5. ADD to to_team:                                               │
│       cloned_state[to_team].append(player_data)                    │
│    6. LOG: "Traded Ohtani from LAD to NYY"                         │
│                                                                     │
│  On error:                                                           │
│    • Team not found → ValueError                                    │
│    • Player not found → ValueError                                  │
│    • Return 400 Bad Request                                         │
│                                                                     │
│  Time: ~5-10ms for all trades                                       │
│                                                                     │
│  Result: cloned_state with players moved between teams              │
│                                                                     │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│  STEP 6: AGGREGATE STATS (simulation.py)                             │
│                                                                     │
│  Like database aggregation but on in-memory data:                   │
│                                                                     │
│  hitting_stats = aggregate_stats_from_state(cloned_state, "ops")   │
│  {                                                                  │
│    "New York Yankees": 0.835,    # avg OPS of all Yankees          │
│    "Los Angeles Dodgers": 0.805,  # avg OPS of all Dodgers         │
│    ...                                                               │
│  }                                                                  │
│                                                                     │
│  Note: Ohtani now included in Yankees stats (after trade)           │
│                                                                     │
│  pitching_stats = aggregate_stats_from_state(cloned_state, "era")  │
│  {                                                                  │
│    "New York Yankees": 3.42,     # avg ERA                         │
│    ...                                                               │
│  }                                                                  │
│                                                                     │
│  Time: ~5-10ms                                                      │
│                                                                     │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│  STEP 7: CALCULATE RANKINGS (team_ranking.py - Core Algorithm)      │
│                                                                     │
│  rank_teams_from_aggregated_stats(                                  │
│    hitting_stats={"NYY": 0.835, "LAD": 0.805, ...},               │
│    pitching_stats={"NYY": 3.42, "LAD": 3.38, ...},                │
│    hitter_metric="ops",                                             │
│    pitcher_metric="era"                                             │
│  )                                                                  │
│                                                                     │
│  Calculations (per team):                                           │
│    1. Calculate league stats:                                       │
│       hitter_mean = 0.800 (average OPS across league)              │
│       pitcher_mean = 3.40 (average ERA)                             │
│       hitter_std = 0.025 (std deviation)                            │
│       pitcher_std = 0.15                                            │
│                                                                     │
│    2. For each team (e.g., Yankees):                                │
│       hitter_z = (0.835 - 0.800) / 0.025 = 1.4 (z-score)          │
│       pitcher_z = (3.42 - 3.40) / 0.15 = 0.133                     │
│                                                                     │
│    3. Normalize by direction:                                       │
│       ERA: lower is better → flip sign                              │
│       OPS: higher is better → keep sign                             │
│       hitter_z_norm = 1.4                                           │
│       pitcher_z_norm = -0.133 (flipped)                             │
│                                                                     │
│    4. Combine scores:                                               │
│       final_score = 1.4 + (-0.133) = 1.267                         │
│                                                                     │
│    5. Rank teams (descending by score)                              │
│       AL:                                                            │
│         1. New York Yankees: 1.267                                  │
│         2. Houston Astros: 1.156                                    │
│         ...                                                          │
│       NL:                                                            │
│         1. Los Angeles Dodgers: 1.234                               │
│         ...                                                          │
│                                                                     │
│  Time: ~2-5ms                                                       │
│                                                                     │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│  STEP 8: BUILD RESPONSE (views.py + simulation.py)                   │
│                                                                     │
│  {                                                                  │
│    "AL": [                                                           │
│      {                                                              │
│        "rank": 1,                                                   │
│        "team_name": "New York Yankees",                             │
│        "score": 1.267,                                              │
│        "hitter_value": 0.835,      # avg OPS                        │
│        "pitcher_value": 3.42,      # avg ERA                        │
│        "hitter_z_score": 1.4,                                       │
│        "pitcher_z_score": -0.133                                    │
│      },                                                              │
│      ...                                                             │
│    ],                                                                │
│    "NL": [...],                                                      │
│    "simulation": {                                                   │
│      "season": 2025,                                                │
│      "hitter_metric": "ops",                                        │
│      "pitcher_metric": "era",                                       │
│      "transactions_applied": 1,                                     │
│      "transaction_messages": [                                      │
│        "Traded Shohei Ohtani from Los Angeles Dodgers to..."       │
│      ],                                                              │
│      "status": "success"                                            │
│    }                                                                 │
│  }                                                                  │
│                                                                     │
│  Time: ~5-10ms (JSON serialization)                                 │
│                                                                     │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│  CLIENT RESPONSE                                                    │
│  HTTP 200 OK                                                        │
│  Content-Type: application/json                                    │
│  Body: Full simulation results                                      │
│                                                                     │
│  Total Time: ~50-85ms (after cache warm-up)                        │
│             ~500ms (first request, cache miss)                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow Diagram

```
                    ┌─────────────────┐
                    │  User Request   │
                    │  (Transaction)  │
                    └────────┬────────┘
                             │
                     ┌───────▼──────┐
                     │ Parse Input  │
                     └───────┬──────┘
                             │
                    ┌────────▼─────────┐
                    │ Fetch Base State │
                    │   from Cache     │
                    └────────┬─────────┘
                             │
              ┌──────────────┴──────────────┐
              │                             │
         ┌────▼─────┐               ┌──────▼──────┐
         │Cache Hit │               │ Cache Miss  │
         │ (1-2ms)  │               │  (500ms)    │
         └────┬─────┘               └──────┬──────┘
              │                            │
              │                    ┌───────▼────────┐
              │                    │  Query DB      │
              │                    │  Serialize     │
              │                    │  Store Cache   │
              │                    └───────┬────────┘
              │                            │
              └────────────┬───────────────┘
                           │
                    ┌──────▼──────────┐
                    │ base_state      │
                    │ (30 teams,      │
                    │ ~1200 players)  │
                    └──────┬──────────┘
                           │
                    ┌──────▼──────────┐
                    │ Deep Copy       │
                    │ (50ms)          │
                    └──────┬──────────┘
                           │
                    ┌──────▼──────────┐
                    │ cloned_state    │
                    │ (independent)   │
                    └──────┬──────────┘
                           │
         ┌─────────────────┤
         │                 │
    ┌────▼─────┐      ┌────▼─────┐      ┌────────────┐
    │ Trade 1  │      │ Trade 2  │      │ Trade N    │
    │ Ohtani   │      │ Soto     │  ... │            │
    │ LAD→NYY  │      │ NYM→LAD  │      │            │
    └────┬─────┘      └────┬─────┘      └────┬───────┘
         │                 │                 │
         └─────────────────┼─────────────────┘
                           │
                    ┌──────▼──────────┐
                    │ modified_state  │
                    │ (rosters        │
                    │  updated)       │
                    └──────┬──────────┘
                           │
         ┌─────────────────┴─────────────────┐
         │                                   │
    ┌────▼──────────┐          ┌────────────▼────┐
    │ Aggregate     │          │ Aggregate       │
    │ Hitting Stats │          │ Pitching Stats  │
    │ (from memory) │          │ (from memory)   │
    └────┬──────────┘          └────────┬────────┘
         │                             │
         └─────────────┬───────────────┘
                       │
                ┌──────▼──────────┐
                │ Aggregated      │
                │ Statistics      │
                │ (team averages) │
                └──────┬──────────┘
                       │
                ┌──────▼──────────┐
                │ Calculate       │
                │ Z-Scores        │
                │ + Normalize     │
                │ + Combine       │
                └──────┬──────────┘
                       │
                ┌──────▼──────────┐
                │ Final Scores    │
                │ + Rankings      │
                │ (AL/NL)         │
                └──────┬──────────┘
                       │
                ┌──────▼──────────┐
                │ Build Response  │
                │ + Metadata      │
                └──────┬──────────┘
                       │
                ┌──────▼──────────┐
                │ Send to Client  │
                │ (200 OK)        │
                └──────────────────┘
```

---

## Component Dependencies

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  views.py (simulation_ranking)                             │
│         │                                                  │
│         ├── services.simulation (run_simulation)           │
│         │   │                                              │
│         │   ├── parse_transactions()                       │
│         │   ├── cache_manager.get_base_state()             │
│         │   ├── clone_base_state()                         │
│         │   ├── apply_transactions()                       │
│         │   ├── aggregate_stats_from_state()               │
│         │   └── team_ranking.rank_teams_from_aggregated_  │
│         │       stats()                                    │
│         │                                                  │
│         └── services.team_ranking (DB wrapper)             │
│             │                                              │
│             ├── aggregate_team_hitting_stats()             │
│             │   └── raw SQL query                          │
│             │                                              │
│             ├── aggregate_team_pitching_stats()            │
│             │   └── raw SQL query                          │
│             │                                              │
│             └── rank_teams_from_aggregated_stats()         │
│                 (core algorithm - data agnostic)           │
│                                                             │
│  cache_manager.py                                          │
│         │                                                  │
│         ├── serialize_player_data_from_db()                │
│         │   └── raw SQL query (teams + players + stats)    │
│         │                                                  │
│         ├── get_base_state()                               │
│         │   ├── cache.get(cache_key)                       │
│         │   ├── serialize_player_data_from_db() [miss]     │
│         │   └── cache.set(cache_key, data, ttl)            │
│         │                                                  │
│         ├── invalidate_base_state_cache()                  │
│         │   └── cache.delete(cache_key)                    │
│         │                                                  │
│         └── get_cache_info()                               │
│             └── cache.get(cache_key)                       │
│                                                             │
│  settings.py                                               │
│         │                                                  │
│         └── CACHES configuration                           │
│             ├── 'locmem' backend (dev)                     │
│             └── 'redis' backend (prod)                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Caching Strategy

```
         TIME AXIS (→)
         
First Request:
├─ 0ms: Client sends simulation request
├─ 5ms: validate input
├─ 10ms: cache.get("mlb_base_state_2025")
├─ 15ms: Cache MISS
├─ 20ms: Query database (optimized single query)
├─ 500ms: Serialize all players (1200+)
├─ 505ms: cache.set() store in cache
├─ 555ms: clone_base_state() deep copy
├─ 605ms: apply_transactions() modify rosters
├─ 650ms: aggregate_stats_from_state()
├─ 660ms: rank_teams_from_aggregated_stats()
├─ 670ms: build response JSON
└─ 680ms: send 200 OK to client

Second Request (within 1 hour):
├─ 0ms: Client sends simulation request
├─ 5ms: validate input
├─ 10ms: cache.get("mlb_base_state_2025")
├─ 12ms: Cache HIT → return base_state
├─ 60ms: clone_base_state() deep copy
├─ 70ms: apply_transactions() modify rosters
├─ 85ms: aggregate_stats_from_state()
├─ 95ms: rank_teams_from_aggregated_stats()
├─ 100ms: build response JSON
└─ 105ms: send 200 OK to client

Savings: 575ms (85% faster) on subsequent requests
```

---

## Error Handling Flow

```
Request arrives
       │
       ▼
Validate metrics
       │
   ┌───┴───┐
   │       │
   ✓       ✗ (Invalid metric)
   │       │
   │       ├→ 400 Bad Request
   │       │  "Unknown hitter metric: xyz"
   │       │  available_metrics: {...}
   │
   ▼
Validate transactions format
       │
   ┌───┴───┐
   │       │
   ✓       ✗ (Missing field)
   │       │
   │       ├→ 400 Bad Request
   │       │  "Transaction 0: Missing required fields: ['to_team']"
   │
   ▼
Get base state
       │
   ┌───┴───┐
   │       │
   ✓       ✗ (DB error)
   │       │
   │       ├→ 500 Internal Server Error
   │       │  "Simulation failed: Connection pool exhausted"
   │
   ▼
Apply transactions
       │
   ┌───┴────────┐
   │            │
   ✓            ✗ (Player not found OR Team not found)
   │            │
   │            ├→ 400 Bad Request
   │            │  "Player 'Nonexistent' not found in Los Angeles Dodgers"
   │            │  OR
   │            │  "From team not found: Boston Red Socks"
   │
   ▼
Calculate rankings
       │
   ┌───┴───┐
   │       │
   ✓       ✗ (Aggregation error)
   │       │
   │       ├→ 500 Internal Server Error
   │       │  "Simulation failed: Failed to aggregate stats..."
   │
   ▼
Return 200 OK + rankings
```

---

## Scaling Considerations

### Request Scaling

```
Requests per hour:     Time to complete     Database impact
──────────────────────────────────────────────────────────
10                    1 second              Minimal
100                   10 seconds            Minimal (cache hits)
1000                  100 seconds (1.7 min) Minimal (cache hits)
10000                 1000 seconds (16 min) Cache efficient
```

### Database Scaling

```
Queries per hour (with 1-hour cache):

Without cache:
  1000 requests × 5ms DB time = 5 seconds of DB load

With cache:
  1 DB query + 999 cache hits = 1.2 seconds total
  Reduction: 75%
```

### Memory Scaling

```
Memory per base state (1200 players):
  ~2-5 MB (JSON serialized)
  
Multiple seasons cached:
  2020: 3 MB
  2021: 3 MB
  2022: 3 MB
  2023: 3 MB
  2024: 3 MB
  2025: 3 MB
  ────────
  Total: ~18 MB (manageable)

Per-request clone (deep copy):
  ~2-5 MB per request × 100 concurrent = 200-500 MB
  (Python garbage collects after request)
```

---

**Architecture designed for scalability, performance, and maintainability.**
