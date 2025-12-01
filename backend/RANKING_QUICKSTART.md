# Team Ranking API - Quick Start Guide

## Basic Usage

### 1. Rank Teams by OPS vs ERA

```bash
curl -X POST http://localhost:8000/api/ranking/ \
  -H "Content-Type: application/json" \
  -d '{
    "hitter_metric": "ops",
    "pitcher_metric": "era"
  }'
```

**Response:**
```json
{
  "AL": [
    ["Houston Astros", 2.345],
    ["New York Yankees", 2.123],
    ["Boston Red Sox", 1.567]
  ],
  "NL": [
    ["Los Angeles Dodgers", 2.678],
    ["San Diego Padres", 2.234],
    ["Arizona Diamondbacks", 1.890]
  ]
}
```

### 2. Get Detailed Breakdown

```bash
curl -X POST http://localhost:8000/api/ranking/ \
  -H "Content-Type: application/json" \
  -d '{
    "hitter_metric": "ops",
    "pitcher_metric": "era",
    "details": true
  }'
```

**Response includes component Z-scores:**
```json
{
  "season": 2025,
  "hitter_metric": "ops",
  "pitcher_metric": "era",
  "AL": [
    {
      "rank": 1,
      "team_name": "Houston Astros",
      "score": 2.345,
      "hitter_value": 0.832,
      "pitcher_value": 3.42,
      "hitter_z_score": 1.234,
      "pitcher_z_score": 1.111
    }
  ]
}
```

### 3. Different Metric Combinations

**Strikeout Pitchers + Home Run Hitters:**
```bash
curl -X POST http://localhost:8000/api/ranking/ \
  -H "Content-Type: application/json" \
  -d '{
    "hitter_metric": "hr",
    "pitcher_metric": "so"
  }'
```

**Contact Hitters + WHIP Leaders:**
```bash
curl -X POST http://localhost:8000/api/ranking/ \
  -H "Content-Type: application/json" \
  -d '{
    "hitter_metric": "avg",
    "pitcher_metric": "whip"
  }'
```

**RBI Leaders + Winning Pitchers:**
```bash
curl -X POST http://localhost:8000/api/ranking/ \
  -H "Content-Type: application/json" \
  -d '{
    "hitter_metric": "rbi",
    "pitcher_metric": "w"
  }'
```

## Understanding the Results

### What Does the Score Mean?

The **score** is the sum of two Z-scores:

```
Final Score = Z_hitter + Z_pitcher
```

Where each Z-score represents how many standard deviations away from the league average a team is:

- **Score > 2.0**: Excellent in both categories (top tier)
- **Score 1.0 - 2.0**: Very good (upper half)
- **Score 0.0 - 1.0**: Above average (middle)
- **Score -1.0 - 0.0**: Below average (lower half)
- **Score < -1.0**: Poor (bottom tier)

### Example Interpretation

```json
{
  "rank": 1,
  "team_name": "Houston Astros",
  "score": 2.345,
  "hitter_value": 0.832,
  "pitcher_value": 3.42,
  "hitter_z_score": 1.234,
  "pitcher_z_score": 1.111
}
```

**Interpretation:**
- The Astros rank #1 in the AL for this metric combination
- Their team OPS of 0.832 is **1.234 standard deviations** above the league average
- Their team ERA of 3.42 is **1.111 standard deviations** better than average (note: ERA is "lower is better", so the Z-score is positive when ERA is low)
- Combined score of 2.345 indicates strong performance in both offensive and pitching metrics

### Why Z-Scores?

Metrics have different scales:
- OPS ranges from ~0.600 to ~0.950
- ERA ranges from ~2.50 to ~5.50
- HR ranges from ~100 to ~250

Z-scores normalize these different scales so both metrics contribute equally to the final ranking, regardless of their natural ranges.

## Common Questions

### Q: Why does a low ERA give a positive Z-score?

**A:** The algorithm detects that ERA is a "lower is better" metric and automatically flips the Z-score. So:
- Team with low ERA (3.20) → Positive Z-score
- Team with high ERA (4.50) → Negative Z-score

This ensures that higher final scores always represent better overall performance.

### Q: What if a team is missing data for a metric?

**A:** The team defaults to the league average for that metric, receiving a Z-score of 0.0 for that component. This prevents teams from being unfairly penalized for missing data.

### Q: How are teams assigned to AL/NL?

**A:** The code includes a hardcoded mapping of all 30 MLB teams to their leagues. This handles the case where the database doesn't have a "League" column. Teams not found in the map default to NL.

## Advanced Usage

### Python/Django Shell

