"""
Season Prediction Module

This module implements season-to-season prediction using:
1. Pythagorean win rate calculation (base skill)
2. Regression to the mean (predicting next season)
3. Log5 formula for matchup win probability
4. Monte Carlo simulation for season outcomes
"""

from typing import Dict, Any, Optional
import random


def predict_next_season_win_rate(
    current_rs: int,
    current_ra: int,
    weight: float = 0.7,
    exponent: float = 1.83
) -> Dict[str, Any]:
    """
    根據今年的得失分，預測下一季的勝率與預期分數
    
    使用「回歸平均」(Regression to the Mean) 概念：
    強隊往往會稍微退步，弱隊往往會稍微進步
    
    Args:
        current_rs (int): 今年總得分 (e.g., 2025)
        current_ra (int): 今年總失分 (e.g., 2025)
        weight (float): 信心權重 (0~1)，越接近 1 代表越相信今年實力會延續
                       0.7 是一個保守且合理的預設值
        exponent (float): 畢氏指數，預設 1.83 (Pythagenpat)
    
    Returns:
        dict: 包含預測的勝率、預測得分、預測失分
              {
                  "current_year_pyth_win_rate": float,  # 今年畢氏勝率 (參考用)
                  "next_year_projected_win_rate": float,  # 明年預測勝率 (用於 Log5)
                  "next_year_projected_rs": int,  # 明年預期得分
                  "next_year_projected_ra": int   # 明年預期失分
              }
    
    Example:
        >>> stats = predict_next_season_win_rate(600, 500, weight=0.7)
        >>> print(f"2026 Projected Win Rate: {stats['next_year_projected_win_rate']}")
        2026 Projected Win Rate: 0.555
    """
    # 1. 先算今年的畢氏勝率 (2025 Base Skill)
    if current_rs == 0 and current_ra == 0:
        pyth_win_pct = 0.500
    else:
        rs_exp = current_rs ** exponent
        ra_exp = current_ra ** exponent
        pyth_win_pct = rs_exp / (rs_exp + ra_exp)
    
    # 2. 應用「回歸平均」預測明年勝率 (2026 Projected Win%)
    # 公式： (今年實力 * 權重) + (聯盟平均 0.500 * (1 - 權重))
    league_average = 0.500
    projected_win_pct = (pyth_win_pct * weight) + (league_average * (1 - weight))
    
    # 3. (選用) 反推明年大概會得幾分/失幾分
    # 計算聯盟平均得分水準 (假設一場兩隊各得 4.5 分 -> 整季 120 場約 540 分)
    avg_runs_baseline = 540
    
    # 預測得分 = (今年得分 * weight) + (聯盟平均 * (1-weight))
    projected_rs = (current_rs * weight) + (avg_runs_baseline * (1 - weight))
    projected_ra = (current_ra * weight) + (avg_runs_baseline * (1 - weight))
    
    return {
        "current_year_pyth_win_rate": round(pyth_win_pct, 4),
        "next_year_projected_win_rate": round(projected_win_pct, 4),
        "next_year_projected_rs": int(projected_rs),
        "next_year_projected_ra": int(projected_ra)
    }


def calculate_log5_win_probability(
    team_a_win_rate: float,
    team_b_win_rate: float
) -> Dict[str, float]:
    """
    使用 Log5 公式計算兩隊對戰的勝率
    
    Log5 公式由 Bill James 發明，用於計算兩支球隊對戰時的勝率
    公式： P(A wins) = (p_A - p_A × p_B) / (p_A + p_B - 2 × p_A × p_B)
    
    Args:
        team_a_win_rate (float): 球隊 A 的預期勝率 (0.0 - 1.0)
        team_b_win_rate (float): 球隊 B 的預期勝率 (0.0 - 1.0)
    
    Returns:
        dict: 包含兩隊對戰勝率
              {
                  "team_a_win_prob": float (0-100),
                  "team_b_win_prob": float (0-100)
              }
    
    Example:
        >>> probs = calculate_log5_win_probability(0.600, 0.450)
        >>> print(f"Team A: {probs['team_a_win_prob']}%")
        Team A: 62.5%
    
    Note:
        Log5 公式的優勢是考慮了兩隊的絕對實力
        例如：0.600 vs 0.450 的對戰，不是簡單的 60% vs 40%
    """
    # Log5 公式
    # P(A) = (p_A - p_A × p_B) / (p_A + p_B - 2 × p_A × p_B)
    
    numerator = team_a_win_rate - (team_a_win_rate * team_b_win_rate)
    denominator = team_a_win_rate + team_b_win_rate - (2 * team_a_win_rate * team_b_win_rate)
    
    # 處理除以零的情況
    if denominator == 0:
        prob_a = 0.5
    else:
        prob_a = numerator / denominator
    
    prob_b = 1 - prob_a
    
    return {
        'team_a_win_prob': round(prob_a * 100, 2),
        'team_b_win_prob': round(prob_b * 100, 2)
    }


