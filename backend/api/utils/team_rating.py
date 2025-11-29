"""
Team Rating Utilities using Pythagorean Expectation

This module provides utilities for calculating team ratings based on 
the Pythagorean expectation formula, which estimates a team's expected 
win percentage based on runs scored and runs allowed.

The Pythagorean expectation formula:
    Expected Win % = RS^exponent / (RS^exponent + RA^exponent)

Where:
- RS = Total Runs Scored
- RA = Total Runs Allowed  
- exponent = 1.83 (Pythagenpat formula, more accurate than 2.0)
"""

from django.db import connection
from typing import Dict, Any, Optional


def calculate_team_pythagorean_rating(
    team_id: str, 
    season: int, 
    exponent: float = 1.83
) -> Optional[Dict[str, Any]]:
    """
    Calculate team's Pythagorean expectation rating based on game logs.
    
    This function queries the team_game_logs table to calculate a team's
    performance rating using the Pythagorean expectation formula.
    
    Args:
        team_id (str|int): Team ID to calculate rating for
        season (int): Year/season to analyze (e.g., 2024)
        exponent (float): Pythagorean exponent, default 1.83 (Pythagenpat)
                         Common values: 2.0 (original), 1.83 (more accurate)
    
    Returns:
        dict: Dictionary containing:
            - team_id: Input team ID
            - season: Input season
            - games_played: Number of games in the dataset
            - total_runs_scored: Total runs scored by team
            - total_runs_allowed: Total runs allowed by team
            - expected_win_rate: Calculated win percentage (0.0-1.0)
            - rating_score: Rating on 0-100 scale
            - msg: Optional message (for errors or special cases)
        
        None: If calculation fails due to database error
    
    Example:
        >>> result = calculate_team_pythagorean_rating('108', 2024)
        >>> print(f"Rating: {result['rating_score']}")
        Rating: 55.2
    """
    try:
        with connection.cursor() as cursor:
            # Query to aggregate runs scored/allowed from game logs
            sql = """
                SELECT 
                    SUM(team_score) as total_rs, 
                    SUM(opponent_score) as total_ra,
                    COUNT(*) as games_played
                FROM team_game_logs 
                WHERE team_id = %s AND season = %s;
            """
            
            cursor.execute(sql, [team_id, season])
            
            # Fetch result as dict
            columns = [col[0] for col in cursor.description]
            row = cursor.fetchone()
            
            if not row:
                return {
                    "team_id": team_id,
                    "season": season,
                    "rating_score": 0,
                    "msg": "查無該年度比賽數據"
                }
            
            result = dict(zip(columns, row))
            
            # Handle case where no games found
            if result['total_rs'] is None or result['total_ra'] is None:
                return {
                    "team_id": team_id,
                    "season": season,
                    "rating_score": 0,
                    "msg": "查無該年度比賽數據"
                }
            
            # Convert to float for calculations
            rs = float(result['total_rs'])  # Total Runs Scored
            ra = float(result['total_ra'])  # Total Runs Allowed
            games = result['games_played']
            
            # Handle edge case: both RS and RA are zero
            if rs == 0 and ra == 0:
                return {
                    "team_id": team_id,
                    "season": season,
                    "rating_score": 50.0,  # Average rating
                    "msg": "無得分紀錄"
                }
            
            # --- Core Algorithm: Pythagorean Expectation ---
            # Formula: RS^exponent / (RS^exponent + RA^exponent)
            rs_exp = rs ** exponent
            ra_exp = ra ** exponent
            expected_win_pct = rs_exp / (rs_exp + ra_exp)
            
            # --- Convert to Rating Score ---
            # Convert win rate (0.0-1.0) to 0-100 scale
            # Example: 0.552 win rate -> 55.2 rating score
            rating_score = round(expected_win_pct * 100, 1)
            
            return {
                "team_id": team_id,
                "season": season,
                "games_played": games,
                "total_runs_scored": int(rs),
                "total_runs_allowed": int(ra),
                "expected_win_rate": round(expected_win_pct, 3),
                "rating_score": rating_score
            }
    
    except Exception as e:
        print(f"[Error] Failed to calculate team rating: {e}")
        return None


def calculate_multiple_teams_ratings(
    team_ids: list, 
    season: int, 
    exponent: float = 1.83
) -> Dict[str, Optional[Dict[str, Any]]]:
    """
    Calculate Pythagorean ratings for multiple teams.
    
    Args:
        team_ids (list): List of team IDs to calculate
        season (int): Season year
        exponent (float): Pythagorean exponent
    
    Returns:
        dict: Mapping of team_id to rating result
    
    Example:
        >>> results = calculate_multiple_teams_ratings(['108', '109'], 2024)
        >>> for team_id, data in results.items():
        ...     print(f"{team_id}: {data['rating_score']}")
    """
    results = {}
    for team_id in team_ids:
        results[team_id] = calculate_team_pythagorean_rating(
            team_id, season, exponent
        )
    return results


def get_team_rating_comparison(
    team_id_a: str,
    team_id_b: str,
    season: int,
    exponent: float = 1.83
) -> Optional[Dict[str, Any]]:
    """
    Compare two teams' Pythagorean ratings.
    
    Args:
        team_id_a (str): First team ID
        team_id_b (str): Second team ID
        season (int): Season year
        exponent (float): Pythagorean exponent
    
    Returns:
        dict: Comparison data including:
            - team_a: Team A rating data
            - team_b: Team B rating data
            - favorite: ID of team with higher rating
            - rating_difference: Absolute difference in ratings
        
        None: If calculation fails
    
    Example:
        >>> comparison = get_team_rating_comparison('108', '109', 2024)
        >>> print(f"Favorite: Team {comparison['favorite']}")
    """
    rating_a = calculate_team_pythagorean_rating(team_id_a, season, exponent)
    rating_b = calculate_team_pythagorean_rating(team_id_b, season, exponent)
    
    if not rating_a or not rating_b:
        return None
    
    score_a = rating_a.get('rating_score', 0)
    score_b = rating_b.get('rating_score', 0)
    
    return {
        'team_a': rating_a,
        'team_b': rating_b,
        'favorite': team_id_a if score_a > score_b else team_id_b,
        'rating_difference': abs(score_a - score_b)
    }


def get_league_top_teams(
    season: int,
    limit: int = 10,
    exponent: float = 1.83
) -> list:
    """
    Get top teams by Pythagorean rating for a given season.
    
    Args:
        season (int): Season year
        limit (int): Number of top teams to return
        exponent (float): Pythagorean exponent
    
    Returns:
        list: List of team ratings sorted by rating_score (descending)
    
    Example:
        >>> top_teams = get_league_top_teams(2024, limit=5)
        >>> for team in top_teams:
        ...     print(f"{team['team_id']}: {team['rating_score']}")
    """
    try:
        with connection.cursor() as cursor:
            # Get all teams that played in the season
            sql = """
                SELECT DISTINCT team_id
                FROM team_game_logs
                WHERE season = %s;
            """
            cursor.execute(sql, [season])
            team_ids = [row[0] for row in cursor.fetchall()]
        
        # Calculate ratings for all teams
        ratings = []
        for team_id in team_ids:
            rating = calculate_team_pythagorean_rating(team_id, season, exponent)
            if rating and rating.get('rating_score', 0) > 0:
                ratings.append(rating)
        
        # Sort by rating score descending
        ratings.sort(key=lambda x: x.get('rating_score', 0), reverse=True)
        
        return ratings[:limit]
    
    except Exception as e:
        print(f"[Error] Failed to get top teams: {e}")
        return []
