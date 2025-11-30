from django.db import connection
from typing import Dict, Any, List, Optional
from datetime import date

from ..utils.team_rating import calculate_team_pythagorean_rating
from ..utils.season_prediction import (
    predict_next_season_win_rate,
    calculate_log5_win_probability
)
from ..utils.elo_rating import (
    get_team_elo_rating,
    calculate_elo_win_probability,
    convert_elo_to_display_score
)
from ..utils.teams import get_team_by_name


def get_team_id_by_name(team_name: str, season: int = 2025) -> Optional[str]:
    """
    Look up team ID from team name in the database.
    
    Args:
        team_name (str): Team name (e.g., "Los Angeles Dodgers")
        season (int): Season year (default: 2025)
    
    Returns:
        str: Team ID if found, None otherwise
    """
    team = get_team_by_name(team_name, season)
    if team:
        return str(team['id'])
    return None


def analyze_matchup(
    team_a_name: str,
    team_b_name: str,
    method: str = "Pythagorean"
) -> Optional[Dict[str, Any]]:
    """
    Analyze a matchup between two teams using specified rating method.
    
    Supports two methods:
    1. Pythagorean (default): 
       - 2025 data → Regression to mean → 2026 prediction
       - Log5 win probability
       - Monte Carlo scoring
    
    2. Elo:
       - Latest Elo ratings from team_elo_history
       - Standard Elo win probability formula
       - Elo-to-score conversion
    
    Args:
        team_a_name (str): Team A name
        team_b_name (str): Team B name
        method (str): "Pythagorean" or "Elo" (default: "Pythagorean")
    
    Returns:
        dict: {
            "team_A": list[player],
            "team_B": list[player],
            "team_A_score": float,
            "team_B_score": float,
            "team_A_win_prob": float,
            "team_B_win_prob": float
        }
        None if matchup analysis fails
    
    Example:
        >>> result = analyze_matchup('Dodgers', 'Yankees', method='Elo')
        >>> print(f"Win Prob: {result['team_A_win_prob']}%")
    """
    # Validate method
    if method not in ["Pythagorean", "Elo"]:
        print(f"[Error] Invalid method: {method}. Must be 'Pythagorean' or 'Elo'")
        return None
    
    # Fixed parameters
    BASE_SEASON = 2025
    
    # Get team IDs
    team_a_id = get_team_id_by_name(team_a_name, BASE_SEASON)
    team_b_id = get_team_id_by_name(team_b_name, BASE_SEASON)
    
    if not team_a_id or not team_b_id:
        return None
    
    # Get player rosters
    from ..utils.roster import fetch_team_roster
    roster_a = fetch_team_roster(int(team_a_id), BASE_SEASON)
    roster_b = fetch_team_roster(int(team_b_id), BASE_SEASON)
    
    # Calculate scores and win probabilities based on method
    if method == "Pythagorean":
        result = _calculate_pythagorean_matchup(team_a_id, team_b_id, BASE_SEASON)
    else:  # Elo
        result = _calculate_elo_matchup(team_a_id, team_b_id, BASE_SEASON)
    
    if not result:
        return None
    
    # Build response
    return {
        'team_A': roster_a,
        'team_B': roster_b,
        'team_A_score': result['team_a_score'],
        'team_B_score': result['team_b_score'],
        'team_A_win_prob': result['team_a_win_prob'],
        'team_B_win_prob': result['team_b_win_prob']
    }


