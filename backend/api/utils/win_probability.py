"""
Win Probability Calculation using Logarithmic Methods

This module calculates win probabilities for team matchups using
logarithmic probability model based on Pythagorean ratings.

Note: Elo-based calculations will be implemented in a separate API endpoint.
"""

import math
from typing import Dict, Any


def calculate_log_win_probability(
    team_a_score: float,
    team_b_score: float,
    k: float = 0.1
) -> Dict[str, float]:
    """
    Calculate win probability using logistic function based on Pythagorean scores.
    
    Uses the logistic regression model:
    P(A wins) = 1 / (1 + exp(-k * (score_A - score_B)))
    
    This provides a smooth probability curve that accounts for the
    diminishing returns of large rating differences.
    
    Args:
        team_a_score (float): Team A's Pythagorean rating score
        team_b_score (float): Team B's Pythagorean rating score
        k (float): Sensitivity parameter (default: 0.1)
                  Higher k = more sensitive to score differences
                  Typical range: 0.05 - 0.15
    
    Returns:
        dict: {
            'team_a_win_prob': float (0-100),
            'team_b_win_prob': float (0-100),
            'rating_difference': float
        }
    
    Example:
        >>> probs = calculate_log_win_probability(75.0, 68.0)
        >>> print(f"Team A: {probs['team_a_win_prob']}%")
        Team A: 58.3%
    """
    # Calculate rating difference
    diff = team_a_score - team_b_score
    
    # Logistic function for win probability
    # P(A) = 1 / (1 + e^(-k * diff))
    try:
        exp_term = math.exp(-k * diff)
        prob_a = 1 / (1 + exp_term)
    except OverflowError:
        # Handle extreme differences
        prob_a = 1.0 if diff > 0 else 0.0
    
    prob_b = 1 - prob_a
    
    return {
        'team_a_win_prob': round(prob_a * 100, 2),
        'team_b_win_prob': round(prob_b * 100, 2),
        'rating_difference': round(diff, 2)
    }