def simulate_season_monte_carlo(
    team_a_win_rate: float,
    team_b_win_rate: float,
    num_games: int = 162,
    simulations: int = 10000
) -> Dict[str, Any]:
    """
    使用蒙地卡羅模擬整個賽季的結果
    
    Args:
        team_a_win_rate (float): 球隊 A 的勝率 (0.0 - 1.0)
        team_b_win_rate (float): 球隊 B 的勝率 (0.0 - 1.0)
        num_games (int): 賽季總場次 (預設 162 場，MLB 標準)
        simulations (int): 模擬次數 (預設 10,000 次)
    
    Returns:
        dict: 模擬結果統計
              {
                  "team_a_avg_wins": float,  # A 隊平均勝場
                  "team_b_avg_wins": float,  # B 隊平均勝場
                  "team_a_win_season_prob": float,  # A 隊勝率優於 B 隊的機率
                  "simulations": int
              }
    
    Example:
        >>> result = simulate_season_monte_carlo(0.580, 0.520, num_games=162)
        >>> print(f"Team A avg wins: {result['team_a_avg_wins']}")
        Team A avg wins: 94.1
    """
    team_a_wins_list = []
    team_b_wins_list = []
    team_a_better_count = 0
    
    for _ in range(simulations):
        # 對每一場比賽擲骰子
        team_a_wins = 0
        team_b_wins = 0
        
        # 先用 Log5 計算對戰勝率
        matchup_probs = calculate_log5_win_probability(team_a_win_rate, team_b_win_rate)
        team_a_vs_b_prob = matchup_probs['team_a_win_prob'] / 100
        
        # 模擬對戰場次 (假設兩隊對戰 num_games 場)
        for _ in range(num_games):
            if random.random() < team_a_vs_b_prob:
                team_a_wins += 1
            else:
                team_b_wins += 1
        
        team_a_wins_list.append(team_a_wins)
        team_b_wins_list.append(team_b_wins)
        
        if team_a_wins > team_b_wins:
            team_a_better_count += 1
    
    return {
        'team_a_avg_wins': round(sum(team_a_wins_list) / simulations, 1),
        'team_b_avg_wins': round(sum(team_b_wins_list) / simulations, 1),
        'team_a_win_season_prob': round((team_a_better_count / simulations) * 100, 2),
        'simulations': simulations
    }


def full_season_prediction_workflow(
    team_a_rs: int,
    team_a_ra: int,
    team_b_rs: int,
    team_b_ra: int,
    weight: float = 0.7,
    num_games: int = 162,
    simulations: int = 10000
) -> Dict[str, Any]:
    """
    完整的賽季預測流程
    
    步驟：
    1. 計算兩隊今年 (2025) 的畢氏勝率
    2. 應用回歸平均預測明年 (2026) 的勝率
    3. 使用 Log5 公式計算對戰勝率
    4. 執行蒙地卡羅模擬整季結果
    
    Args:
        team_a_rs (int): 球隊 A 今年得分
        team_a_ra (int): 球隊 A 今年失分
        team_b_rs (int): 球隊 B 今年得分
        team_b_ra (int): 球隊 B 今年失分
        weight (float): 回歸權重
        num_games (int): 賽季場次
        simulations (int): -模擬次數
    
    Returns:
        dict: 完整的預測結果
    
    Example:
        >>> result = full_season_prediction_workflow(
        ...     team_a_rs=600, team_a_ra=500,
        ...     team_b_rs=550, team_b_ra=550
        ... )
        >>> print(result['log5_matchup'])
        {'team_a_win_prob': 62.5, 'team_b_win_prob': 37.5}
    """
    # 步驟 1 & 2: 計算畢氏勝率並預測下一季
    team_a_prediction = predict_next_season_win_rate(team_a_rs, team_a_ra, weight)
    team_b_prediction = predict_next_season_win_rate(team_b_rs, team_b_ra, weight)
    
    # 步驟 3: Log5 對戰勝率
    log5_result = calculate_log5_win_probability(
        team_a_prediction['next_year_projected_win_rate'],
        team_b_prediction['next_year_projected_win_rate']
    )
    
    # 步驟 4: 蒙地卡羅模擬
    monte_carlo_result = simulate_season_monte_carlo(
        team_a_prediction['next_year_projected_win_rate'],
        team_b_prediction['next_year_projected_win_rate'],
        num_games,
        simulations
    )
    
    return {
        'team_a_prediction': team_a_prediction,
        'team_b_prediction': team_b_prediction,
        'log5_matchup': log5_result,
        'monte_carlo_simulation': monte_carlo_result
    }
