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
       - Log5 win probability (no Monte Carlo)
    
    2. Elo:
       - Latest Elo ratings from team_elo_history
       - Standard Elo win probability formula (no Monte Carlo)
    
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
    Uses direct Log5 formula for win probability (no Monte Carlo).
    """
    PREDICTION_WEIGHT = 0.7
    
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
    
    # Step 3: Convert to scores (0-100 scale)
    team_a_score = prediction_a['next_year_projected_win_rate'] * 100
    team_b_score = prediction_b['next_year_projected_win_rate'] * 100
    
    # Step 4: Calculate win probability using Log5 formula (no Monte Carlo)
    win_rate_a = prediction_a['next_year_projected_win_rate']
    win_rate_b = prediction_b['next_year_projected_win_rate']
    
    # Log5 formula: P(A beats B) = (pA - pA*pB) / (pA + pB - 2*pA*pB)
    log5_result = calculate_log5_win_probability(win_rate_a, win_rate_b)
    team_a_win_prob = log5_result['team_a_win_prob']
    team_b_win_prob = log5_result['team_b_win_prob']
    
    return {
        'team_a_score': round(team_a_score, 2),
        'team_b_score': round(team_b_score, 2),
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
    then uses standard Elo formula for win probability (no Monte Carlo).
    """
    PREDICTION_WEIGHT = 0.75  # Elo season regression weight
    
    # Get latest available 2025 Elo ratings from database
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
    
    # Convert 2026 Elo to display scores (0-100 scale)
    # Elo range: 1200-1800 → Score range: 0-100
    team_a_score = ((float(rating_a_2026) - 1200) / 600) * 100
    team_b_score = ((float(rating_b_2026) - 1200) / 600) * 100
    
    # Calculate win probability using standard Elo formula (no Monte Carlo)
    # Expected score = 1 / (1 + 10^((Rb - Ra) / 400))
    rating_diff = float(rating_b_2026 - rating_a_2026)
    team_a_win_prob = (1 / (1 + 10 ** (rating_diff / 400))) * 100
    team_b_win_prob = 100 - team_a_win_prob
    
    return {
        'team_a_score': round(team_a_score, 2),
        'team_b_score': round(team_b_score, 2),
        'team_a_win_prob': round(team_a_win_prob, 2),
        'team_b_win_prob': round(team_b_win_prob, 2)
    }
