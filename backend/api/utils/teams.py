"""
Teams Utility Module

Provides utility functions for fetching team data from the database.
This module can be reused across multiple API endpoints.
"""

from django.db import connection
from typing import List, Dict, Any, Optional


def fetch_all_teams(season: int = 2025) -> List[Dict[str, Any]]:
    """
    Fetch all teams from the database for a specific season.
    
    Args:
        season (int): Season year (default: 2025)
    
    Returns:
        List[Dict]: List of team dictionaries with id and name
                   Returns empty list if query fails
    
    Example:
        >>> teams = fetch_all_teams(2025)
        >>> print(teams[0])
        {'id': 109, 'name': 'Los Angeles Dodgers'}
    """
    try:
        with connection.cursor() as cursor:
            sql = """
                SELECT team_id, team_name
                FROM teams
                WHERE season = %s
                ORDER BY team_name
            """
            cursor.execute(sql, [season])
            rows = cursor.fetchall()
            
            teams = [
                {
                    'id': row[0],
                    'name': row[1]
                }
                for row in rows
            ]
            
            return teams
            
    except Exception as e:
        print(f"[Error] Failed to fetch teams for season {season}: {e}")
        return []


def get_team_by_id(team_id: int, season: int = 2025) -> Optional[Dict[str, Any]]:
    """
    Get a specific team by ID and season.
    
    Args:
        team_id (int): Team ID
        season (int): Season year (default: 2025)
    
    Returns:
        Optional[Dict]: Team dictionary or None if not found
    
    Example:
        >>> team = get_team_by_id(109, 2025)
        >>> print(team['name'])
        'Los Angeles Dodgers'
    """
    try:
        with connection.cursor() as cursor:
            sql = """
                SELECT team_id, team_name
                FROM teams
                WHERE team_id = %s AND season = %s
            """
            cursor.execute(sql, [team_id, season])
            row = cursor.fetchone()
            
            if row:
                return {
                    'id': row[0],
                    'name': row[1]
                }
            return None
            
    except Exception as e:
        print(f"[Error] Failed to fetch team {team_id} for season {season}: {e}")
        return None


def get_team_by_name(team_name: str, season: int = 2025) -> Optional[Dict[str, Any]]:
    """
    Get a team by name (case-insensitive partial match).
    
    Args:
        team_name (str): Team name or partial name
        season (int): Season year (default: 2025)
    
    Returns:
        Optional[Dict]: Team dictionary or None if not found
    
    Example:
        >>> team = get_team_by_name('Dodgers', 2025)
        >>> print(team['id'])
        109
    """
    try:
        with connection.cursor() as cursor:
            sql = """
                SELECT team_id, team_name
                FROM teams
                WHERE LOWER(team_name) LIKE LOWER(%s) AND season = %s
                LIMIT 1
            """
            cursor.execute(sql, [f'%{team_name}%', season])
            row = cursor.fetchone()
            
            if row:
                return {
                    'id': row[0],
                    'name': row[1]
                }
            return None
            
    except Exception as e:
        print(f"[Error] Failed to fetch team by name '{team_name}': {e}")
        return None
