"""
Team Rankings Service

Predicts 2026 team rankings using Monte Carlo season simulation with realistic scheduling.
Simulates a full season (approx 162 games) accounting for strength of schedule:
- Division rivals: ~13 games
- League rivals: ~6 games
- Inter-league: ~3 games
"""

from typing import Dict, List, Tuple, Any
from decimal import Decimal
import numpy as np

from ..utils.team_rating import calculate_team_pythagorean_rating
from ..utils.season_prediction import (
    predict_next_season_win_rate,
    calculate_log5_win_probability
)
from ..utils.teams import fetch_all_teams


# Team Configuration with League and Division
# Structure: {TeamName: (League, Division)}
TEAM_STRUCTURE = {
    # AL East
    "Baltimore Orioles": ("AL", "East"),
    "Boston Red Sox": ("AL", "East"),
    "New York Yankees": ("AL", "East"),
    "Tampa Bay Rays": ("AL", "East"),
    "Toronto Blue Jays": ("AL", "East"),
    
    # AL Central
    "Chicago White Sox": ("AL", "Central"),
    "Cleveland Guardians": ("AL", "Central"),
    "Detroit Tigers": ("AL", "Central"),
    "Kansas City Royals": ("AL", "Central"),
    "Minnesota Twins": ("AL", "Central"),
    
    # AL West
    "Houston Astros": ("AL", "West"),
    "Los Angeles Angels": ("AL", "West"),
    "Athletics": ("AL", "West"),
    "Seattle Mariners": ("AL", "West"),
    "Texas Rangers": ("AL", "West"),
    
    # NL East
    "Atlanta Braves": ("NL", "East"),
    "Miami Marlins": ("NL", "East"),
    "New York Mets": ("NL", "East"),
    "Philadelphia Phillies": ("NL", "East"),
    "Washington Nationals": ("NL", "East"),
    
    # NL Central
    "Chicago Cubs": ("NL", "Central"),
    "Cincinnati Reds": ("NL", "Central"),
    "Milwaukee Brewers": ("NL", "Central"),
    "Pittsburgh Pirates": ("NL", "Central"),
    "St. Louis Cardinals": ("NL", "Central"),
    
    # NL West
    "Arizona Diamondbacks": ("NL", "West"),
    "Colorado Rockies": ("NL", "West"),
    "Los Angeles Dodgers": ("NL", "West"),
    "San Diego Padres": ("NL", "West"),
    "San Francisco Giants": ("NL", "West"),
}


def predict_2026_rankings(method: str = "Pythagorean") -> Dict[str, List[str]]:
    """
    Predict 2026 team rankings using Monte Carlo season simulation.
    
    Simulates a full season with realistic schedule weighting.
    
    Args:
        method (str): "Pythagorean" or "Elo"
    
    Returns:
        dict: {
            "NL": ["Team 1", "Team 2", ...],
            "AL": ["Team 1", "Team 2", ...]
        }
    """
    BASE_SEASON = 2025
    SIMULATIONS = 1000
    
    # Get all teams
    teams_data = fetch_all_teams(BASE_SEASON)
    if not teams_data:
        return {"NL": [], "AL": []}
    
    # Map team names to IDs and validate structure
    valid_teams = []
    for team in teams_data:
        if team['name'] in TEAM_STRUCTURE:
            valid_teams.append(team)
    
    # 1. Get Team Ratings (Win Probability vs Average)
    if method == "Pythagorean":
        team_ratings = _get_pythagorean_ratings(valid_teams, BASE_SEASON)
    else:  # Elo
        team_ratings = _get_elo_ratings(valid_teams, BASE_SEASON)
    
    # 2. Generate Schedule (List of Matchups)
    schedule = _generate_balanced_schedule(list(team_ratings.keys()))
    
    # 3. Run Monte Carlo Simulation
    team_avg_wins = _simulate_schedule_monte_carlo(
        team_ratings,
        schedule,
        SIMULATIONS,
        method
    )
    
    # 4. Sort and Format Results
    nl_teams = []
    al_teams = []
    
    for team_name, avg_wins in team_avg_wins.items():
        league = TEAM_STRUCTURE.get(team_name, ("Unknown",))[0]
        if league == "NL":
            nl_teams.append((team_name, avg_wins))
        elif league == "AL":
            al_teams.append((team_name, avg_wins))
    
    # Sort by wins (descending)
    nl_teams.sort(key=lambda x: x[1], reverse=True)
    al_teams.sort(key=lambda x: x[1], reverse=True)
    
    return {
        "NL": [team[0] for team in nl_teams],
        "AL": [team[0] for team in al_teams]
    }


def _get_pythagorean_ratings(teams: List[Dict], season: int) -> Dict[str, float]:
    """Get Pythagorean win rates (vs average) for all teams."""
    REGRESSION_WEIGHT = 0.7
    ratings = {}
    
    for team in teams:
        team_id = str(team['id'])
        team_name = team['name']
        
        rating = calculate_team_pythagorean_rating(team_id, season)
        if not rating or not rating.get('total_runs_scored'):
            ratings[team_name] = 0.5  # Fallback
            continue
        
        prediction = predict_next_season_win_rate(
            rating['total_runs_scored'],
            rating['total_runs_allowed'],
            weight=REGRESSION_WEIGHT
        )
        ratings[team_name] = prediction['next_year_projected_win_rate']
    
    return ratings


