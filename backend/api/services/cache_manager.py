"""
Cache Manager Service

Manages the "Base State" cache for simulation. This module provides functions to:
1. Serialize player data from the database into a cache-friendly format
2. Retrieve the cached base state (load from cache or refresh from DB)
3. Manage cache expiration and invalidation

The "Load Once, Clone Many" Pattern:
- On first request (or cache miss), query ALL active players and their stats
- Store in Django cache with TTL (e.g., 1 hour)
- Per request: clone this cached data, modify it, and calculate rankings
"""

from django.core.cache import cache
from django.db import connection
from typing import Dict, List, Optional
import json
import logging

logger = logging.getLogger(__name__)

# Cache key for storing the base state
BASE_STATE_CACHE_KEY = "mlb_players_base_state_{season}"

# Default TTL: 1 hour (3600 seconds)
# In production, adjust based on your data update frequency
BASE_STATE_CACHE_TTL = 3600


def serialize_player_data_from_db(season: int) -> Dict[str, List[Dict]]:
    """
    Fetch all active players from the database and serialize into a cache-friendly format.
    
    Structure:
    {
        "Los Angeles Dodgers": [
            {
                "player_id": 123,
                "player_name": "Shohei Ohtani",
                "position": "DH",
                "position_type": "Two-Way Player",
                "hitting_stats": {
                    "avg": 0.285,
                    "ops": 0.825,
                    "hr": 45,
                    "rbi": 120,
                    ...
                },
                "pitching_stats": {
                    "era": 3.14,
                    "whip": 1.05,
                    "so": 250,
                    "w": 15,
                    ...
                }
            },
            ...
        ],
        ...
    }
    
    Args:
        season (int): Season year (e.g., 2025)
    
    Returns:
        Dict[str, List[Dict]]: Team name -> list of player dictionaries
    
    Raises:
        Exception: If database query fails
    """
    try:
        with connection.cursor() as cursor:
            # Query to fetch all player data with stats in a single efficient query
            # This joins players -> hitting_stats and pitching_stats
            sql = """
                SELECT 
                    t.team_name,
                    p.player_id,
                    p.player_name,
                    p.position_name,
                    p.position_type,
                    -- Hitting stats
                    phs.avg,
                    phs.ops,
                    phs.ops_plus,
                    phs.hr,
                    phs.rbi,
                    phs.r,
                    phs.h,
                    phs.obp,
                    phs.slg,
                    -- Pitching stats
                    pps.era,
                    pps.era_plus,
                    pps.whip,
                    pps.so,
                    pps.w,
                    pps.l,
                    pps.bb
                FROM teams t
                JOIN players p ON t.team_id = p.current_team_id 
                    AND t.season = p.season
                LEFT JOIN player_hitting_stats phs ON p.player_id = phs.player_id 
                    AND p.season = phs.season
                LEFT JOIN player_pitching_stats pps ON p.player_id = pps.player_id 
                    AND p.season = pps.season
                WHERE t.season = %s
                ORDER BY t.team_name, p.player_name
            """
            
            cursor.execute(sql, [season])
            rows = cursor.fetchall()
            
            # Get column names
            column_names = [desc[0] for desc in cursor.description]
            
            # Organize data by team
            base_state = {}
            
            for row in rows:
                row_dict = dict(zip(column_names, row))
                
                team_name = row_dict['team_name']
                player_id = row_dict['player_id']
                player_name = row_dict['player_name']
                position = row_dict['position_name']
                position_type = row_dict['position_type']
                
                # Initialize team list if not exists
                if team_name not in base_state:
                    base_state[team_name] = []
                
                # Build hitting stats dict (filter None values)
                hitting_stats = {
                    'avg': row_dict.get('avg'),
                    'ops': row_dict.get('ops'),
                    'ops_plus': row_dict.get('ops_plus'),
                    'hr': row_dict.get('hr'),
                    'rbi': row_dict.get('rbi'),
                    'r': row_dict.get('r'),
                    'h': row_dict.get('h'),
                    'obp': row_dict.get('obp'),
                    'slg': row_dict.get('slg'),
                }
                hitting_stats = {k: v for k, v in hitting_stats.items() if v is not None}
                
                # Build pitching stats dict (filter None values)
                pitching_stats = {
                    'era': row_dict.get('era'),
                    'era_plus': row_dict.get('era_plus'),
                    'whip': row_dict.get('whip'),
                    'so': row_dict.get('so'),
                    'w': row_dict.get('w'),
                    'l': row_dict.get('l'),
                    'bb': row_dict.get('bb'),
                }
                pitching_stats = {k: v for k, v in pitching_stats.items() if v is not None}
                
                # Add player to team list
                player_data = {
                    'player_id': player_id,
                    'player_name': player_name,
                    'position': position,
                    'position_type': position_type,
                    'hitting_stats': hitting_stats,
                    'pitching_stats': pitching_stats,
                }
                
                base_state[team_name].append(player_data)
            
            logger.info(f"Serialized {sum(len(v) for v in base_state.values())} players "
                       f"from {len(base_state)} teams for season {season}")
            return base_state
    
    except Exception as e:
        logger.error(f"Failed to serialize player data for season {season}: {e}")
        import traceback
        traceback.print_exc()
        raise


