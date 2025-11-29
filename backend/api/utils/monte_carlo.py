"""
Monte Carlo Simulation for Team Rating Adjustment

This module provides Monte Carlo simulation to adjust team Pythagorean ratings
by considering score variability and randomness in game outcomes.
"""

import random
from typing import Dict, Any


def monte_carlo_rating_adjustment(
    team_rating: float,
    runs_scored: int,
    runs_allowed: int,
    games_played: int,
    simulations: int = 10000,
    variance_factor: float = 0.1
) -> Dict[str, Any]:
    """
    Adjust team rating using Monte Carlo simulation.
    
    This function runs multiple simulations to account for variance in
    game outcomes, providing a more robust rating estimate.
    
    Args:
        team_rating (float): Base Pythagorean rating (0-100)
        runs_scored (int): Total runs scored by team
        runs_allowed (int): Total runs allowed by team
        games_played (int): Number of games played
        simulations (int): Number of Monte Carlo simulations (default: 10000)
        variance_factor (float): Variance multiplier (default: 0.1)
    
    Returns:
        dict: {
            'adjusted_rating': float,
            'confidence_interval': tuple,
            'std_deviation': float
        }
    """
    if games_played == 0:
        return {
            'adjusted_rating': team_rating,
            'confidence_interval': (team_rating, team_rating),
            'std_deviation': 0.0
        }
    
    # Calculate average runs per game
    avg_rs_per_game = runs_scored / games_played
    avg_ra_per_game = runs_allowed / games_played
    
    # Estimate standard deviation (simplified model)
    std_rs = avg_rs_per_game * variance_factor * (games_played ** 0.5)
    std_ra = avg_ra_per_game * variance_factor * (games_played ** 0.5)
    
    simulated_ratings = []
    
    for _ in range(simulations):
        # Simulate variation in runs scored/allowed
        sim_rs = max(0, random.gauss(runs_scored, std_rs))
        sim_ra = max(0, random.gauss(runs_allowed, std_ra))
        
        # Calculate Pythagorean expectation for this simulation
        if sim_rs == 0 and sim_ra == 0:
            sim_rating = 50.0
        else:
            exponent = 1.83
            rs_exp = sim_rs ** exponent
            ra_exp = sim_ra ** exponent
            win_pct = rs_exp / (rs_exp + ra_exp)
            sim_rating = win_pct * 100
        
        simulated_ratings.append(sim_rating)
    
    # Calculate statistics
    adjusted_rating = sum(simulated_ratings) / len(simulated_ratings)
    sorted_ratings = sorted(simulated_ratings)
    
    # 95% confidence interval
    lower_idx = int(len(sorted_ratings) * 0.025)
    upper_idx = int(len(sorted_ratings) * 0.975)
    confidence_interval = (sorted_ratings[lower_idx], sorted_ratings[upper_idx])
    
    # Standard deviation
    mean = adjusted_rating
    variance = sum((x - mean) ** 2 for x in simulated_ratings) / len(simulated_ratings)
    std_dev = variance ** 0.5
    
    return {
        'adjusted_rating': round(adjusted_rating, 2),
        'confidence_interval': (round(confidence_interval[0], 2), round(confidence_interval[1], 2)),
        'std_deviation': round(std_dev, 2)
    }


def simulate_matchup_outcome(
    team_a_rating: float,
    team_b_rating: float,
    simulations: int = 10000
) -> Dict[str, float]:
    """
    Simulate matchup outcomes using Monte Carlo method.
    
    Args:
        team_a_rating (float): Team A's rating
        team_b_rating (float): Team B's rating
        simulations (int): Number of simulations
    
    Returns:
        dict: {
            'team_a_wins': int,
            'team_b_wins': int, 
            'team_a_win_rate': float,
            'team_b_win_rate': float
        }
    """
    team_a_wins = 0
    team_b_wins = 0
    
    for _ in range(simulations):
        # Add some randomness to ratings
        a_sim = random.gauss(team_a_rating, team_a_rating * 0.05)
        b_sim = random.gauss(team_b_rating, team_b_rating * 0.05)
        
        # Determine winner (higher rating wins)
        if a_sim > b_sim:
            team_a_wins += 1
        else:
            team_b_wins += 1
    
    return {
        'team_a_wins': team_a_wins,
        'team_b_wins': team_b_wins,
        'team_a_win_rate': round(team_a_wins / simulations, 4),
        'team_b_win_rate': round(team_b_wins / simulations, 4)
    }