```python
from api.services.team_ranking import rank_teams_by_metrics, get_ranking_with_details

# Simple ranking
result = rank_teams_by_metrics("ops", "era", season=2025)
print(result["AL"])  # List of (team_name, score) tuples

# Detailed ranking
details = get_ranking_with_details("ops", "era", season=2025)
for team in details["AL"]:
    print(f"{team['rank']}. {team['team_name']}: {team['score']}")
```

### Programmatic Error Handling

```python
try:
    result = rank_teams_by_metrics("invalid_metric", "era")
except ValueError as e:
    print(f"Invalid metric: {e}")

try:
    result = rank_teams_by_metrics("ops", "era", season=2020)
except Exception as e:
    print(f"Data not available: {e}")
```

## Integration Examples

### Frontend Display (HTML/JavaScript)

```html
<table id="ranking-table">
  <thead>
    <tr>
      <th>Rank</th>
      <th>Team</th>
      <th>Score</th>
      <th>Offensive Value</th>
      <th>Pitching Value</th>
    </tr>
  </thead>
  <tbody id="al-teams"></tbody>
  <tbody id="nl-teams"></tbody>
</table>

<script>
async function loadRanking() {
  const response = await fetch('/api/ranking/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      hitter_metric: 'ops',
      pitcher_metric: 'era',
      details: true
    })
  });
  
  const data = await response.json();
  
  // Render AL teams
  const alBody = document.getElementById('al-teams');
  data.AL.forEach((team, i) => {
    alBody.innerHTML += `
      <tr>
        <td>${team.rank}</td>
        <td>${team.team_name}</td>
        <td>${team.score.toFixed(3)}</td>
        <td>${team.hitter_value.toFixed(4)} (Z: ${team.hitter_z_score.toFixed(3)})</td>
        <td>${team.pitcher_value.toFixed(4)} (Z: ${team.pitcher_z_score.toFixed(3)})</td>
      </tr>
    `;
  });
}

loadRanking();
</script>
```

## Testing the API

### Using cURL

```bash
# Test basic ranking
curl -X POST http://localhost:8000/api/ranking/ \
  -H "Content-Type: application/json" \
  -d '{"hitter_metric": "ops", "pitcher_metric": "era"}'

# Test with details
curl -X POST http://localhost:8000/api/ranking/ \
  -H "Content-Type: application/json" \
  -d '{"hitter_metric": "ops", "pitcher_metric": "era", "details": true}'

# Test invalid metric (should get error)
curl -X POST http://localhost:8000/api/ranking/ \
  -H "Content-Type: application/json" \
  -d '{"hitter_metric": "invalid", "pitcher_metric": "era"}'
```

### Using Python requests

```python
import requests

url = "http://localhost:8000/api/ranking/"

# Test 1: Basic ranking
response = requests.post(url, json={
    "hitter_metric": "ops",
    "pitcher_metric": "era"
})
print(response.json())

# Test 2: Detailed ranking
response = requests.post(url, json={
    "hitter_metric": "hr",
    "pitcher_metric": "so",
    "details": True
})
print(response.json())

# Test 3: Error handling
response = requests.post(url, json={
    "hitter_metric": "invalid_metric",
    "pitcher_metric": "era"
})
print(f"Status: {response.status_code}")
print(f"Error: {response.json()}")
```

## Performance Tips

1. **Cache Results**: If the same ranking is requested multiple times, cache it for a few hours
2. **Specify Season**: If you know which season, include it to potentially use cached data
3. **Use Basic Mode**: Use `details: false` (default) for faster responses if you don't need Z-scores
4. **Batch Requests**: If testing multiple metrics, batch requests to avoid repeated database connections

## Troubleshooting

**"Failed to rank teams" error:**
- Check that stats exist in the database for the season
- Verify player-team relationships are correct
- Ensure the specified season exists

**"Unknown metric" error:**
- Check spelling of metric names (case-sensitive)
- Refer to the available metrics list
- Some metrics may not be in the database yet

**Empty results:**
- Verify data has been loaded for the season
- Check that position_type values match expected values (P, C, SS, 2B, 3B, 1B, OF, DH)
- Ensure the team name mapping includes all teams

## API Reference

**Endpoint:** `POST /api/ranking/`

**Required Parameters:**
- `hitter_metric` (string): One of [avg, ops, hr, rbi, r, h, obp, slg]
- `pitcher_metric` (string): One of [era, whip, so, w, l, bb]

**Optional Parameters:**
- `season` (integer): Default is latest available season
- `details` (boolean): Default is false

**Response Codes:**
- `200 OK`: Successful ranking
- `400 Bad Request`: Invalid metrics or missing parameters
- `500 Internal Server Error`: Database error