def get_base_state(season: int, force_refresh: bool = False) -> Dict[str, List[Dict]]:
    """
    Get the "Base State" from cache, or fetch from database if not cached.
    
    Implements the "Load Once, Clone Many" pattern:
    - First request fetches all players from DB and caches them
    - Subsequent requests get cached data
    - Returns a dict that can be safely deep-copied per request
    
    Args:
        season (int): Season year (e.g., 2025)
        force_refresh (bool): If True, bypass cache and fetch from DB
    
    Returns:
        Dict[str, List[Dict]]: Team name -> list of player dictionaries
    
    Raises:
        Exception: If database query fails (only on cache miss/refresh)
    """
    cache_key = BASE_STATE_CACHE_KEY.format(season=season)
    
    if not force_refresh:
        # Try to get from cache first
        cached_data = cache.get(cache_key)
        if cached_data:
            logger.info(f"Base state for season {season} retrieved from cache")
            return cached_data
    
    # Cache miss or force_refresh: fetch from DB
    logger.info(f"Cache miss for season {season} - fetching from database")
    base_state = serialize_player_data_from_db(season)
    
    # Store in cache with TTL
    cache.set(cache_key, base_state, BASE_STATE_CACHE_TTL)
    logger.info(f"Base state for season {season} cached for {BASE_STATE_CACHE_TTL}s")
    
    return base_state


def invalidate_base_state_cache(season: Optional[int] = None):
    """
    Invalidate the base state cache.
    
    Use this when:
    - Player stats are updated in the database
    - A player is traded (moved between teams)
    - New players are added mid-season
    
    Args:
        season (int): Season to invalidate. If None, invalidates all seasons.
    """
    if season is None:
        # Invalidate all season caches (brute force approach)
        # In production, you might want to track all cached seasons
        for year in range(2015, 2030):
            cache_key = BASE_STATE_CACHE_KEY.format(season=year)
            cache.delete(cache_key)
        logger.info("Invalidated all base state caches")
    else:
        cache_key = BASE_STATE_CACHE_KEY.format(season=season)
        cache.delete(cache_key)
        logger.info(f"Invalidated base state cache for season {season}")


def get_cache_info(season: int) -> Dict:
    """
    Get information about the current cache state.
    
    Useful for debugging and monitoring cache effectiveness.
    
    Args:
        season (int): Season year
    
    Returns:
        Dict with cache statistics
    """
    cache_key = BASE_STATE_CACHE_KEY.format(season=season)
    cached_data = cache.get(cache_key)
    
    return {
        "season": season,
        "cache_key": cache_key,
        "is_cached": cached_data is not None,
        "cached_teams": len(cached_data) if cached_data else 0,
        "cached_players": sum(len(v) for v in cached_data.values()) if cached_data else 0,
        "cache_ttl": BASE_STATE_CACHE_TTL,
    }
