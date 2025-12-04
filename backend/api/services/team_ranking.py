"""
Team Ranking Service

This module provides functionality to rank MLB teams based on a combination of
hitter and pitcher metrics using Z-score normalization.

Features:
- Aggregate hitting and pitching stats by team
- Normalize metrics using Z-scores (handles different scales and directions)
- Rank teams by combined score
- Split results by league (AL/NL)
"""

from django.db import connection
from typing import Dict, List, Optional, Tuple
import statistics


# MLB Team to League Mapping
# Maps standard team names to their league (AL or NL)
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
    "Oakland Athletics": "AL",
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

# Metrics configuration: whether higher is better (True) or lower is better (False)
METRIC_DIRECTION = {
    # Hitting metrics (higher is better)
    "avg": True,      # Batting Average
    "ops": True,      # On-base Plus Slugging
    "ops_plus": True, # On-base Plus Slugging Plus (advanced metric, scaled to 100)
    "hr": True,       # Home Runs
    "rbi": True,      # Runs Batted In
    "r": True,        # Runs
    "h": True,        # Hits
    "obp": True,      # On-Base Percentage
    "slg": True,      # Slugging Percentage
    
    # Pitching metrics (lower is better)
    "era": False,     # Earned Run Average
    "whip": False,    # Walks + Hits per Innings Pitched
    "l": False,       # Losses
    "bb": False,      # Walks
    
    # Pitching metrics (higher is better)
    "so": True,       # Strikeouts
    "w": True,        # Wins
    "era_plus": True, # ERA Plus (advanced metric, scaled to 100, higher is better)
}


def get_latest_season() -> int:
    """
    Get the latest available season from the database.
    
    Returns:
        int: Latest season year (e.g., 2025)
    
    Raises:
        Exception: If no seasons are found
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT MAX(season) FROM teams
            """)
            result = cursor.fetchone()
            season = result[0] if result and result[0] else 2025
            return int(season)
    except Exception as e:
        print(f"[Error] Failed to get latest season: {e}")
        return 2025


def aggregate_team_hitting_stats(
    metric: str,
    season: Optional[int] = None
) -> Dict[str, float]:
    """
    Aggregate hitting statistics by team for all players.
    
    Args:
        metric (str): Metric to aggregate (e.g., "avg", "ops", "hr", "rbi")
        season (int): Season year. If None, uses latest season.
    
    Returns:
        Dict[str, float]: Mapping of team_name to average metric value
                         Only includes teams with hitting stats
    
    Example:
        >>> stats = aggregate_team_hitting_stats("ops", season=2025)
        >>> print(stats["Los Angeles Dodgers"])
        0.785
    """
    if season is None:
        season = get_latest_season()
    
    try:
        with connection.cursor() as cursor:
            # Query to aggregate hitting stats
            # Join teams -> players -> player_hitting_stats
            sql = f"""
                SELECT 
                    t.team_name,
                    AVG(CAST(phs.{metric} AS FLOAT)) as avg_metric
                FROM teams t
                JOIN players p ON t.team_id = p.current_team_id 
                    AND t.season = p.season
                JOIN player_hitting_stats phs ON p.player_id = phs.player_id 
                    AND p.season = phs.season
                WHERE t.season = %s
                    AND p.position_type IN ('Outfielder', 'Catcher', 'Infielder', 'Hitter', 'Two-Way Player')
                    AND phs.{metric} IS NOT NULL
                    AND phs.{metric} > 0
                GROUP BY t.team_name
            """
            
            cursor.execute(sql, [season])
            rows = cursor.fetchall()
            
            result = {}
            for row in rows:
                team_name, avg_value = row
                result[team_name] = float(avg_value) if avg_value else 0.0
            
            return result
    
    except Exception as e:
        print(f"[Error] Failed to aggregate hitting stats for {metric}: {e}")
        import traceback
        traceback.print_exc()
        return {}


