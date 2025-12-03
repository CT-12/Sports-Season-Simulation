"""
API Views for MLB Season Simulator
Provides endpoints for matchup analysis, team rankings prediction, and team ranking
"""

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .services.matchup import analyze_matchup
from .services.rankings import predict_2026_rankings
from .services.team_ranking import rank_teams_by_metrics, get_ranking_with_details


@api_view(['POST'])
def matchup_analysis(request):
    """
    POST /api/matchup/
    Analyze matchup using specified rating method
    
    Request body:
    {
        "team_A": "Los Angeles Dodgers",
        "team_B": "New York Yankees",
        "method": "Pythagorean"  // or "Elo"
    }
    
    Methods:
    - Pythagorean (default): 2025 data → regression → 2026 prediction + Log5 + Monte Carlo
    - Elo: Latest Elo ratings → Standard Elo win probability
    
    Response format (same for both methods):
    {
        "team_A": [{"id": int, "name": str, "position": str, "Rating": {...}}, ...],
        "team_B": [...],
        "team_A_score": float,
        "team_B_score": float,
        "team_A_win_prob": float,
        "team_B_win_prob": float
    }
    """
    # Validate request data
    team_a = request.data.get('team_A')
    team_b = request.data.get('team_B')
    method = request.data.get('method', 'Pythagorean')  # Default to Pythagorean
    
    if not team_a or not team_b:
        return Response(
            {'error': 'Both team_A and team_B are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validate method
    if method not in ['Pythagorean', 'Elo']:
        return Response(
            {'error': 'method must be either "Pythagorean" or "Elo"'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Analyze matchup with specified method
    result = analyze_matchup(team_a, team_b, method=method)
    
    if not result:
        error_msg = (
            f'Failed to analyze matchup using {method} method. '
            'Please check team names and ensure required data exists.'
        )
        if method == 'Elo':
            error_msg += ' (Elo ratings must be calculated first using: python manage.py calculate_elo)'
        
        return Response(
            {'error': error_msg},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Debug: Check result before returning
    print(f"[DEBUG] Result keys: {result.keys()}")
    print(f"[DEBUG] Team A count: {len(result.get('team_A', []))}")
    print(f"[DEBUG] Team B count: {len(result.get('team_B', []))}")
    
    return Response(result, status=status.HTTP_200_OK)


@api_view(['POST'])
def rankings_prediction(request):
    """
    POST /api/team_ranking/
    Predict 2026 team rankings by league
    
    Request body:
    {
        "method": "Pythagorean"  // or "Elo"
    }
    
    Response format:
    {
        "NL": ["Los Angeles Dodgers", "Atlanta Braves", ...],
        "AL": ["New York Yankees", "Houston Astros", ...]
    }
    
    Teams are sorted by predicted 2026 strength (best to worst).
    """
    method = request.data.get('method', 'Pythagorean')
    
    # Validate method
    if method not in ['Pythagorean', 'Elo']:
        return Response(
            {'error': 'method must be either "Pythagorean" or "Elo"'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        rankings = predict_2026_rankings(method=method)
        
        if not rankings['NL'] and not rankings['AL']:
            error_msg = f'Failed to calculate rankings using {method} method. Please ensure required data exists.'
            if method == 'Elo':
                error_msg += ' (Elo ratings must be calculated first using: python manage.py calculate_elo)'
            
            return Response(
                {'error': error_msg},
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response(rankings, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response(
            {'error': f'Failed to calculate rankings: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
def team_ranking(request):
    """
    POST /api/ranking/
    Rank all MLB teams by a combination of hitter and pitcher metrics.
    
    Request body:
    {
        "hitter_metric": "ops",  // or "avg", "hr", "rbi", etc.
        "pitcher_metric": "era", // or "whip", "so", "w", "l", etc.
        "season": 2025           // optional, defaults to latest season
        "details": false         // optional, set to true for detailed response
    }
    
    Response format (basic):
    {
        "AL": [
            ["New York Yankees", 2.145],
            ["Houston Astros", 1.892],
            ...
        ],
        "NL": [
            ["Los Angeles Dodgers", 2.567],
            ...
        ]
    }
    
    Response format (with details=true):
    {
        "season": 2025,
        "hitter_metric": "ops",
        "pitcher_metric": "era",
        "AL": [
            {
                "rank": 1,
                "team_name": "New York Yankees",
                "score": 2.145,
                "hitter_value": 0.820,
                "pitcher_value": 3.45,
                "hitter_z_score": 1.234,
                "pitcher_z_score": 0.911
            },
            ...
        ],
        "NL": [...]
    }
    """
    # Validate request data
    hitter_metric = request.data.get('hitter_metric')
    pitcher_metric = request.data.get('pitcher_metric')
    season = request.data.get('season')
    details = request.data.get('details', False)  # Request detailed info
    
    if not hitter_metric or not pitcher_metric:
        return Response(
            {
                'error': 'Both hitter_metric and pitcher_metric are required',
                'available_metrics': {
                    'hitting': ['avg', 'ops', 'hr', 'rbi', 'r', 'h', 'obp', 'slg'],
                    'pitching': ['era', 'whip', 'so', 'w', 'l', 'bb']
                }
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Get ranking
        if details:
            result = get_ranking_with_details(hitter_metric, pitcher_metric, season)
        else:
            result = rank_teams_by_metrics(hitter_metric, pitcher_metric, season)
        
        return Response(result, status=status.HTTP_200_OK)
    
    except ValueError as e:
        return Response(
            {
                'error': str(e),
                'available_metrics': {
                    'hitting': ['avg', 'ops', 'hr', 'rbi', 'r', 'h', 'obp', 'slg'],
                    'pitching': ['era', 'whip', 'so', 'w', 'l', 'bb']
                }
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    except Exception as e:
        return Response(
            {'error': f'Failed to rank teams: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
