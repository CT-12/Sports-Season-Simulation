# Quick Start: Simulation Endpoint

## Setup (5 minutes)

### 1. Configuration

Ensure your `.env` file has cache settings:

```bash
# Development (default)
CACHE_BACKEND=locmem

# Or Production (if using Redis)
CACHE_BACKEND=redis
REDIS_URL=redis://localhost:6379/1
```

### 2. Dependencies

Requirements are already in `requirements.txt`. If needed, install manually:

```bash
pip install Django==5.0.2
pip install djangorestframework==3.14.0
pip install django-redis  # Optional, for Redis support
```

### 3. Start Server

```bash
python manage.py runserver
```

---

## First Request (30 seconds)

### Test Basic Ranking

```bash
curl -X POST http://localhost:8000/api/ranking/ \
  -H "Content-Type: application/json" \
  -d '{
    "hitter_metric": "ops",
    "pitcher_metric": "era",
    "season": 2025
  }'
```

**Expected response:** AL and NL rankings

---

## Simulation Request (Your First Trade!)

### Test Single Trade

```bash
curl -X POST http://localhost:8000/api/simulation/ranking/ \
  -H "Content-Type: application/json" \
  -d '{
    "hitter_metric": "ops",
    "pitcher_metric": "era",
    "season": 2025,
    "transactions": [
      {
        "player_name": "Shohei Ohtani",
        "position": "Two-Way Player",
        "from_team": "Los Angeles Dodgers",
        "to_team": "New York Yankees"
      }
    ]
  }'
```

### What You'll See

```json
{
  "AL": [
    {
      "rank": 1,
      "team_name": "New York Yankees",
      "score": 2.523,
      "hitter_value": 0.850,
      "pitcher_value": 3.45,
      "hitter_z_score": 1.567,
      "pitcher_z_score": 0.956
    },
    ...
  ],
  "NL": [...],
  "simulation": {
    "season": 2025,
    "hitter_metric": "ops",
    "pitcher_metric": "era",
    "transactions_applied": 1,
    "transaction_messages": [
      "Traded Shohei Ohtani from Los Angeles Dodgers to New York Yankees"
    ],
    "status": "success"
  }
}
```

**Notice:**
- Yankees appear higher in AL ranking
- Simulation metadata shows what happened
- No changes to the actual database
- Response includes detailed Z-scores

---

## Common Requests

### Get Cache Status

```bash
curl http://localhost:8000/api/cache/status/?season=2025
```

### Multi-Team Trade

```bash
curl -X POST http://localhost:8000/api/simulation/ranking/ \
  -H "Content-Type: application/json" \
  -d '{
    "hitter_metric": "avg",
    "pitcher_metric": "whip",
    "season": 2025,
    "transactions": [
      {
        "player_name": "Shohei Ohtani",
        "position": "DH",
        "from_team": "Los Angeles Dodgers",
        "to_team": "New York Yankees"
      },
      {
        "player_name": "Juan Soto",
        "position": "OF",
        "from_team": "New York Mets",
        "to_team": "Los Angeles Dodgers"
      }
    ]
  }'
```

### Detailed Results

Add `"details": true` to see Z-scores and metric values:

```json
{
  "hitter_metric": "ops",
  "pitcher_metric": "era",
  "season": 2025,
  "details": true,
  ...
}
```

---

## Error Handling

### Player Not Found

```json
{
  "error": "Player 'Nonexistent Player' not found in Los Angeles Dodgers"
}
```

**Fix:** Check exact player name in database

### Invalid Metric

```json
{
  "error": "Unknown hitter metric: xyz",
  "available_metrics": {
    "hitting": ["avg", "ops", "ops_plus", "hr", "rbi", "r", "h", "obp", "slg"],
    "pitching": ["era", "era_plus", "whip", "so", "w", "l", "bb"]
  }
}
```

### Missing Required Field

```json
{
  "error": "Transaction 0: Missing required fields: ['to_team']"
}
```

**Fix:** Ensure all transaction fields are present:
- `player_name`
- `position`
- `from_team`
- `to_team`

---

## Performance Tips

### Cache Warm-up (on first deployment)

The first request will populate the cache from the database. This takes ~1-2 seconds.

Subsequent requests reuse the cached data and run in ~60ms.

```bash
# Warm up cache
curl http://localhost:8000/api/cache/status/?season=2025
```

### Batch Testing

If running many simulations:

