#!/usr/bin/env python
"""
Test script for the Team Ranking API endpoint

This script demonstrates how to use the team ranking functionality
and validates the implementation.

Usage:
    python manage.py shell < test_ranking.py
    # or from within Django shell:
    exec(open('api/tests/test_ranking.py').read())
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sports_simulator.settings')
django.setup()

from api.services.team_ranking import (
    rank_teams_by_metrics,
    get_ranking_with_details,
    get_latest_season,
    aggregate_team_hitting_stats,
    aggregate_team_pitching_stats,
    calculate_z_score,
    normalize_z_score_by_direction,
    METRIC_DIRECTION,
    TEAM_LEAGUE_MAP,
)


def print_section(title):
    """Print a formatted section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def test_latest_season():
    """Test getting the latest season"""
    print_section("Test 1: Get Latest Season")
    try:
        season = get_latest_season()
        print(f"✓ Latest season: {season}")
        return season
    except Exception as e:
        print(f"✗ Error: {e}")
        return 2025


def test_team_league_mapping():
    """Test team to league mapping"""
    print_section("Test 2: Team League Mapping")
    print(f"Total teams mapped: {len(TEAM_LEAGUE_MAP)}")
    
    al_teams = [t for t, l in TEAM_LEAGUE_MAP.items() if l == "AL"]
    nl_teams = [t for t, l in TEAM_LEAGUE_MAP.items() if l == "NL"]
    
    print(f"AL Teams: {len(al_teams)}")
    for team in sorted(al_teams)[:3]:
        print(f"  - {team}")
    print("  ...")
    
    print(f"NL Teams: {len(nl_teams)}")
    for team in sorted(nl_teams)[:3]:
        print(f"  - {team}")
    print("  ...")


def test_aggregate_stats(season):
    """Test aggregating team stats"""
    print_section("Test 3: Aggregate Team Statistics")
    
    try:
        # Test hitting stats
        print("Fetching OPS (On-base Plus Slugging)...")
        ops_stats = aggregate_team_hitting_stats("ops", season)
        print(f"✓ Found OPS stats for {len(ops_stats)} teams")
        
        if ops_stats:
            # Show top 3 teams
            top_teams = sorted(ops_stats.items(), key=lambda x: x[1], reverse=True)[:3]
            print("  Top OPS teams:")
            for team, ops in top_teams:
                print(f"    - {team}: {ops:.4f}")
        
        # Test pitching stats
        print("\nFetching ERA (Earned Run Average)...")
        era_stats = aggregate_team_pitching_stats("era", season)
        print(f"✓ Found ERA stats for {len(era_stats)} teams")
        
        if era_stats:
            # Show best 3 teams (lowest ERA)
            best_teams = sorted(era_stats.items(), key=lambda x: x[1])[:3]
            print("  Best ERA teams (lowest):")
            for team, era in best_teams:
                print(f"    - {team}: {era:.4f}")
        
        return ops_stats, era_stats
    
    except Exception as e:
        print(f"✗ Error: {e}")
        return {}, {}


def test_z_score_calculation():
    """Test Z-score normalization"""
    print_section("Test 4: Z-Score Calculation")
    
    # Example: test with hypothetical values
    # League: avg OPS 0.750, std_dev 0.030
    
    values = [0.750, 0.780, 0.720, 0.800, 0.740]
    mean = sum(values) / len(values)
    variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
    std_dev = variance ** 0.5
    
    print(f"Test values: {values}")
    print(f"Mean: {mean:.4f}, Std Dev: {std_dev:.4f}")
    
    print("\nZ-Scores:")
    for value in values:
        z = calculate_z_score(value, mean, std_dev)
        print(f"  Value {value:.3f} → Z-Score: {z:.3f}")
    
    # Test direction normalization
    print("\nDirection Normalization:")
    print("  Metric 'ops' (higher is better):")
    z_score = 1.5
    normalized = normalize_z_score_by_direction(z_score, "ops")
    print(f"    Z={z_score} → {normalized} (unchanged)")
    
    print("  Metric 'era' (lower is better):")
    z_score = -1.5
    normalized = normalize_z_score_by_direction(z_score, "era")
    print(f"    Z={z_score} → {normalized} (flipped)")


