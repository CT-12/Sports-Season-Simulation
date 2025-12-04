"""
Roster Utility Module

Provides utility functions for fetching team roster data from the database.
This module can be reused across multiple API endpoints.
"""

from django.db import connection
from typing import List, Dict, Any, Optional


def fetch_team_roster(team_id: int, season: int = 2025) -> List[Dict[str, Any]]:
    """
    Fetch roster for a specific team from the database with player statistics.
    
    This is a utility function that can be used by any API endpoint
    that needs team roster data.
    
    Args:
        team_id (int): The team ID
        season (int): Season year (default: 2025)
        
    Returns:
        List[Dict]: List of player dictionaries with id, name, position, and Rating
                   Returns empty list if fetch fails
    
    Example:
        >>> roster = fetch_team_roster(109, 2025)
        >>> print(roster[0])
        {
            'id': 660271, 
            'name': 'Shohei Ohtani', 
            'position': 'DH', 
            'Rating': {'AVG': 0.304, 'OPS': 1.036, 'ERA': None, 'WHIP': None}
        }
    """
    try:
        with connection.cursor() as cursor:
            sql = """
                SELECT 
                    player_id,
                    player_name,
                    position_name,
                    position_type
                FROM players
                WHERE current_team_id = %s AND season = %s
                ORDER BY 
                    CASE position_type
                        WHEN 'Pitcher' THEN 1
                        WHEN 'Catcher' THEN 2
                        WHEN 'Infielder' THEN 3
                        WHEN 'Outfielder' THEN 4
                        ELSE 5
                    END,
                    position_name
            """
            cursor.execute(sql, [team_id, season])
            rows = cursor.fetchall()
            
            players = []
            for row in rows:
                player_id = row[0]
                player_name = row[1]
                position_name = row[2] or 'N/A'
                position_type = row[3]
                
                # Get player rating based on position type
                # Pass player_name for special handling (e.g., Shohei Ohtani)
                rating = _get_player_rating(player_id, season, position_type, player_name)
                
                # Ensure all Rating values are JSON-serializable
                # Convert None to null, Decimal to float
                json_safe_rating = {}
                for key, value in rating.items():
                    if value is None:
                        json_safe_rating[key] = None
                    elif isinstance(value, (int, float)):
                        json_safe_rating[key] = value
                    else:
                        # Convert Decimal or other types to float
                        try:
                            json_safe_rating[key] = float(value)
                        except (TypeError, ValueError):
                            json_safe_rating[key] = value
                
                players.append({
                    'id': player_id,
                    'name': player_name,
                    'position': position_name,
                    'Rating': json_safe_rating
                })
            
            return players
            
    except Exception as e:
        print(f"[Error] Failed to fetch roster for team {team_id}, season {season}: {e}")
        return []


