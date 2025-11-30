"""
Elo Rating Utility Module

Provides utility functions for working with Elo ratings:
- Fetch team's current/historical Elo rating
- Calculate Elo-based win probability
- Convert Elo ratings to display scores (0-100 scale)
"""

from django.db import connection
from typing import Dict, Any, Optional
from decimal import Decimal
from datetime import date, datetime


def get_team_elo_rating(
    team_id: int,
    target_date: date = None,
    season: int = None
) -> Optional[Decimal]:
    """
    取得球隊在特定日期的 Elo 評分
    
    Args:
        team_id: 球隊 ID
        target_date: 查詢日期 (預設今天)
        season: 賽季 (可選，用於加速查詢)
    
    Returns:
        Decimal: Elo 評分，如果找不到則返回 None
    
    Example:
        >>> rating = get_team_elo_rating(109, date(2025, 10, 1))
        >>> print(rating)
        Decimal('1625.5432')
    """
    if target_date is None:
        target_date = date.today()
    
    try:
        with connection.cursor() as cursor:
            # 查詢該日期或之前最接近的評分
            if season:
                sql = """
                    SELECT rating
                    FROM team_elo_history
                    WHERE team_id = %s 
                        AND season = %s
                        AND date <= %s
                    ORDER BY date DESC
                    LIMIT 1
                """
                cursor.execute(sql, [team_id, season, target_date])
            else:
                sql = """
                    SELECT rating
                    FROM team_elo_history
                    WHERE team_id = %s AND date <= %s
                    ORDER BY date DESC
                    LIMIT 1
                """
                cursor.execute(sql, [team_id, target_date])
            
            row = cursor.fetchone()
            if row:
                return Decimal(str(row[0]))
            return None
            
    except Exception as e:
        print(f"[Error] Failed to fetch Elo rating for team {team_id}: {e}")
        return None


def calculate_elo_win_probability(
    rating_a: Decimal,
    rating_b: Decimal
) -> Dict[str, float]:
    """
    根據 Elo 評分計算對戰勝率
    
    使用標準 Elo 勝率公式：
    P(A wins) = 1 / (1 + 10^((Rb - Ra) / 400))
    
    Args:
        rating_a: 球隊 A 的 Elo 評分
        rating_b: 球隊 B 的 Elo 評分
    
    Returns:
        dict: {
            'team_a_win_prob': float (0-100),
            'team_b_win_prob': float (0-100)
        }
    
    Example:
        >>> probs = calculate_elo_win_probability(Decimal('1600'), Decimal('1500'))
        >>> print(probs['team_a_win_prob'])
        64.01
    """
    # 轉換為 float 進行計算
    ra = float(rating_a)
    rb = float(rating_b)
    
    # Elo 勝率公式
    prob_a = 1 / (1 + 10 ** ((rb - ra) / 400))
    prob_b = 1 - prob_a
    
    return {
        'team_a_win_prob': round(prob_a * 100, 2),
        'team_b_win_prob': round(prob_b * 100, 2)
    }


def convert_elo_to_display_score(
    rating_a: Decimal,
    rating_b: Decimal
) -> Dict[str, float]:
    """
    將 Elo 評分轉換為 0-100 的顯示分數
    
    使用相對評分方式：將兩隊評分映射到 0-100 範圍
    同時保持相對實力差距
    
    Args:
        rating_a: 球隊 A 的 Elo 評分
        rating_b: 球隊 B 的 Elo 評分
    
    Returns:
        dict: {
            'team_a_score': float (0-100),
            'team_b_score': float (0-100)
        }
    
    Example:
        >>> scores = convert_elo_to_display_score(Decimal('1600'), Decimal('1500'))
        >>> print(scores)
        {'team_a_score': 61.54, 'team_b_score': 57.69}
    
    Note:
        使用公式：score = (rating - 1200) / 600 * 100
        假設合理的 Elo 範圍是 1200-1800
    """
    # Elo 評分通常在 1200-1800 之間
    MIN_ELO = 1200
    MAX_ELO = 1800
    
    def elo_to_score(rating: Decimal) -> float:
        """將 Elo 評分轉換為 0-100 分數"""
        r = float(rating)
        # 限制在合理範圍內
        r = max(MIN_ELO, min(MAX_ELO, r))
        # 線性映射到 0-100
        score = ((r - MIN_ELO) / (MAX_ELO - MIN_ELO)) * 100
        return round(score, 2)
    
    return {
        'team_a_score': elo_to_score(rating_a),
        'team_b_score': elo_to_score(rating_b)
    }


def get_elo_rating_with_fallback(
    team_id: int,
    target_date: date = None,
    season: int = None,
    default_rating: int = 1500
) -> Decimal:
    """
    取得 Elo 評分，如果找不到則返回預設值
    
    Args:
        team_id: 球隊 ID
        target_date: 查詢日期
        season: 賽季
        default_rating: 預設評分 (如果找不到)
    
    Returns:
        Decimal: Elo 評分
    """
    rating = get_team_elo_rating(team_id, target_date, season)
    if rating is None:
        return Decimal(default_rating)
    return rating


def get_season_elo_range(team_id: int, season: int) -> Dict[str, Any]:
    """
    取得球隊在某賽季的 Elo 評分範圍
    
    Args:
        team_id: 球隊 ID
        season: 賽季年份
    
    Returns:
        dict: {
            'min_rating': Decimal,
            'max_rating': Decimal,
            'season_start': Decimal,
            'season_end': Decimal,
            'average': Decimal
        }
    """
    try:
        with connection.cursor() as cursor:
            sql = """
                SELECT 
                    MIN(rating) as min_rating,
                    MAX(rating) as max_rating,
                    AVG(rating) as avg_rating
                FROM team_elo_history
                WHERE team_id = %s AND season = %s
            """
            cursor.execute(sql, [team_id, season])
            row = cursor.fetchone()
            
            if not row:
                return None
            
            # 取得季初和季末評分
            cursor.execute("""
                SELECT rating FROM team_elo_history
                WHERE team_id = %s AND season = %s
                ORDER BY date ASC LIMIT 1
            """, [team_id, season])
            season_start = cursor.fetchone()
            
            cursor.execute("""
                SELECT rating FROM team_elo_history
                WHERE team_id = %s AND season = %s
                ORDER BY date DESC LIMIT 1
            """, [team_id, season])
            season_end = cursor.fetchone()
            
            return {
                'min_rating': Decimal(str(row[0])) if row[0] else None,
                'max_rating': Decimal(str(row[1])) if row[1] else None,
                'average': Decimal(str(row[2])) if row[2] else None,
                'season_start': Decimal(str(season_start[0])) if season_start else None,
                'season_end': Decimal(str(season_end[0])) if season_end else None
            }
            
    except Exception as e:
        print(f"[Error] Failed to get Elo range for team {team_id}, season {season}: {e}")
        return None