def _calculate_pythagorean_matchup(
    team_a_id: str,
    team_b_id: str,
    base_season: int
) -> Optional[Dict[str, float]]:
    """
    Calculate matchup using Pythagorean method with regression to mean.
    Uses Monte Carlo simulation for both scores and win probability.
    """
    PREDICTION_WEIGHT = 0.7
    MC_SIMULATIONS = 10000
    
    # Step 1: Get 2025 Pythagorean ratings
    rating_a = calculate_team_pythagorean_rating(team_a_id, base_season)
    rating_b = calculate_team_pythagorean_rating(team_b_id, base_season)
    
    if not rating_a or not rating_b:
        return None
    
    if not rating_a.get('total_runs_scored') or not rating_b.get('total_runs_scored'):
        return None
    
    # Step 2: Predict 2026 win rates with regression to mean
    prediction_a = predict_next_season_win_rate(
        rating_a['total_runs_scored'],
        rating_a['total_runs_allowed'],
        weight=PREDICTION_WEIGHT
    )
    
    prediction_b = predict_next_season_win_rate(
        rating_b['total_runs_scored'],
        rating_b['total_runs_allowed'],
        weight=PREDICTION_WEIGHT
    )
    
    # Step 3: Monte Carlo simulation for both scores and win probability
    import numpy as np
    
    # Base scores from 2026 predictions
    base_score_a = prediction_a['next_year_projected_win_rate'] * 100
    base_score_b = prediction_b['next_year_projected_win_rate'] * 100
    
    # Standard deviation based on sample size (games played)
    std_dev_a = 100 / np.sqrt(rating_a.get('games_played', 100))
    std_dev_b = 100 / np.sqrt(rating_b.get('games_played', 100))
    
    # Run Monte Carlo simulations
    team_a_scores = []
    team_b_scores = []
    team_a_wins = 0
    
    for _ in range(MC_SIMULATIONS):
        # Sample scores from normal distribution
        score_a = np.random.normal(base_score_a, std_dev_a)
        score_b = np.random.normal(base_score_b, std_dev_b)
        
        # Clip to valid range
        score_a = max(0, min(100, score_a))
        score_b = max(0, min(100, score_b))
        
        team_a_scores.append(score_a)
        team_b_scores.append(score_b)
        
        # Count wins for probability
        if score_a > score_b:
            team_a_wins += 1
    
    # Calculate results from simulations
    team_a_win_prob = (team_a_wins / MC_SIMULATIONS) * 100
    team_b_win_prob = 100 - team_a_win_prob
    
    return {
        'team_a_score': round(np.mean(team_a_scores), 2),
        'team_b_score': round(np.mean(team_b_scores), 2),
        'team_a_win_prob': round(team_a_win_prob, 2),
        'team_b_win_prob': round(team_b_win_prob, 2)
    }


