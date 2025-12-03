"""
Player Rating Normalization Module

Calculates standardized player ratings using:
1. ERA+ and OPS+: Traditional baseball statistics (100 = league average)
2. AVG and WHIP normalized: T-Score method (50 = league average, 0-99 scale)

Note: ERA+ and OPS+ are pre-calculated and stored in database.
      AVG_normalized and WHIP_normalized are calculated on-the-fly.
"""

import numpy as np
from django.db import connection
from typing import Dict, Optional


def calculate_normalized_stat(
    value: float,
    stat_type: str,
    season: int = 2025
) -> Optional[int]:
    """
    Calculate T-Score normalized rating for AVG or WHIP.
    
    Args:
        value: Player's stat value
        stat_type: 'AVG' or 'WHIP'
        season: Season year
    
    Returns:
        int: Normalized score (0-99), or None if calculation fails
    
    Example:
        >>> avg_norm = calculate_normalized_stat(0.304, 'AVG', 2025)
        >>> print(avg_norm)
        75
    """
    if value is None:
        return None
    
    # Get league statistics
    league_stats = _get_league_stat(stat_type, season)
    if not league_stats:
        return None
    
    league_mean = league_stats['mean']
    league_std = league_stats['std']
    
    # Handle edge case: std = 0
    if league_std == 0 or league_std is None:
        return 50
    
    # Calculate Z-Score
    z_score = (value - league_mean) / league_std
    
    # Invert for WHIP (lower is better)
    if stat_type == 'WHIP':
        z_score = -z_score
    
    # Convert to T-Score (mean=50, std=10)
    t_score = 50 + (z_score * 10)
    
    # Clip to [0, 99] range
    normalized = int(np.clip(t_score, 0, 99))
    
    return normalized


def _get_league_stat(stat_type: str, season: int) -> Optional[Dict]:
    """
    Get league average and standard deviation for a stat.
    
    Args:
        stat_type: 'AVG' or 'WHIP'
        season: Season year
    
    Returns:
        dict: {'mean': float, 'std': float} or None
    """
    try:
        with connection.cursor() as cursor:
            if stat_type == 'AVG':
                sql = """
                    SELECT 
                        AVG(avg) as mean,
                        STDDEV(avg) as std
                    FROM player_hitting_stats
                    WHERE season = %s AND ab >= 100 AND avg IS NOT NULL
                """
                cursor.execute(sql, [season])
                row = cursor.fetchone()
                if row and row[0]:
                    return {'mean': float(row[0]), 'std': float(row[1]) if row[1] else 0.030}
                return {'mean': 0.250, 'std': 0.030}  # Fallback
            
            elif stat_type == 'WHIP':
                sql = """
                    SELECT 
                        AVG(whip) as mean,
                        STDDEV(whip) as std
                    FROM player_pitching_stats
                    WHERE season = %s AND ip >= 50 AND whip IS NOT NULL
                """
                cursor.execute(sql, [season])
                row = cursor.fetchone()
                if row and row[0]:
                    return {'mean': float(row[0]), 'std': float(row[1]) if row[1] else 0.15}
                return {'mean': 1.30, 'std': 0.15}  # Fallback
    
    except Exception as e:
        print(f"[Error] Failed to get league stats for {stat_type}: {e}")
    
    # Fallback values
    if stat_type == 'AVG':
        return {'mean': 0.250, 'std': 0.030}
    else:  # WHIP
        return {'mean': 1.30, 'std': 0.15}


def _calculate_single_metric_rating(
    value: float,
    league_mean: float,
    league_std: float,
    direction: int
) -> int:
    """
    Calculate T-Score rating for a single metric.
    
    Args:
        value: Player's metric value
        league_mean: League average for this metric
        league_std: League standard deviation for this metric
        direction: 1 for higher is better, -1 for lower is better
    
    Returns:
        int: Rating score (0-99)
    """
    # Handle edge case: std = 0 (all players have same value)
    if league_std == 0 or league_std is None:
        return 50  # Average rating
    
    # Calculate Z-Score
    z_score = (value - league_mean) / league_std
    
    # Invert for metrics where lower is better
    if direction == -1:
        z_score = -z_score
    
    # Convert to T-Score (mean=50, std=10)
    t_score = 50 + (z_score * 10)
    
    # Clip to [0, 99] range and convert to integer
    rating = int(np.clip(t_score, 0, 99))
    
    return rating