def aggregate_team_pitching_stats(
    metric: str,
    season: Optional[int] = None
) -> Dict[str, float]:
    """
    Aggregate pitching statistics by team for all players.
    
    Args:
        metric (str): Metric to aggregate (e.g., "era", "whip", "so", "w", "l")
        season (int): Season year. If None, uses latest season.
    
    Returns:
        Dict[str, float]: Mapping of team_name to average metric value
                         Only includes teams with pitching stats
    
    Example:
        >>> stats = aggregate_team_pitching_stats("era", season=2025)
        >>> print(stats["Los Angeles Dodgers"])
        3.52
    """
    if season is None:
        season = get_latest_season()
    
    try:
        with connection.cursor() as cursor:
            # Query to aggregate pitching stats
            # Join teams -> players -> player_pitching_stats
            sql = f"""
                SELECT 
                    t.team_name,
                    AVG(CAST(pps.{metric} AS FLOAT)) as avg_metric
                FROM teams t
                JOIN players p ON t.team_id = p.current_team_id 
                    AND t.season = p.season
                JOIN player_pitching_stats pps ON p.player_id = pps.player_id 
                    AND p.season = pps.season
                WHERE t.season = %s
                    AND p.position_type = 'Pitcher'
                    AND pps.{metric} IS NOT NULL
                    AND pps.{metric} > 0
                GROUP BY t.team_name
            """
            
            cursor.execute(sql, [season])
            rows = cursor.fetchall()
            
            result = {}
            for row in rows:
                team_name, avg_value = row
                result[team_name] = float(avg_value) if avg_value else 0.0
            
            return result
    
    except Exception as e:
        print(f"[Error] Failed to aggregate pitching stats for {metric}: {e}")
        import traceback
        traceback.print_exc()
        return {}


def calculate_z_score(value: float, mean: float, std_dev: float) -> float:
    """
    Calculate Z-score for a value.
    
    Formula: z = (x - mean) / std_dev
    
    Args:
        value (float): The value to normalize
        mean (float): Mean of the distribution
        std_dev (float): Standard deviation of the distribution
    
    Returns:
        float: Z-score (can be negative, zero, or positive)
               Returns 0 if std_dev is 0 (no variation)
    
    Example:
        >>> z = calculate_z_score(0.800, 0.750, 0.030)
        >>> print(z)
        1.667
    """
    if std_dev == 0:
        # No variation in data, return 0 (neutral score)
        return 0.0
    return (value - mean) / std_dev


def normalize_z_score_by_direction(z_score: float, metric: str) -> float:
    """
    Adjust Z-score based on metric direction.
    
    For "lower is better" metrics (ERA, WHIP, L), flip the sign so
    higher Z-scores always represent better performance.
    
    Args:
        z_score (float): The calculated Z-score
        metric (str): Metric name (used to look up direction)
    
    Returns:
        float: Adjusted Z-score (flipped if metric is negative-is-better)
    
    Example:
        >>> # For ERA (lower is better), flip the score
        >>> adjusted = normalize_z_score_by_direction(-0.5, "era")
        >>> print(adjusted)
        0.5
    """
    is_positive = METRIC_DIRECTION.get(metric, True)
    
    # If higher is better, keep as-is
    if is_positive:
        return z_score
    # If lower is better, flip the sign
    else:
        return -z_score