def test_basic_ranking(season):
    """Test basic team ranking"""
    print_section("Test 5: Basic Team Ranking (OPS vs ERA)")
    
    try:
        result = rank_teams_by_metrics("ops", "era", season)
        
        print(f"✓ Ranking completed successfully\n")
        
        # Show AL results
        print("American League (AL):")
        for i, (team, score) in enumerate(result["AL"][:5], 1):
            print(f"  {i}. {team:<30} Score: {score:>7.3f}")
        if len(result["AL"]) > 5:
            print(f"  ... ({len(result['AL']) - 5} more teams)")
        
        # Show NL results
        print("\nNational League (NL):")
        for i, (team, score) in enumerate(result["NL"][:5], 1):
            print(f"  {i}. {team:<30} Score: {score:>7.3f}")
        if len(result["NL"]) > 5:
            print(f"  ... ({len(result['NL']) - 5} more teams)")
        
        return result
    
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_detailed_ranking(season):
    """Test ranking with detailed information"""
    print_section("Test 6: Detailed Ranking with Z-Scores")
    
    try:
        result = get_ranking_with_details("ops", "era", season)
        
        print(f"✓ Detailed ranking completed\n")
        print(f"Season: {result['season']}")
        print(f"Hitter Metric: {result['hitter_metric']}")
        print(f"Pitcher Metric: {result['pitcher_metric']}\n")
        
        # Show AL results
        print("American League (AL) - Top 3:")
        for team in result["AL"][:3]:
            print(f"\n  Rank {team['rank']}: {team['team_name']}")
            print(f"    Score: {team['score']:.3f}")
            print(f"    OPS: {team['hitter_value']:.4f} (Z={team['hitter_z_score']:+.3f})")
            print(f"    ERA: {team['pitcher_value']:.4f} (Z={team['pitcher_z_score']:+.3f})")
        
        return result
    
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_alternative_metrics(season):
    """Test with different metric combinations"""
    print_section("Test 7: Alternative Metric Combinations")
    
    test_cases = [
        ("avg", "whip"),    # Batting Average vs WHIP
        ("hr", "so"),       # Home Runs vs Strikeouts
        ("rbi", "w"),       # RBIs vs Wins
    ]
    
    for hitter_metric, pitcher_metric in test_cases:
        try:
            print(f"\nRanking by {hitter_metric.upper()} vs {pitcher_metric.upper()}...")
            result = rank_teams_by_metrics(hitter_metric, pitcher_metric, season)
            
            # Show top team from each league
            al_top = result["AL"][0] if result["AL"] else None
            nl_top = result["NL"][0] if result["NL"] else None
            
            if al_top:
                print(f"  AL Leader: {al_top[0]:<30} ({al_top[1]:>7.3f})")
            if nl_top:
                print(f"  NL Leader: {nl_top[0]:<30} ({nl_top[1]:>7.3f})")
        
        except Exception as e:
            print(f"  ✗ Error: {e}")


def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("  MLB TEAM RANKING SERVICE - TEST SUITE")
    print("=" * 70)
    
    # Test 1: Get latest season
    season = test_latest_season()
    
    # Test 2: Check league mapping
    test_team_league_mapping()
    
    # Test 3: Aggregate stats
    ops_stats, era_stats = test_aggregate_stats(season)
    
    # Test 4: Z-score calculation
    test_z_score_calculation()
    
    # Test 5: Basic ranking
    test_basic_ranking(season)
    
    # Test 6: Detailed ranking
    test_detailed_ranking(season)
    
    # Test 7: Alternative metrics
    test_alternative_metrics(season)
    
    print("\n" + "=" * 70)
    print("  ALL TESTS COMPLETED")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
