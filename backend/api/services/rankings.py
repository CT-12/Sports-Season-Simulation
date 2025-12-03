"""
Team Rankings Service

Predicts 2026 team rankings using Monte Carlo season simulation.
Both Pythagorean and Elo methods simulate a full 162-game season.
"""

from typing import Dict, List, Tuple
from decimal import Decimal
import numpy as np

from ..utils.team_rating import calculate_team_pythagorean_rating
from ..utils.season_prediction import (
    predict_next_season_win_rate,
    calculate_log5_win_probability
)
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
    Predict 2026 team rankings using Monte Carlo season simulation.
    
    Simulates a full 162-game season using specified method, then ranks
    teams by simulated wins.
    
    Args:
        method (str): "Pythagorean" or "Elo"
    
    Returns:
        dict: {
            "NL": ["Team 1", "Team 2", ...],  # Sorted by simulated wins
            "AL": ["Team 1", "Team 2", ...]   # Sorted by simulated wins
        }
    
    Example:
        >>> rankings = predict_2026_rankings("Elo")
        >>> print(rankings["AL"][0])  # Best AL team
        'New York Yankees'
    """
    BASE_SEASON = 2025
    SIMULATIONS = 1000  # Monte Carlo simulations
    GAMES_PER_SEASON = 162
    
    # Get all teams
    teams = fetch_all_teams(BASE_SEASON)
    if not teams:
        return {"NL": [], "AL": []}
    
    # Get team win probabilities for each method
    if method == "Pythagorean":
        team_win_rates = _get_pythagorean_win_rates(teams, BASE_SEASON)
    else:  # Elo
        team_win_rates = _get_elo_win_rates(teams, BASE_SEASON)
    
    # Run Monte Carlo season simulation
    team_avg_wins = _simulate_season_monte_carlo(
        team_win_rates, 
        GAMES_PER_SEASON, 
        SIMULATIONS
    )
    
    # Separate by league and sort by wins
    nl_teams = []
    al_teams = []
    
    for team_name, avg_wins in team_avg_wins.items():
        league = TEAM_LEAGUE_MAP.get(team_name)
        if league == "NL":
            nl_teams.append((team_name, avg_wins))
        elif league == "AL":
            al_teams.append((team_name, avg_wins))
    
    # Sort by wins (descending - most wins first)
    nl_teams.sort(key=lambda x: x[1], reverse=True)
    al_teams.sort(key=lambda x: x[1], reverse=True)
    
    # Extract team names only
    return {
        "NL": [team[0] for team in nl_teams],
        "AL": [team[0] for team in al_teams]
    }


def _get_pythagorean_win_rates(teams: List[Dict], season: int) -> Dict[str, float]:
    """
    Get 2026 predicted win rates using Pythagorean method.
    
    Returns:
        dict: {team_name: predicted_win_rate}
    """
    REGRESSION_WEIGHT = 0.7
    team_win_rates = {}
    
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
        
        team_win_rates[team_name] = prediction['next_year_projected_win_rate']
    
    return team_win_rates


def _get_elo_win_rates(teams: List[Dict], season: int) -> Dict[str, float]:
    """
    Get 2026 predicted win rates using Elo method.
    
    Returns:
        dict: {team_name: predicted_win_rate}
    """
    INITIAL_ELO = Decimal('1500')
    REGRESSION_WEIGHT = Decimal('0.75')
    team_elo_ratings = {}
    
    # First, get all Elo ratings
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
        team_elo_ratings[team_name] = float(rating_2026)
    
    # Convert Elo ratings to win rates
    # Average opponent has Elo = 1500
    team_win_rates = {}
    for team_name, elo in team_elo_ratings.items():
        # Win probability against average team (1500)
        # P(win) = 1 / (1 + 10^((1500 - elo) / 400))
        win_rate = 1 / (1 + 10 ** ((1500 - elo) / 400))
        team_win_rates[team_name] = win_rate
    
    return team_win_rates


def _simulate_season_monte_carlo(
    team_win_rates: Dict[str, float],
    games_per_season: int,
    simulations: int
) -> Dict[str, float]:
    """
    Simulate full season using Monte Carlo method.
    
    Args:
        team_win_rates: Dictionary of {team_name: win_rate}
        games_per_season: Number of games per season (162)
        simulations: Number of Monte Carlo simulations
    
    Returns:
        dict: {team_name: average_wins_across_simulations}
    """
    team_names = list(team_win_rates.keys())
    team_total_wins = {name: 0.0 for name in team_names}
    
    # Run simulations
    for _ in range(simulations):
        # Simulate one season for each team
        for team_name in team_names:
            win_rate = team_win_rates[team_name]
            
            # Simulate games using binomial distribution
            # Each game is a Bernoulli trial with probability win_rate
            wins = np.random.binomial(games_per_season, win_rate)
            team_total_wins[team_name] += wins
    
    # Calculate average wins
    team_avg_wins = {
        name: total_wins / simulations 
        for name, total_wins in team_total_wins.items()
    }
    
    return team_avg_wins