def rank_teams_from_aggregated_stats(
    hitting_stats: Dict[str, float],
    pitching_stats: Dict[str, float],
    hitter_metric: str,
    pitcher_metric: str
) -> Dict[str, List[Tuple[str, float]]]:
    """
    Rank teams using pre-aggregated statistics (from DB or memory).
    
    This is the core algorithm extracted to work with any data source.
    
    Algorithm:
    1. Calculate Z-scores for each metric
    2. Normalize Z-scores by direction
    3. Combine scores: final_score = z_hitter + z_pitcher
    4. Sort teams and split by league
    
    Args:
        hitting_stats (Dict[str, float]): Team -> average hitter metric
        pitching_stats (Dict[str, float]): Team -> average pitcher metric
        hitter_metric (str): Hitter metric name (for direction lookup)
        pitcher_metric (str): Pitcher metric name (for direction lookup)
    
    Returns:
        Dict with structure:
        {
            "AL": [("Team Name", score), ...],
            "NL": [("Team Name", score), ...]
        }
        Sorted by score descending within each league.
    
    Raises:
        ValueError: If no teams found in either stats dict
    """
    if not hitting_stats or not pitching_stats:
        raise ValueError(
            f"Empty stats provided. "
            f"Hitting: {len(hitting_stats)}, Pitching: {len(pitching_stats)}"
        )
    
    # Calculate league statistics (mean, std_dev)
    hitter_values = list(hitting_stats.values())
    pitcher_values = list(pitching_stats.values())
    
    hitter_mean = statistics.mean(hitter_values) if hitter_values else 0
    pitcher_mean = statistics.mean(pitcher_values) if pitcher_values else 0
    
    hitter_std = statistics.stdev(hitter_values) if len(hitter_values) > 1 else 0
    pitcher_std = statistics.stdev(pitcher_values) if len(pitcher_values) > 1 else 0
    
    # Calculate combined scores
    team_scores = {}
    
    for team_name in hitting_stats.keys():
        # Get stats (default to mean if team has no pitching stats)
        hitter_value = hitting_stats.get(team_name, hitter_mean)
        pitcher_value = pitching_stats.get(team_name, pitcher_mean)
        
        # Calculate Z-scores
        hitter_z = calculate_z_score(hitter_value, hitter_mean, hitter_std)
        pitcher_z = calculate_z_score(pitcher_value, pitcher_mean, pitcher_std)
        
        # Normalize by direction
        hitter_z = normalize_z_score_by_direction(hitter_z, hitter_metric)
        pitcher_z = normalize_z_score_by_direction(pitcher_z, pitcher_metric)
        
        # Combine scores
        final_score = hitter_z + pitcher_z
        team_scores[team_name] = final_score
    
    # Sort and split by league
    sorted_teams = sorted(
        team_scores.items(),
        key=lambda x: x[1],
        reverse=True
    )
    
    result = {"AL": [], "NL": []}
    
    for team_name, score in sorted_teams:
        league = TEAM_LEAGUE_MAP.get(team_name, "NL")  # Default to NL if not found
        result[league].append((team_name, round(score, 3)))
    
    return result


def get_ranking_with_details_from_aggregated_stats(
    hitting_stats: Dict[str, float],
    pitching_stats: Dict[str, float],
    hitter_metric: str,
    pitcher_metric: str,
    season: int
) -> Dict:
    """
    Get detailed ranking using pre-aggregated statistics (from DB or memory).
    
    This is the detailed version of rank_teams_from_aggregated_stats.
    
    Args:
        hitting_stats (Dict[str, float]): Team -> average hitter metric
        pitching_stats (Dict[str, float]): Team -> average pitcher metric
        hitter_metric (str): Hitter metric name
        pitcher_metric (str): Pitcher metric name
        season (int): Season year
    
    Returns:
        Dict with structure:
        {
            "season": int,
            "hitter_metric": str,
            "pitcher_metric": str,
            "AL": [{...}, ...],
            "NL": [{...}, ...]
        }
    """
    if not hitting_stats or not pitching_stats:
        raise ValueError("Empty stats provided")
    
    # Calculate league statistics
    hitter_values = list(hitting_stats.values())
    pitcher_values = list(pitching_stats.values())
    
    hitter_mean = statistics.mean(hitter_values)
    pitcher_mean = statistics.mean(pitcher_values)
    hitter_std = statistics.stdev(hitter_values) if len(hitter_values) > 1 else 0
    pitcher_std = statistics.stdev(pitcher_values) if len(pitcher_values) > 1 else 0
    
    # Build detailed results
    team_details = []
    
    for team_name in hitting_stats.keys():
        hitter_value = hitting_stats.get(team_name, hitter_mean)
        pitcher_value = pitching_stats.get(team_name, pitcher_mean)
        
        # Calculate Z-scores
        hitter_z = calculate_z_score(hitter_value, hitter_mean, hitter_std)
        pitcher_z = calculate_z_score(pitcher_value, pitcher_mean, pitcher_std)
        
        # Normalize
        hitter_z_norm = normalize_z_score_by_direction(hitter_z, hitter_metric)
        pitcher_z_norm = normalize_z_score_by_direction(pitcher_z, pitcher_metric)
        
        final_score = hitter_z_norm + pitcher_z_norm
        
        team_details.append({
            "team_name": team_name,
            "score": round(final_score, 3),
            "hitter_value": round(hitter_value, 4),
            "pitcher_value": round(pitcher_value, 4),
            "hitter_z_score": round(hitter_z_norm, 3),
            "pitcher_z_score": round(pitcher_z_norm, 3)
        })
    
    # Sort and split by league with ranking
    sorted_teams = sorted(team_details, key=lambda x: x["score"], reverse=True)
    
    result = {
        "season": season,
        "hitter_metric": hitter_metric,
        "pitcher_metric": pitcher_metric,
        "AL": [],
        "NL": []
    }
    
    al_rank = 1
    nl_rank = 1
    
    for team_detail in sorted_teams:
        team_name = team_detail["team_name"]
        league = TEAM_LEAGUE_MAP.get(team_name, "NL")
        
        if league == "AL":
            team_detail["rank"] = al_rank
            result["AL"].append(team_detail)
            al_rank += 1
        else:
            team_detail["rank"] = nl_rank
            result["NL"].append(team_detail)
            nl_rank += 1
    
    return result