def _get_league_hitting_stats(season: int) -> Optional[Dict]:
    """
    Get league-wide hitting statistics for normalization.
    
    Args:
        season: Season year
    
    Returns:
        dict: {
            'AVG': {'mean': float, 'std': float},
            'OPS': {'mean': float, 'std': float}
        }
    """
    try:
        with connection.cursor() as cursor:
            sql = """
                SELECT 
                    AVG(avg) as avg_mean,
                    STDDEV(avg) as avg_std,
                    AVG(ops) as ops_mean,
                    STDDEV(ops) as ops_std
                FROM player_hitting_stats
                WHERE season = %s
                    AND ab >= 100  -- Minimum at-bats for qualified players
            """
            cursor.execute(sql, [season])
            row = cursor.fetchone()
            
            if row and row[0] is not None:
                return {
                    'AVG': {
                        'mean': float(row[0]) if row[0] else 0.250,
                        'std': float(row[1]) if row[1] else 0.030
                    },
                    'OPS': {
                        'mean': float(row[2]) if row[2] else 0.720,
                        'std': float(row[3]) if row[3] else 0.100
                    }
                }
    except Exception as e:
        print(f"[Error] Failed to get league hitting stats: {e}")
    
    # Fallback to typical MLB averages
    return {
        'AVG': {'mean': 0.250, 'std': 0.030},
        'OPS': {'mean': 0.720, 'std': 0.100}
    }


def _get_league_pitching_stats(season: int) -> Optional[Dict]:
    """
    Get league-wide pitching statistics for normalization.
    
    Args:
        season: Season year
    
    Returns:
        dict: {
            'ERA': {'mean': float, 'std': float},
            'WHIP': {'mean': float, 'std': float}
        }
    """
    try:
        with connection.cursor() as cursor:
            sql = """
                SELECT 
                    AVG(era) as era_mean,
                    STDDEV(era) as era_std,
                    AVG(whip) as whip_mean,
                    STDDEV(whip) as whip_std
                FROM player_pitching_stats
                WHERE season = %s
                    AND ip >= 50  -- Minimum innings pitched for qualified pitchers
            """
            cursor.execute(sql, [season])
            row = cursor.fetchone()
            
            if row and row[0] is not None:
                return {
                    'ERA': {
                        'mean': float(row[0]) if row[0] else 4.00,
                        'std': float(row[1]) if row[1] else 0.80
                    },
                    'WHIP': {
                        'mean': float(row[2]) if row[2] else 1.30,
                        'std': float(row[3]) if row[3] else 0.15
                    }
                }
    except Exception as e:
        print(f"[Error] Failed to get league pitching stats: {e}")
    
    # Fallback to typical MLB averages
    return {
        'ERA': {'mean': 4.00, 'std': 0.80},
        'WHIP': {'mean': 1.30, 'std': 0.15}
    }


def calculate_weighted_total_rating(
    ratings: Dict[str, Optional[int]],
    is_pitcher: bool
) -> Optional[int]:
    """
    Calculate weighted total rating from individual metric ratings.
    
    Args:
        ratings: Dictionary with individual metric ratings
        is_pitcher: True if pitcher, False if hitter
    
    Returns:
        int: Weighted total rating (0-99) or None
    """
    if is_pitcher:
        # Pitching metrics
        era_rating = ratings.get('ERA_rating')
        whip_rating = ratings.get('WHIP_rating')
        
        if era_rating is None and whip_rating is None:
            return None
        
        # Use available ratings with their weights
        total_weight = 0
        weighted_sum = 0
        
        if era_rating is not None:
            weighted_sum += era_rating * PITCHING_METRICS_CONFIG['ERA']['weight']
            total_weight += PITCHING_METRICS_CONFIG['ERA']['weight']
        
        if whip_rating is not None:
            weighted_sum += whip_rating * PITCHING_METRICS_CONFIG['WHIP']['weight']
            total_weight += PITCHING_METRICS_CONFIG['WHIP']['weight']
        
        if total_weight > 0:
            return int(np.clip(weighted_sum / total_weight, 0, 99))
    else:
        # Hitting metrics
        avg_rating = ratings.get('AVG_rating')
        ops_rating = ratings.get('OPS_rating')
        
        if avg_rating is None and ops_rating is None:
            return None
        
        # Use available ratings with their weights
        total_weight = 0
        weighted_sum = 0
        
        if avg_rating is not None:
            weighted_sum += avg_rating * HITTING_METRICS_CONFIG['AVG']['weight']
            total_weight += HITTING_METRICS_CONFIG['AVG']['weight']
        
        if ops_rating is not None:
            weighted_sum += ops_rating * HITTING_METRICS_CONFIG['OPS']['weight']
            total_weight += HITTING_METRICS_CONFIG['OPS']['weight']
        
        if total_weight > 0:
            return int(np.clip(weighted_sum / total_weight, 0, 99))
    
    return None
