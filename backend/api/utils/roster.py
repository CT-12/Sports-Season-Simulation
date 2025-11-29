"""
Roster Utility Module

Provides utility functions for fetching team roster data from the database.
This module can be reused across multiple API endpoints.
"""

from django.db import connection
from typing import List, Dict, Any


def fetch_team_roster(team_id: int, season: int = 2025) -> List[Dict[str, Any]]:
    """
    Fetch roster for a specific team from the database.
    
    This is a utility function that can be used by any API endpoint
    that needs team roster data.
    
    Args:
        team_id (int): The team ID
        season (int): Season year (default: 2025)
        
    Returns:
        List[Dict]: List of player dictionaries with id, name, position, and score
                   Returns empty list if fetch fails
    
    Example:
        >>> roster = fetch_team_roster(109, 2025)
        >>> print(roster[0])
        {'id': 660271, 'name': 'Shohei Ohtani', 'position': 'DH', 'score': 85.5}
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
                position_name = row[2] or 'N/A'  # Use position_name directly from database
                
                # Generate temporary score
                score = _generate_player_score(player_id)
                
                players.append({
                    'id': player_id,
                    'name': player_name,
                    'position': position_name,  # Directly from database
                    'score': score
                })
            
            return players
            
    except Exception as e:
        print(f"[Error] Failed to fetch roster for team {team_id}, season {season}: {e}")
        return []


def _generate_player_score(player_id: int) -> float:
    """
    Generate a random score for a player.
    
    Args:
        player_id (int): Player's unique ID (used for random seed)
    
    Returns:
        float: Random score between 40.0 and 100.0
    
    Note:
        This is a temporary placeholder until real player ratings are implemented.
        Uses player_id as seed for consistency across requests.
    """
    import random
    random.seed(player_id)
    score = random.uniform(40.0, 100.0)
    return round(score, 1)


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