def rank_teams_by_metrics(
    hitter_metric: str,
    pitcher_metric: str,
    season: Optional[int] = None
) -> Dict[str, List[Tuple[str, float]]]:
    """
    Rank all teams by a combination of hitter and pitcher metrics (from database).
    
    This is a convenience wrapper that queries the DB and delegates to
    rank_teams_from_aggregated_stats for the actual ranking logic.
    
    Args:
        hitter_metric (str): Hitter metric (e.g., "ops", "avg", "hr", "rbi")
        pitcher_metric (str): Pitcher metric (e.g., "era", "whip", "so")
        season (int): Season year. If None, uses latest season.
    
    Returns:
        Dict with structure:
        {
            "AL": [("Team Name", score), ...],
            "NL": [("Team Name", score), ...]
        }
        Sorted by score descending within each league.
    
    Raises:
        ValueError: If invalid metrics provided
    
    Example:
        >>> result = rank_teams_by_metrics("ops", "era", season=2025)
        >>> print(result["AL"][0])
        ("New York Yankees", 2.45)
    """
    # Validate metrics
    if hitter_metric not in METRIC_DIRECTION:
        raise ValueError(f"Unknown hitter metric: {hitter_metric}")
    if pitcher_metric not in METRIC_DIRECTION:
        raise ValueError(f"Unknown pitcher metric: {pitcher_metric}")
    
    if season is None:
        season = get_latest_season()
    
    # Aggregate stats from database
    hitting_stats = aggregate_team_hitting_stats(hitter_metric, season)
    pitching_stats = aggregate_team_pitching_stats(pitcher_metric, season)
    
    if not hitting_stats or not pitching_stats:
        raise Exception(
            f"Failed to fetch stats. "
            f"Hitting stats found: {len(hitting_stats)}, "
            f"Pitching stats found: {len(pitching_stats)}"
        )
    
    # Delegate to core ranking logic
    return rank_teams_from_aggregated_stats(
        hitting_stats,
        pitching_stats,
        hitter_metric,
        pitcher_metric
    )


def get_ranking_with_details(
    hitter_metric: str,
    pitcher_metric: str,
    season: Optional[int] = None
) -> Dict:
    """
    Get detailed ranking information from database.
    
    This is a convenience wrapper that queries the DB and delegates to
    get_ranking_with_details_from_aggregated_stats for the actual logic.
    
    Args:
        hitter_metric (str): Hitter metric
        pitcher_metric (str): Pitcher metric
        season (int): Season year
    
    Returns:
        Dict with structure:
        {
            "season": int,
            "hitter_metric": str,
            "pitcher_metric": str,
            "AL": [{...}, ...],
            "NL": [{...}, ...]
        }
    
    Example:
        >>> details = get_ranking_with_details("ops", "era", season=2025)
        >>> print(details["AL"][0])
    """
    if season is None:
        season = get_latest_season()
    
    # Validate metrics
    if hitter_metric not in METRIC_DIRECTION:
        raise ValueError(f"Unknown hitter metric: {hitter_metric}")
    if pitcher_metric not in METRIC_DIRECTION:
        raise ValueError(f"Unknown pitcher metric: {pitcher_metric}")
    
    # Get stats from database
    hitting_stats = aggregate_team_hitting_stats(hitter_metric, season)
    pitching_stats = aggregate_team_pitching_stats(pitcher_metric, season)
    
    if not hitting_stats or not pitching_stats:
        raise Exception("Failed to fetch stats")
    
    # Delegate to core logic
    return get_ranking_with_details_from_aggregated_stats(
        hitting_stats,
        pitching_stats,
        hitter_metric,
        pitcher_metric,
        season
    )