def _get_player_rating(player_id: int, season: int, position_type: str, player_name: str = '') -> Dict[str, Optional[float]]:
    """
    Get player rating from database based on position type.
    
    Args:
        player_id (int): Player's unique ID
        season (int): Season year
        position_type (str): Position type ('Pitcher', 'Catcher', 'Infielder', 'Outfielder')
        player_name (str): Player name for special handling (e.g., Shohei Ohtani)
    
    Returns:
        dict: {
            'AVG': float or None,
            'OPS': float or None,
            'ERA': float or None,
            'WHIP': float or None,
            'AVG_normalized': int or None,      # T-Score (0-99)
            'OPS_plus': int or None,             # OPS+ (100 = average)
            'ERA_plus': int or None,             # ERA+ (100 = average)
            'WHIP_normalized': int or None       # T-Score (0-99)
        }
    
    Note:
        - Pitchers: ERA, WHIP, ERA+ (from DB), WHIP_normalized (calculated)
        - Others: AVG, OPS, AVG_normalized (calculated), OPS+ (from DB)
        - Special: Shohei Ohtani gets stats from both tables
        - *_plus stats are pre-calculated and stored in DB
        - *_normalized stats are calculated using T-Score method
    """
    from ..utils.player_rating import calculate_normalized_stat
    
    rating = {
        'AVG': None,
        'OPS': None,
        'ERA': None,
        'WHIP': None,
        'AVG_normalized': None,
        'OPS_plus': None,
        'ERA_plus': None,
        'WHIP_normalized': None
    }
    
    try:
        with connection.cursor() as cursor:
            # Special handling for Shohei Ohtani (two-way player)
            if 'Shohei Ohtani' in player_name or 'Ohtani' in player_name:
                # Get pitching stats with ERA+
                sql_pitching = """
                    SELECT era, whip, era_plus
                    FROM player_pitching_stats
                    WHERE player_id = %s AND season = %s
                    LIMIT 1
                """
                cursor.execute(sql_pitching, [player_id, season])
                row_pitching = cursor.fetchone()
                
                if row_pitching:
                    rating['ERA'] = float(row_pitching[0]) if row_pitching[0] is not None else None
                    rating['WHIP'] = float(row_pitching[1]) if row_pitching[1] is not None else None
                    rating['ERA_plus'] = int(row_pitching[2]) if row_pitching[2] is not None else None
                    
                    # Calculate WHIP_normalized
                    if rating['WHIP'] is not None:
                        rating['WHIP_normalized'] = calculate_normalized_stat(
                            rating['WHIP'], 'WHIP', season
                        )
                
                # Get hitting stats with OPS+
                sql_hitting = """
                    SELECT avg, ops, ops_plus
                    FROM player_hitting_stats
                    WHERE player_id = %s AND season = %s
                    LIMIT 1
                """
                cursor.execute(sql_hitting, [player_id, season])
                row_hitting = cursor.fetchone()
                
                if row_hitting:
                    rating['AVG'] = float(row_hitting[0]) if row_hitting[0] is not None else None
                    rating['OPS'] = float(row_hitting[1]) if row_hitting[1] is not None else None
                    rating['OPS_plus'] = int(row_hitting[2]) if row_hitting[2] is not None else None
                    
                    # Calculate AVG_normalized
                    if rating['AVG'] is not None:
                        rating['AVG_normalized'] = calculate_normalized_stat(
                            rating['AVG'], 'AVG', season
                        )
            
            elif position_type == 'Pitcher':
                # Regular pitcher: ERA+, WHIP_normalized
                sql = """
                    SELECT era, whip, era_plus
                    FROM player_pitching_stats
                    WHERE player_id = %s AND season = %s
                    LIMIT 1
                """
                cursor.execute(sql, [player_id, season])
                row = cursor.fetchone()
                
                if row:
                    rating['ERA'] = float(row[0]) if row[0] is not None else None
                    rating['WHIP'] = float(row[1]) if row[1] is not None else None
                    rating['ERA_plus'] = int(row[2]) if row[2] is not None else None
                    
                    # Calculate WHIP_normalized
                    if rating['WHIP'] is not None:
                        rating['WHIP_normalized'] = calculate_normalized_stat(
                            rating['WHIP'], 'WHIP', season
                        )
            else:
                # Regular hitter: OPS+, AVG_normalized
                sql = """
                    SELECT avg, ops, ops_plus
                    FROM player_hitting_stats
                    WHERE player_id = %s AND season = %s
                    LIMIT 1
                """
                cursor.execute(sql, [player_id, season])
                row = cursor.fetchone()
                
                if row:
                    rating['AVG'] = float(row[0]) if row[0] is not None else None
                    rating['OPS'] = float(row[1]) if row[1] is not None else None
                    rating['OPS_plus'] = int(row[2]) if row[2] is not None else None
                    
                    # Calculate AVG_normalized
                    if rating['AVG'] is not None:
                        rating['AVG_normalized'] = calculate_normalized_stat(
                            rating['AVG'], 'AVG', season
                        )
    
    except Exception as e:
        print(f"[Error] Failed to fetch rating for player {player_id}: {e}")
    
    return rating


def get_player_by_id(player_id: int, season: int = 2025) -> Dict[str, Any]:
    """
    Get a specific player by ID and season.
    
    Args:
        player_id (int): Player ID
        season (int): Season year (default: 2025)
    
    Returns:
        Optional[Dict]: Player dictionary or None if not found
    """
    try:
        with connection.cursor() as cursor:
            sql = """
                SELECT 
                    player_id,
                    player_name,
                    current_team_id,
                    position_name,
                    position_type
                FROM players
                WHERE player_id = %s AND season = %s
            """
            cursor.execute(sql, [player_id, season])
            row = cursor.fetchone()
            
            if row:
                return {
                    'id': row[0],
                    'name': row[1],
                    'team_id': row[2],
                    'position': row[3] or 'N/A',  # Use position_name directly
                    'position_type': row[4]
                }
            return None
            
    except Exception as e:
        print(f"[Error] Failed to fetch player {player_id}, season {season}: {e}")
        return None


def get_team_roster_count(team_id: int, season: int = 2025) -> int:
    """
    Get the number of players on a team's roster.
    
    Args:
        team_id (int): Team ID
        season (int): Season year (default: 2025)
    
    Returns:
        int: Number of players on the roster
    """
    try:
        with connection.cursor() as cursor:
            sql = """
                SELECT COUNT(*)
                FROM players
                WHERE current_team_id = %s AND season = %s
            """
            cursor.execute(sql, [team_id, season])
            count = cursor.fetchone()[0]
            return count
            
    except Exception as e:
        print(f"[Error] Failed to count roster for team {team_id}: {e}")
        return 0