1. First request warms cache
2. Remaining requests are fast (~60ms each)
3. No benefit to parallel requests (cache overhead)

### Clear Cache When Data Changes

After updating player stats in the database:

```python
from api.services.cache_manager import invalidate_base_state_cache
invalidate_base_state_cache(season=2025)
```

---

## Testing Your Integration

### Python Script Example

```python
import requests
import json

BASE_URL = "http://localhost:8000/api"

def test_simulation():
    payload = {
        "hitter_metric": "ops",
        "pitcher_metric": "era",
        "season": 2025,
        "transactions": [
            {
                "player_name": "Shohei Ohtani",
                "position": "DH",
                "from_team": "Los Angeles Dodgers",
                "to_team": "New York Yankees"
            }
        ]
    }
    
    response = requests.post(
        f"{BASE_URL}/simulation/ranking/",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✓ Simulation successful")
        print(f"  Transactions applied: {result['simulation']['transactions_applied']}")
        print(f"  Yankees rank: {result['AL'][0]['rank']} (after trade)")
    else:
        print(f"✗ Error: {response.status_code}")
        print(response.json())

if __name__ == "__main__":
    test_simulation()
```

Run it:
```bash
python test_simulation.py
```

---

## Debugging

### Enable Logging

In `settings.py`:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'api.services': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

### Inspect Cache

```python
from django.core.cache import cache
from api.services.cache_manager import BASE_STATE_CACHE_KEY

cache_key = BASE_STATE_CACHE_KEY.format(season=2025)
cached_data = cache.get(cache_key)

if cached_data:
    print(f"Teams: {list(cached_data.keys())}")
    print(f"Players in LAD: {len(cached_data.get('Los Angeles Dodgers', []))}")
else:
    print("Cache miss - will fetch from DB")
```

---

## Next Steps

1. **Read the Full Guide:** `SIMULATION_IMPLEMENTATION.md`
2. **Review OpenAPI Spec:** `SIMULATION_OPENAPI.yaml`
3. **Check Source Code:** `api/services/simulation.py`, `api/services/cache_manager.py`
4. **Write Tests:** Create unit tests for your use cases
5. **Deploy:** Use Redis for production caching

---

## Support

### Common Issues

**Q: "Player not found" error**
- A: Check exact player name (case-insensitive, but spelling matters)

**Q: Slow first request**
- A: First request loads from DB. Subsequent requests use cache (1 hour default)

**Q: Results don't change**
- A: Ensure transaction is being applied (check `transaction_messages`)

**Q: Cache not working**
- A: Check `CACHE_BACKEND` setting. Run `curl localhost:8000/api/cache/status/?season=2025`

### Logs Location

```bash
# If running with: python manage.py runserver
# Logs appear in terminal output

# If running with gunicorn:
tail -f /var/log/gunicorn.log
```

---

## Architecture Diagram

```
┌────────────────────────────────────────────────────┐
│              Client Request                        │
│  POST /api/simulation/ranking/                     │
└────────────────────────────────────────────────────┘
                        ↓
┌────────────────────────────────────────────────────┐
│         API View (views.py)                        │
│  ✓ Validate metrics                               │
│  ✓ Parse transactions                             │
│  ✓ Call simulation service                        │
└────────────────────────────────────────────────────┘
                        ↓
┌────────────────────────────────────────────────────┐
│    Simulation Service (simulation.py)              │
│  1. Fetch base state from cache                    │
│  2. Clone state (deep copy)                        │
│  3. Apply transactions (move players)              │
│  4. Aggregate stats from modified state            │
│  5. Delegate to ranking calculation                │
└────────────────────────────────────────────────────┘
                        ↓
        ┌───────────────┼───────────────┐
        ↓               ↓               ↓
   ┌─────────┐    ┌──────────┐    ┌──────────┐
   │ Cache   │    │ Ranking  │    │ Response │
   │ Manager │    │ Service  │    │ Builder  │
   │         │    │          │    │          │
   │Get/Store│    │Z-scores  │    │AL/NL     │
   └─────────┘    │Combine   │    │Metadata  │
                  └──────────┘    └──────────┘
                        ↓
┌────────────────────────────────────────────────────┐
│            JSON Response                           │
│  - AL rankings                                     │
│  - NL rankings                                     │
│  - Simulation metadata                             │
└────────────────────────────────────────────────────┘
```

---

Good luck with your simulations! 🚀