def _calculate_elo_matchup(
    team_a_id: str,
    team_b_id: str,
    season: int
) -> Optional[Dict[str, float]]:
    """
    Calculate matchup using Elo ratings with 2026 prediction.
    
    Uses latest 2025 Elo ratings, applies regression to mean,
    then uses Monte Carlo simulation for 2026 scores and win probability.
    """
    PREDICTION_WEIGHT = 0.75  # Elo season regression weight
    MC_SIMULATIONS = 10000
    
    # Get latest available 2025 Elo ratings from database
    # Query for the most recent rating in the 2025 season
    from django.db import connection as db_connection
    
    with db_connection.cursor() as cursor:
        # Get latest 2025 rating for team A
        cursor.execute("""
            SELECT rating FROM team_elo_history
            WHERE team_id = %s AND season = %s
            ORDER BY date DESC LIMIT 1
        """, [int(team_a_id), season])
        row_a = cursor.fetchone()
        rating_a_2025 = row_a[0] if row_a else None
        
        # Get latest 2025 rating for team B
        cursor.execute("""
            SELECT rating FROM team_elo_history
            WHERE team_id = %s AND season = %s
            ORDER BY date DESC LIMIT 1
        """, [int(team_b_id), season])
        row_b = cursor.fetchone()
        rating_b_2025 = row_b[0] if row_b else None
    
    if not rating_a_2025 or not rating_b_2025:
        print(f"[Error] Elo ratings not found for teams {team_a_id} and/or {team_b_id} in {season}")
        return None
    
    # Convert to Decimal for calculations
    from decimal import Decimal
    rating_a_2025 = Decimal(str(rating_a_2025))
    rating_b_2025 = Decimal(str(rating_b_2025))
    
    # Apply season regression for 2026 prediction
    # Formula: new_rating = (old_rating × 0.75) + (1500 × 0.25)
    INITIAL_ELO = Decimal('1500')
    REGRESSION_WEIGHT = Decimal(str(PREDICTION_WEIGHT))
    
    rating_a_2026 = (rating_a_2025 * REGRESSION_WEIGHT) + (INITIAL_ELO * (Decimal('1') - REGRESSION_WEIGHT))
    rating_b_2026 = (rating_b_2025 * REGRESSION_WEIGHT) + (INITIAL_ELO * (Decimal('1') - REGRESSION_WEIGHT))
    
    # Convert 2026 Elo to base scores (0-100 scale)
    # Elo range: 1200-1800 → Score range: 0-100
    def elo_to_score(elo):
        return ((float(elo) - 1200) / 600) * 100
    
    base_score_a = elo_to_score(rating_a_2026)
    base_score_b = elo_to_score(rating_b_2026)
    
    # Estimate standard deviation based on Elo rating uncertainty
    # Higher rated teams have shown more stability, lower std dev
    std_dev_a = abs(float(rating_a_2026 - INITIAL_ELO)) / 400 * 10  # Scaled to 0-100
    std_dev_b = abs(float(rating_b_2026 - INITIAL_ELO)) / 400 * 10
    
    # Ensure reasonable std dev range (3-10)
    std_dev_a = max(3, min(10, std_dev_a))
    std_dev_b = max(3, min(10, std_dev_b))
    
    # Run Monte Carlo simulation
    import numpy as np
    
    team_a_scores = []
    team_b_scores = []
    team_a_wins = 0
    
    for _ in range(MC_SIMULATIONS):
        # Sample scores from normal distribution
        score_a = np.random.normal(base_score_a, std_dev_a)
        score_b = np.random.normal(base_score_b, std_dev_b)
        
        # Clip to valid range
        score_a = max(0, min(100, score_a))
        score_b = max(0, min(100, score_b))
        
        team_a_scores.append(score_a)
        team_b_scores.append(score_b)
        
        # Count wins for probability
        if score_a > score_b:
            team_a_wins += 1
    
    # Calculate results from simulations
    team_a_win_prob = (team_a_wins / MC_SIMULATIONS) * 100
    team_b_win_prob = 100 - team_a_win_prob
    
    return {
        'team_a_score': round(np.mean(team_a_scores), 2),
        'team_b_score': round(np.mean(team_b_scores), 2),
        'team_a_win_prob': round(team_a_win_prob, 2),
        'team_b_win_prob': round(team_b_win_prob, 2)
    }
    
    if not rating_a_2025 or not rating_b_2025:
        print(f"[Error] Elo ratings not found for teams {team_a_id} and/or {team_b_id}")
        return None
    
    # Apply season regression for 2026 prediction
    # Formula: new_rating = (old_rating × 0.75) + (1500 × 0.25)
    INITIAL_ELO = 1500
    rating_a_2026 = (rating_a_2025 * PREDICTION_WEIGHT) + (INITIAL_ELO * (1 - PREDICTION_WEIGHT))
    rating_b_2026 = (rating_b_2025 * PREDICTION_WEIGHT) + (INITIAL_ELO * (1 - PREDICTION_WEIGHT))
    
    # Convert 2026 Elo to base scores (0-100 scale)
    # Elo range: 1200-1800 → Score range: 0-100
    def elo_to_score(elo):
        return ((float(elo) - 1200) / 600) * 100
    
    base_score_a = elo_to_score(rating_a_2026)
    base_score_b = elo_to_score(rating_b_2026)
    
    # Estimate standard deviation based on Elo rating uncertainty
    # Higher rated teams have shown more stability, lower std dev
    # Typical Elo std dev is about 3-5% of the rating
    std_dev_a = abs(float(rating_a_2026 - INITIAL_ELO)) / 400 * 10  # Scaled to 0-100
    std_dev_b = abs(float(rating_b_2026 - INITIAL_ELO)) / 400 * 10
    
    # Ensure reasonable std dev range (3-10)
    std_dev_a = max(3, min(10, std_dev_a))
    std_dev_b = max(3, min(10, std_dev_b))
    
    # Run Monte Carlo simulation
    import numpy as np
    
    team_a_scores = []
    team_b_scores = []
    team_a_wins = 0
    
    for _ in range(MC_SIMULATIONS):
        # Sample scores from normal distribution
        score_a = np.random.normal(base_score_a, std_dev_a)
        score_b = np.random.normal(base_score_b, std_dev_b)
        
        # Clip to valid range
        score_a = max(0, min(100, score_a))
        score_b = max(0, min(100, score_b))
        
        team_a_scores.append(score_a)
        team_b_scores.append(score_b)
        
        # Count wins for probability
        if score_a > score_b:
            team_a_wins += 1
    
    # Calculate results from simulations
    team_a_win_prob = (team_a_wins / MC_SIMULATIONS) * 100
    team_b_win_prob = 100 - team_a_win_prob
    
    return {
        'team_a_score': round(np.mean(team_a_scores), 2),
        'team_b_score': round(np.mean(team_b_scores), 2),
        'team_a_win_prob': round(team_a_win_prob, 2),
        'team_b_win_prob': round(team_b_win_prob, 2)
    }
