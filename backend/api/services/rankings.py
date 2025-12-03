"""
Team Rankings Service

Predicts 2026 team rankings using Pythagorean or Elo method.
"""

from typing import Dict, List
from decimal import Decimal

from ..utils.team_rating import calculate_team_pythagorean_rating
from ..utils.season_prediction import predict_next_season_win_rate
from ..utils.elo_rating import get_team_elo_rating
from ..utils.teams import fetch_all_teams


# Team to League mapping
TEAM_LEAGUE_MAP = {
    # American League (AL)
    "Baltimore Orioles": "AL",
    "Boston Red Sox": "AL",
    "New York Yankees": "AL",
    "Tampa Bay Rays": "AL",
    "Toronto Blue Jays": "AL",
    "Chicago White Sox": "AL",
    "Cleveland Guardians": "AL",
    "Detroit Tigers": "AL",
    "Kansas City Royals": "AL",
    "Minnesota Twins": "AL",
    "Houston Astros": "AL",
    "Los Angeles Angels": "AL",
    "Athletics": "AL",  # 資料庫中是 "Athletics" 而不是 "Oakland Athletics"
    "Seattle Mariners": "AL",
    "Texas Rangers": "AL",
    
    # National League (NL)
    "Atlanta Braves": "NL",
    "Miami Marlins": "NL",
    "New York Mets": "NL",
    "Philadelphia Phillies": "NL",
    "Washington Nationals": "NL",
    "Chicago Cubs": "NL",
    "Cincinnati Reds": "NL",
    "Milwaukee Brewers": "NL",
    "Pittsburgh Pirates": "NL",
    "St. Louis Cardinals": "NL",
    "Arizona Diamondbacks": "NL",
    "Colorado Rockies": "NL",
    "Los Angeles Dodgers": "NL",
    "San Diego Padres": "NL",
    "San Francisco Giants": "NL",
}


def predict_2026_rankings(method: str = "Pythagorean") -> Dict[str, List[str]]:
    """
    Predict 2026 team rankings using specified method.
    
    Args:
        method (str): "Pythagorean" or "Elo"
    
    Returns:
        dict: {
            "NL": ["Team 1", "Team 2", ...],  # Sorted by predicted strength
            "AL": ["Team 1", "Team 2", ...]   # Sorted by predicted strength
        }
    
    Example:
        >>> rankings = predict_2026_rankings("Elo")
        >>> print(rankings["AL"][0])  # Best AL team
        'New York Yankees'
    """
    BASE_SEASON = 2025
    
    # Get all teams
    teams = fetch_all_teams(BASE_SEASON)
    if not teams:
        return {"NL": [], "AL": []}
    
    # Calculate scores for all teams
    team_scores = {}
    
    if method == "Pythagorean":
        team_scores = _calculate_pythagorean_rankings(teams, BASE_SEASON)
    else:  # Elo
        team_scores = _calculate_elo_rankings(teams, BASE_SEASON)
    
    # Separate by league and sort
    nl_teams = []
    al_teams = []
    
    for team_name, score in team_scores.items():
        league = TEAM_LEAGUE_MAP.get(team_name)
        if league == "NL":
            nl_teams.append((team_name, score))
        elif league == "AL":
            al_teams.append((team_name, score))
    
    # Sort by score (descending - higher is better)
    nl_teams.sort(key=lambda x: x[1], reverse=True)
    al_teams.sort(key=lambda x: x[1], reverse=True)
    
    # Extract team names only
    return {
        "NL": [team[0] for team in nl_teams],
        "AL": [team[0] for team in al_teams]
    }


def _calculate_pythagorean_rankings(teams: List[Dict], season: int) -> Dict[str, float]:
    """
    Calculate 2026 predictions using Pythagorean method.
    
    Returns:
        dict: {team_name: predicted_2026_score}
    """
    REGRESSION_WEIGHT = 0.7
    team_scores = {}
    
    for team in teams:
        team_id = str(team['id'])
        team_name = team['name']
        
        # Get 2025 Pythagorean rating
        rating = calculate_team_pythagorean_rating(team_id, season)
        if not rating or not rating.get('total_runs_scored'):
            continue
        
        # Predict 2026 with regression to mean
        prediction = predict_next_season_win_rate(
            rating['total_runs_scored'],
            rating['total_runs_allowed'],
            weight=REGRESSION_WEIGHT
        )
        
        # Convert to 0-100 scale
        score = prediction['next_year_projected_win_rate'] * 100
        team_scores[team_name] = score
    
    return team_scores


def _calculate_elo_rankings(teams: List[Dict], season: int) -> Dict[str, float]:
    """
    Calculate 2026 predictions using Elo method.
    
    Returns:
        dict: {team_name: predicted_2026_score}
    """
    INITIAL_ELO = Decimal('1500')
    REGRESSION_WEIGHT = Decimal('0.75')
    team_scores = {}
    
    for team in teams:
        team_id = team['id']
        team_name = team['name']
        
        # Get latest 2025 Elo rating
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT rating FROM team_elo_history
                WHERE team_id = %s AND season = %s
                ORDER BY date DESC LIMIT 1
            """, [team_id, season])
            row = cursor.fetchone()
            
            if not row:
                continue
            
            rating_2025 = Decimal(str(row[0]))
        
        # Apply season regression for 2026
        rating_2026 = (rating_2025 * REGRESSION_WEIGHT) + (INITIAL_ELO * (Decimal('1') - REGRESSION_WEIGHT))
        
        # Convert to 0-100 scale
        # Elo range: 1200-1800 → Score range: 0-100
        score = ((float(rating_2026) - 1200) / 600) * 100
        team_scores[team_name] = score
    
    return team_scores