def _get_elo_ratings(teams: List[Dict], season: int) -> Dict[str, float]:
    """Get Elo ratings (regressed to 2026) for all teams."""
    INITIAL_ELO = Decimal('1500')
    REGRESSION_WEIGHT = Decimal('0.75')
    ratings = {}
    
    from django.db import connection
    
    for team in teams:
        team_id = team['id']
        team_name = team['name']
        
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT rating FROM team_elo_history
                WHERE team_id = %s AND season = %s
                ORDER BY date DESC LIMIT 1
            """, [team_id, season])
            row = cursor.fetchone()
            
            if row:
                rating_2025 = Decimal(str(row[0]))
                rating_2026 = (rating_2025 * REGRESSION_WEIGHT) + (INITIAL_ELO * (Decimal('1') - REGRESSION_WEIGHT))
                ratings[team_name] = float(rating_2026)
            else:
                ratings[team_name] = 1500.0  # Fallback
                
    return ratings


def _generate_balanced_schedule(team_names: List[str]) -> List[Tuple[str, str]]:
    """
    Generate a balanced schedule of matchups.
    Returns a list of (TeamA, TeamB) tuples representing all games in a season.
    """
    schedule = []
    
    # Games per opponent type
    GAMES_DIVISION = 13
    GAMES_LEAGUE = 6
    GAMES_INTERLEAGUE = 3
    
    for i, team_a in enumerate(team_names):
        for j, team_b in enumerate(team_names):
            if i >= j: continue  # Avoid duplicates and self-play
            
            info_a = TEAM_STRUCTURE.get(team_a)
            info_b = TEAM_STRUCTURE.get(team_b)
            
            if not info_a or not info_b:
                continue
                
            league_a, div_a = info_a
            league_b, div_b = info_b
            
            num_games = 0
            
            if league_a == league_b:
                if div_a == div_b:
                    num_games = GAMES_DIVISION
                else:
                    num_games = GAMES_LEAGUE
            else:
                num_games = GAMES_INTERLEAGUE
            
            # Add matchups
            for _ in range(num_games):
                schedule.append((team_a, team_b))
                
    return schedule


def _simulate_schedule_monte_carlo(
    team_ratings: Dict[str, float],
    schedule: List[Tuple[str, str]],
    simulations: int,
    method: str
) -> Dict[str, float]:
    """
    Simulate the schedule N times using vectorized operations.
    """
    team_names = list(team_ratings.keys())
    team_indices = {name: i for i, name in enumerate(team_names)}
    num_teams = len(team_names)
    num_games = len(schedule)
    
    # 1. Prepare Matchup Probabilities Vector
    # probs[i] = Probability that Team A (schedule[i][0]) beats Team B (schedule[i][1])
    probs = np.zeros(num_games)
    
    # Map schedule to indices for fast lookup later
    game_indices_a = np.zeros(num_games, dtype=int)
    game_indices_b = np.zeros(num_games, dtype=int)
    
    for i, (name_a, name_b) in enumerate(schedule):
        rating_a = team_ratings[name_a]
        rating_b = team_ratings[name_b]
        
        game_indices_a[i] = team_indices[name_a]
        game_indices_b[i] = team_indices[name_b]
        
        if method == "Pythagorean":
            # Log5 Formula
            # Pa = rating_a, Pb = rating_b (both are win rates vs avg)
            # P(A>B) = (Pa - PaPb) / (Pa + Pb - 2PaPb)
            pa = rating_a
            pb = rating_b
            # Avoid division by zero
            denom = pa + pb - 2 * pa * pb
            if denom == 0:
                prob = 0.5
            else:
                prob = (pa - pa * pb) / denom
        else:
            # Elo Formula
            # P(A>B) = 1 / (1 + 10^((Rb - Ra) / 400))
            prob = 1 / (1 + 10 ** ((rating_b - rating_a) / 400))
            
        probs[i] = prob
        
    # 2. Run Vectorized Simulation
    # Generate random outcomes for all games in all simulations
    # Shape: (simulations, num_games)
    random_outcomes = np.random.random((simulations, num_games))
    
    # Boolean matrix: True if Team A wins
    wins_a = random_outcomes < probs
    
    # 3. Aggregate Wins
    total_wins = np.zeros(num_teams)
    
    # This part is tricky to fully vectorize without a loop over teams or games
    # But since num_teams is small (30), we can loop over teams
    # Or use np.add.at if we flatten, but loop over teams is readable and fast enough
    
    # Sum wins for Team A positions
    for i in range(num_games):
        idx_a = game_indices_a[i]
        idx_b = game_indices_b[i]
        
        # wins_a[:, i] is a column of wins for this game across all sims
        # Summing gives total wins for this game across all sims
        game_wins_a = np.sum(wins_a[:, i])
        game_wins_b = simulations - game_wins_a
        
        total_wins[idx_a] += game_wins_a
        total_wins[idx_b] += game_wins_b
        
    # 4. Calculate Average Wins
    # Normalize to 162 games if schedule length differs
    avg_wins = total_wins / simulations
    
    if num_games > 0:
        # Calculate games per team in schedule to normalize accurately
        # But simple scaling is usually fine: (AvgWins / GamesPlayed) * 162
        # Let's just return the raw simulated average, as our schedule is approx 162
        pass
        
    return {name: avg_wins[i] for i, name in enumerate(team_names)}
